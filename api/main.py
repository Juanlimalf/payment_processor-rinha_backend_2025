import asyncio
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI

from config import settings
from router.router import router as app_router
from services.health_check import HealthCheckService
from services.payments import WorkerConsumer

consumer = WorkerConsumer()
health_check_service = HealthCheckService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    workers = [consumer.start_processing(n) for n in range(1, settings.NUM_WORKERS + 1)]
    asyncio.gather(*workers, health_check_service.check_services())
    yield


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    lifespan=lifespan,
)

app.include_router(app_router)


@app.get("/heatcheck")
async def root():
    return {"message": "service is running"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        loop="uvloop",
        http="httptools",
        workers=1,
        access_log=False,
    )
