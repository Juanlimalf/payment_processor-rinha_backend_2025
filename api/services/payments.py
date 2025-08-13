import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import httpx
import redis

from config import settings
from schemas.schema import Payment, PaymentsTotals, Summary

PAYMENT_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments"
PAYMENT_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments"
HEALTH_CHECK_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments/service-health"
HEALTH_CHECK_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments/service-health"

queue_payments = asyncio.Queue(maxsize=60_000)
redis_client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=0)
http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=500, max_keepalive_connections=100),
    timeout=httpx.Timeout(10.0, connect=10.0, read=10.0, write=10.0),
    headers={"Content-Type": "application/json", "Accept": "application/json"},
)

logger = logging.getLogger("worker")
logger.setLevel(level=settings.LOG_LEVEL)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


class PaymentService:
    def _iso_to_timestamp(self, iso_str: str) -> int:
        dt = datetime.strptime(iso_str.split(".")[0], "%Y-%m-%dT%H:%M:%S")

        return int(time.mktime(dt.timetuple()))

    async def insert_payment(self, data: Payment):
        queue_payments.put_nowait(data)

    async def get_summary(self, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Summary:
        if from_date and to_date:
            from_ts = self._iso_to_timestamp(from_date)
            to_ts = self._iso_to_timestamp(to_date)

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


class PublishService:
    async def start_processing(self, n: int):
        logger.info(f"Iniciando o processamento de pagamentos...{n}")

        while True:
            try:
                data: Payment = await queue_payments.get()

                if data:
                    await self.process_payment(data)

            except Exception as e:
                print(e)
                await queue_payments.put(data)
            finally:
                queue_payments.task_done()

    async def process_payment(self, data: Payment) -> None:
        amount = data.amount
        correlation_id = data.correlationId
        requested_at = datetime.now(tz=timezone.utc) + timedelta(seconds=5)
        logger.info(f"Iniciando processamento do pagamento - CorrelationId: {correlation_id} - Amount: {amount}")

        response = None
        response = await self.send_payment(
            url=PAYMENT_DEFAULT,
            processorType="default",
            requestedAt=requested_at,
            payment=data,
        )

        if not response:
            response = await self.send_payment(
                url=PAYMENT_FALLBACK,
                processorType="fallback",
                requestedAt=requested_at,
                payment=data,
            )

            if not response:
                raise Exception("Serviços de pagamento indisponíveis")

    async def send_payment(self, url: str, processorType: str, requestedAt: datetime, payment: Payment) -> bool:
        try:
            body = {
                "correlationId": payment.correlationId,
                "amount": float(payment.amount),
                "requestedAt": requestedAt.isoformat().split(".")[0],
            }

            response = await http_client.post(url, json=body)

            if response.status_code >= 500:
                return False

            if response.status_code == 422:
                logger.error(f"Erro ao processar o pagamento com o processador {processorType} - Status: {response.status_code}")

                return True

            await self.update_status_payment(body, processorType, int(time.mktime(requestedAt.timetuple())))
            return True

        except Exception as exc:
            logger.error(f"Erro ao processar o pagamento com o processador {processorType}: {exc}")
            return False

    async def update_status_payment(self, body, process_type, timestamp):
        redis_client.zadd(f"payment_processed_{process_type}", {json.dumps(body): timestamp})

        logger.info(f"Pagamento processado com sucesso - {body} - payment_processed_{process_type}")
