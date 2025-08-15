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
    workers = [consumer.start_processing(n) for n in range(1, settings.NUM_WORKERS + 1)]
    asyncio.gather(*workers, health_check_service.check_services())
    yield
    await db.close()


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    title="Payment Processor API",
    description="API for processing payments in the Rinha de Backend",
    lifespan=start_db,
)

app.include_router(app_router)


@app.get("/")
async def root():
    return {"message": "Benvindo a Api do Rinha de Backend 2025 - Payment Processor by Juan Lima"}


# if __name__ == "__main__":
#     config = uvicorn.Config(
#         app,
#         host="0.0.0.0",
#         port=8000,
#         workers=2,
#         access_log=False,
#         server_header=False,
#         date_header=False,
#     )

#     server = uvicorn.Server(config)

#     server.run()
