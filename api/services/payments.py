import asyncio
import json
from datetime import datetime, timezone
from typing import Optional

from config import logger, settings
from schemas.schema import Payment, PaymentsTotals, Summary
from services.http_client import http_client
from services.redis_client import redis_client

PAYMENT_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments"
PAYMENT_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments"

queue_payments = asyncio.Queue(maxsize=60_000)


def iso_to_timestamp(iso_str: str) -> int:
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))

    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    else:
        dt = dt.astimezone(timezone.utc)

    return int(dt.timestamp() * 1000)


class PaymentService:
    async def insert_payment(self, data: Payment):
        queue_payments.put_nowait(data)

    async def get_summary(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Summary:
        if from_date and to_date:
            from_ts = iso_to_timestamp(from_date)
            to_ts = iso_to_timestamp(to_date)

            payments_default = redis_client.zrangebyscore("payment_processed_default", from_ts, to_ts)
            payments_fallback = redis_client.zrangebyscore("payment_processed_fallback", from_ts, to_ts)
        else:
            payments_default = redis_client.zrange("payment_processed_default", 0, -1)
            payments_fallback = redis_client.zrange("payment_processed_fallback", 0, -1)

        return Summary(
            default=PaymentsTotals(
                totalRequests=len(payments_default),
                totalAmount=round(sum(json.loads(item.decode())["amount"] for item in payments_default), 2),
            ),
            fallback=PaymentsTotals(
                totalRequests=len(payments_fallback),
                totalAmount=round(sum(json.loads(item.decode())["amount"] for item in payments_fallback), 2),
            ),
        )

    async def purge_database(self) -> None:
        redis_client.flushdb()


class WorkerConsumer:
    def __init__(self) -> None:
        self._status_default = True
        self._status_fallback = True

    async def start_processing(self, worker_id: int):
        logger.info(f"Iniciando worker de processamento de pagamentos - Worker ID: {worker_id}")

        while True:
            try:
                data: Payment = await queue_payments.get()

                await self.process_payment(data)

                queue_payments.task_done()

            except Exception as e:
                print(e)
                await queue_payments.put(data)

    async def process_payment(self, data: Payment) -> None:
        amount = data.amount
        correlation_id = data.correlationId
        requested_at = datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        logger.info(f"Iniciando processamento do pagamento - CorrelationId: {correlation_id} - Amount: {amount}")

        payment_processor_default_status = redis_client.get("payment_processor_default_status")
        payment_processor_fallback_status = redis_client.get("payment_processor_fallback_status")

        response = None

        if payment_processor_default_status:
            response = await self.send_payment(
                url=PAYMENT_DEFAULT,
                processorType="default",
                requestedAt=requested_at,
                payment=data,
            )

        elif not response and payment_processor_fallback_status:
            response = await self.send_payment(
                url=PAYMENT_FALLBACK,
                processorType="fallback",
                requestedAt=requested_at,
                payment=data,
            )
        else:
            logger.error("Nenhum serviço de pagamento disponível para processar o pagamento.")
            raise Exception("Nenhum serviço de pagamento disponível")

    async def send_payment(self, url: str, processorType: str, requestedAt: datetime, payment: Payment) -> bool:
        try:
            body = {
                "correlationId": payment.correlationId,
                "amount": float(payment.amount),
                "requestedAt": requestedAt,
            }

            response = await http_client.post(url, json=body)

            if response.status_code >= 500:
                return False

            if response.status_code == 422:
                logger.error(f"Erro ao processar o pagamento com o processador {processorType} - Status: {response.status_code}")

                return True

            await self.update_status_payment(body, processorType, iso_to_timestamp(requestedAt))
            return True

        except Exception as exc:
            logger.error(f"Erro ao processar o pagamento com o processador {processorType}: {exc}")
            return False

    async def update_status_payment(self, body, process_type, timestamp):
        redis_client.zadd(f"payment_processed_{process_type}", {json.dumps(body): timestamp})

        logger.info(f"Pagamento processado com sucesso - {body} - payment_processed_{process_type}")
