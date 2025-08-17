# Arquivo healf_check gerado automaticamente.


import asyncio

from config import logger, settings
from services.http_client import HttpClient
from services.redis_client import RedisClient

HEALTH_CHECK_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments/service-health"
HEALTH_CHECK_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments/service-health"


class HealthCheckService:
    def __init__(self):
        self.http_client = HttpClient().get_client()
        self.redis_client = RedisClient().get_client()

    async def check_services(self) -> None:
        while True:
            logger.info("Verificando serviços de pagamento...")
            tasks = [self.health_check(HEALTH_CHECK_DEFAULT), self.health_check(HEALTH_CHECK_FALLBACK)]

            status_default, status_fallback = await asyncio.gather(*tasks)

            self.redis_client.set("payment_processor_default_status", int(status_default))
            self.redis_client.set("payment_processor_fallback_status", int(status_fallback))

            await asyncio.sleep(5)

    async def health_check(self, url: str) -> bool:
        try:
            response = await self.http_client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao verificar saúde do serviço {url}: {e}")
            return False
