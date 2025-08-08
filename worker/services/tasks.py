import asyncio
import json
import logging
import time
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Union

import httpx
from redis import Redis
from tenacity import retry, stop_after_attempt, wait_fixed

from config import settings

logger = logging.getLogger("worker")

logger.setLevel(level=logging.INFO)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


PAYMENT_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments"
PAYMENT_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments"


class WorkerService:
    __slots__ = ("http_client", "redis_client")

    def __init__(self, http_client: httpx.AsyncClient, redis_client: Redis) -> None:
        self.http_client = http_client
        self.redis_client = redis_client

    async def start_process(self):
        payments = await self.get_payments()

        if not payments:
            return

        tasks = [self.payment_process(json.loads(payment)) for payment in payments]

        await asyncio.gather(*tasks)

    async def get_payments(self) -> Union[List[str], None]:
        try:
            return self.redis_client.lpop("payment_queue", 500)

        except Exception as e:
            logger.error(f"Erro ao obter os pagamentos: {e}")

    async def payment_process(self, data: Any) -> None:
        try:
            amount = data["amount"]
            correlation_id = data["correlationId"]
            requested_at = datetime.now(tz=timezone.utc)

            response_default = await self.task_process(
                url=PAYMENT_DEFAULT,
                processorType="default",
                amount=amount,
                correlationId=correlation_id,
                requestedAt=requested_at,
            )

            if not response_default:
                response_fallback = await self.task_process(
                    url=PAYMENT_FALLBACK,
                    processorType="fallback",
                    amount=amount,
                    correlationId=correlation_id,
                    requestedAt=requested_at,
                )

                if not response_fallback:
                    raise Exception("Não foi possível processar o pagamento com nenhum dos processadores disponíveis")

        except Exception as e:
            logger.error(f"Erro ao processar o pagamento: {e}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2))
    async def task_process(self, url: str, processorType: str, amount: Decimal, correlationId: str, requestedAt: datetime) -> bool:
        try:
            headers = {
                "Content-Type": "application/json",
                "Accept": "application/json",
            }

            body = {
                "correlationId": correlationId,
                "amount": float(amount),
                "requestedAt": requestedAt.isoformat().split(".")[0],
            }

            response = await self.http_client.post(url, json=body, headers=headers)

            if response.status_code != 200:
                logger.error(f"Erro ao processar o pagamento com o processador {processorType} - Status: {response.status_code} - Mensagem: {response.text}")
                return False

            await self.update_status(body, processorType, int(time.mktime(requestedAt.timetuple())))
            return True

        except Exception as exc:
            logger.error(f"Erro ao processar o pagamento com o processador {processorType}: {exc}")
            return False

    async def update_status(self, body, process_type, timestamp):
        self.redis_client.zadd(f"payment_processed_{process_type}", {json.dumps(body): timestamp})

        logger.info(f"Pagamento processado com sucesso - {body} - payment_processed_{process_type}")
