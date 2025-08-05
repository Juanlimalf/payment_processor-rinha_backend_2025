from datetime import datetime
from decimal import Decimal
from typing import Any, Dict

import httpx

from config import settings
from config.postgresDB import AsyncPostgresDB

PAYMENT_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments"
PAYMENT_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments"


http_client = httpx.AsyncClient(
    limits=httpx.Limits(max_connections=200, max_keepalive_connections=40),
    timeout=httpx.Timeout(10.0, connect=10.0, read=10.0, write=10.0),
)


class WorkerService:
    __slots__ = ("connection",)

    def __init__(self, connection: AsyncPostgresDB) -> None:
        self.connection = connection

    async def payment_process(self, data: Any) -> Dict[str, Any]:
        try:
            payment_id = data["id"]
            amount = data["amount"]
            correlation_id = data["correlation_id"]
            requested_at = data["requested_at"]

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

            return {"status": "success", "message": "Pagamento processado com sucesso"}

        except Exception as e:
            print(f"Reprocessar o pagamento devido ao erro: {e}")
            raise

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

            response = await http_client.post(url, json=body, headers=headers)

            if response.status_code != 200:
                if response.status_code != 422:
                    print(f"Pagamento processado com sucesso com o processador {processorType} - Status: {response.status_code} - Mensagem: {response.text}")
                    return False

            await self.update_status(payment_id=paymentId, process_type=processorType)
            return True

        except Exception as exc:
            print(f"Erro ao processar o pagamento com o processador {processorType}: {exc}")
            return False

    async def update_status(self, payment_id: int, process_type: int):
        async with self.connection.connection() as conn:
            async with conn.transaction():
                await conn.execute(
                    """update
                            payments
                        set
                            was_processed = true,
                            process_type = $1
                        where
                            id = $2;""",
                    process_type,
                    payment_id,
                )
        print(f"Pagamento processado com sucesso - {payment_id}")
