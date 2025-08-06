import asyncio
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict

import httpx

from config import settings
from config.postgresDB import AsyncPostgresDB

logger = logging.getLogger("worker")

logger.setLevel(level=logging.ERROR)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


PAYMENT_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments"
PAYMENT_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments"


class WorkerService:
    __slots__ = ("connection", "http_client")

    def __init__(self, connection: AsyncPostgresDB, http_client: httpx.AsyncClient) -> None:
        self.connection = connection
        self.http_client = http_client

    async def start_process(self):
        async with self.connection.connection() as conn:
            payments = await conn.fetch(
                """SELECT
                        p.id,
                        p.correlation_id,
                        p.amount
                    FROM
                        payments p
                    WHERE
                        p.was_processed = false
                    FOR UPDATE SKIP LOCKED
                    LIMIT 300;"""
            )

        if not payments:
            return

        tasks = [self.payment_process(payment) for payment in payments]
        await asyncio.gather(*tasks)

    async def payment_process(self, data: Any) -> Dict[str, Any]:
        try:
            payment_id = data["id"]
            amount = data["amount"]
            correlation_id = data["correlation_id"]
            requested_at = datetime.now(tz=timezone.utc)

            response_default = await self.task_process(
                url=PAYMENT_DEFAULT,
                paymentId=payment_id,
                processorType=1,
                amount=amount,
                correlationId=correlation_id,
                requestedAt=requested_at,
            )

            if not response_default:
                response_fallback = await self.task_process(
                    url=PAYMENT_FALLBACK,
                    paymentId=payment_id,
                    processorType=2,
                    amount=amount,
                    correlationId=correlation_id,
                    requestedAt=requested_at,
                )

                if not response_fallback:
                    raise Exception("Não foi possível processar o pagamento com nenhum dos processadores disponíveis")

        except Exception as e:
            logger.error(f"Erro ao processar o pagamento: {e}")

    async def task_process(self, url: str, paymentId: int, processorType: int, amount: Decimal, correlationId: str, requestedAt: datetime) -> bool:
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            body = {
                "correlationId": correlationId,
                "amount": float(amount),
                "requestedAt": requestedAt.isoformat(),
            }

            response = await self.http_client.post(url, json=body, headers=headers)

            if response.status_code != 200:
                if response.status_code != 422:
                    logger.error(f"Erro ao processar o pagamento com o processador {processorType} - Status: {response.status_code} - Mensagem: {response.text}")
                    return False

            await self.update_status(payment_id=paymentId, process_type=processorType, requestedAt=requestedAt)
            return True

        except Exception as exc:
            logger.error(f"Erro ao processar o pagamento com o processador {processorType}: {exc}")
            return False

    async def update_status(self, payment_id: int, process_type: int, requestedAt: datetime):
        async with self.connection.connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    f"""update
                            payments
                        set
                            was_processed = true,
                            process_type = $1,
                            requested_at = '{str(requestedAt)}'
                        where
                            id = $2;""",
                    process_type,
                    payment_id,
                )
        logger.info(f"Pagamento processado com sucesso - {payment_id}")
