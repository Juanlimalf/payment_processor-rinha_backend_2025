import json
from datetime import datetime, timezone
from queue import Queue
from typing import Optional

from config import logger, settings
from schemas.schema import Payment, PaymentsTotals, Summary
from services.http_client import HttpClient
from services.queue import task_queue
from services.redis_client import RedisClient

PAYMENT_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments"
PAYMENT_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments"


def iso_to_timestamp(iso_str: str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.timestamp()


class PaymentService:
    def __init__(self):
        self.redis_client = RedisClient().get_client()

    async def insert_payment(self, data: Payment):
        task_queue.put_nowait(data)

    async def get_summary(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Summary:
        if from_date and to_date:
            from_ts = iso_to_timestamp(from_date)
            to_ts = iso_to_timestamp(to_date)

            payments_default = self.redis_client.zrangebyscore(
                "payment_processed_default",
                from_ts,
                to_ts,
            )
            payments_fallback = self.redis_client.zrangebyscore(
                "payment_processed_fallback",
                from_ts,
                to_ts,
            )
        else:
            payments_default = self.redis_client.zrange(
                "payment_processed_default",
                0,
                -1,
            )
            payments_fallback = self.redis_client.zrange(
                "payment_processed_fallback",
                0,
                -1,
            )

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
        self.redis_client.flushdb()


class WorkerConsumer:
    def __init__(self) -> None:
        self._status_default = True
        self._status_fallback = True
        self.redis_client = RedisClient().get_client()
        self.http_client = HttpClient().get_client()

    async def start_processing(self, worker_id: int, task_queue: Queue):
        logger.info(f"Iniciando worker de processamento de pagamentos - Worker ID: {worker_id}")

        while True:
            try:
                data: Payment = task_queue.get()

                if data is not None:
                    await self.process_payment(data)

                task_queue.task_done()

            except Exception as e:
                print(e)

                task_queue.put_nowait(data)

    async def process_payment(self, data: Payment) -> None:
        amount = data.amount
        correlation_id = data.correlationId
        requested_at = datetime.now(tz=timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

        logger.info(f"Iniciando processamento do pagamento - CorrelationId: {correlation_id} - Amount: {amount}")

        payment_processor_default_status = self.redis_client.get("payment_processor_default_status")
        payment_processor_fallback_status = self.redis_client.get("payment_processor_fallback_status")
        # payment_processor_default_status = True
        # payment_processor_fallback_status = True

        result = None

        if payment_processor_default_status:
            result = await self.send_payment(
                url=PAYMENT_DEFAULT,
                processorType="default",
                requestedAt=requested_at,
                payment=data,
            )

        if not result and payment_processor_fallback_status:
            result = await self.send_payment(
                url=PAYMENT_FALLBACK,
                processorType="fallback",
                requestedAt=requested_at,
                payment=data,
            )

        if not result:
            logger.error("Nenhum serviço de pagamento disponível para processar o pagamento.")
            raise Exception("Nenhum serviço de pagamento disponível para processar o pagamento.")

    async def send_payment(self, url: str, processorType: str, requestedAt: str, payment: Payment) -> bool:
        try:
            body = {
                "correlationId": payment.correlationId,
                "amount": float(payment.amount),
                "requestedAt": requestedAt,
            }

            response = await self.http_client.post(url, json=body)

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
        self.redis_client.zadd(f"payment_processed_{process_type}", {json.dumps(body): timestamp})

        logger.info(f"Pagamento processado com sucesso - {body} - payment_processed_{process_type}")
