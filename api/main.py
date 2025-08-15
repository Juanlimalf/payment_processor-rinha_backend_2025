import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from config import settings
from infra.postgres_client import AsyncPostgresDB
from router.router import router as app_router
from services.consumer import WorkerConsumer
from services.health_check import HealthCheckService

consumer = WorkerConsumer()
health_check_service = HealthCheckService()
db = AsyncPostgresDB()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_pool()
    await db.create_table()
    await health_check_service.init_data_status()
    asyncio.gather(
        *[consumer.start_processing() for _ in range(50)],
        # health_check_service.check_services(),
    )
    yield
    await db.close()


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    title="Payment Processor API",
    description="API for processing payments in the Rinha de Backend",
    lifespan=lifespan,
)

app.include_router(app_router)


@app.get("/")
async def root():
    return {"message": "Benvindo a Api do Rinha de Backend 2025 - Payment Processor by Juan Lima"}
