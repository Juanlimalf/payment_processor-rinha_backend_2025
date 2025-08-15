# Arquivo healf_check gerado automaticamente.


import asyncio
import logging

from annotated_types import T

from config import settings
from infra.http_client import HttpClient
from infra.postgres_client import AsyncPostgresDB
from infra.redis_client import RedisClient

logger = logging.getLogger("health_check")
logger.setLevel(level=settings.LOG_LEVEL)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


HEALTH_CHECK_DEFAULT = f"{settings.PAYMENT_PROCESSOR_DEFAULT}/payments/service-health"
HEALTH_CHECK_FALLBACK = f"{settings.PAYMENT_PROCESSOR_FALLBACK}/payments/service-health"


class HealthCheckService:
    def __init__(self) -> None:
        self.http_client = HttpClient().get_client()
        self.db = AsyncPostgresDB()

    async def init_data_status(self) -> None:
        try:
            async with self.db.connection() as conn:
                await conn.execute(
                    """INSERT INTO 
                            services (id, service_default, service_fallback)
                        VALUES
                            ($1, $2, $3)
                        ON CONFLICT (id) DO NOTHING""",
                    1,
                    True,
                    True,
                )
        except Exception as e:
            logger.error(f"{e}")

    async def check_services(self) -> None:
        while True:
            try:
                logger.info("Verificando serviços de pagamento...")
                tasks = [self.health_check(HEALTH_CHECK_DEFAULT), self.health_check(HEALTH_CHECK_FALLBACK)]

                status_default, status_fallback = await asyncio.gather(*tasks)

                await self.add_status_to_db(status_default, status_fallback)

                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Erro ao verificar serviços de pagamento: {e}")

    async def health_check(self, url: str) -> bool:
        try:
            response = await self.http_client.get(url)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Erro ao verificar saúde do serviço {url}: {e}")
            return False

    async def add_status_to_db(self, status_default: bool, status_fallback: bool) -> None:
        async with self.db.connection() as conn:
            await conn.execute(
                """update services set service_default = $1, service_fallback = $2 where id = 1""",
                status_default,
                status_fallback,
            )
