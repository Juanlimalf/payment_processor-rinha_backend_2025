import asyncio
import logging
from datetime import datetime, timezone

from config.settings import settings
from infra.http_client import HttpClient
from infra.postgres_client import AsyncPostgresDB
from infra.redis_client import RedisClient
from schemas.schema import Payment
from services.queue import queue_payments

logger = logging.getLogger("consumer")
logger.setLevel(level=settings.LOG_LEVEL)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


PAYMENT_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments"
PAYMENT_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments"


class WorkerConsumer:
    def __init__(self) -> None:
        self._status_default = True
        self._status_fallback = True
        self.redis_client = RedisClient().get_client()
        self.http_client = HttpClient().get_client()
        self.db = AsyncPostgresDB()
        self._semaphore = asyncio.Semaphore(90)

    async def start_processing(self):
        while True:
            try:
                data: Payment = await queue_payments.get()

                async with self._semaphore:
                    await self.process_payment(data)

                queue_payments.task_done()

            except Exception as e:
                print(e)
                await queue_payments.put(data)

    async def process_payment(self, data: Payment) -> None:
        # await self.get_payment_status()
        amount = data.amount
        correlation_id = data.correlationId
        requested_at = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")

        logger.info(f"Iniciando processamento do pagamento - CorrelationId: {correlation_id} - Amount: {amount}")

        response = None

        if self._status_default:
            response = await self.send_payment(
                url=PAYMENT_DEFAULT,
                processorType="default",
                requestedAt=requested_at,
                payment=data,
            )

        if not response and self._status_fallback:
            response = await self.send_payment(
                url=PAYMENT_FALLBACK,
                processorType="fallback",
                requestedAt=requested_at,
                payment=data,
            )
        else:
            logger.error("Nenhum serviço de pagamento disponível para processar o pagamento.")
            raise Exception("Nenhum serviço de pagamento disponível")

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

            await self.update_status_payment(correlationId=payment.correlationId, amount=payment.amount, process_type=processorType, requestedAt=requestedAt)
            return True

        except Exception as exc:
            logger.error(f"Erro ao processar o pagamento com o processador {processorType}: {exc}")
            return False

    async def update_status_payment(self, correlationId: str, amount: float, process_type: str, requestedAt: str):
        async with self.db.connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    f"""insert into payments (correlation_id, amount, process_type, requested_at)
                       values ($1, $2, $3, '{str(requestedAt.replace("Z", "+00:00").replace("T", " "))}')""",
                    correlationId,
                    amount,
                    process_type,
                )

    async def get_payment_status(self):
        async with self.db.connection() as conn:
            result = await conn.fetchrow(
                """select service_default, service_fallback from services""",
            )
            self._status_default = result["service_default"] if result else None
            self._status_fallback = result["service_fallback"] if result else None
