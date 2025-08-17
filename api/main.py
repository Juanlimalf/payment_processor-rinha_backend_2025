import asyncio
from concurrent.futures import ThreadPoolExecutor

import uvicorn
from fastapi import FastAPI

from config import settings
from router.router import router as app_router
from services.health_check import HealthCheckService
from services.payments import WorkerConsumer
from services.queue import task_queue


def run_consumer(workerId, task_queue):
    print(f"Starting worker {workerId}")
    consumer = WorkerConsumer()
    asyncio.run(consumer.start_processing(workerId, task_queue))


def run_health_check():
    print("Starting health check service")
    health_check_service = HealthCheckService()
    asyncio.run(health_check_service.check_services())


app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.include_router(app_router)


@app.get("/healthcheck")
async def root():
    return {"message": "service is running"}


def run_server():
    print("Starting FastAPI server")
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        loop="uvloop",
        http="httptools",
        workers=1,
        access_log=False,
    )
    server = uvicorn.Server(config)
    asyncio.run(server.serve())


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=60) as exec:
        print("Starting services...")
        exec.submit(run_server)

        for i in range(1, settings.NUM_WORKERS + 1):
            exec.submit(run_consumer, i, task_queue)
        exec.submit(run_health_check)
