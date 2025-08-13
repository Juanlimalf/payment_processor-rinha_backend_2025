import asyncio

import uvicorn
from fastapi import FastAPI

from config import settings
from router.router import router as app_router
from services.payments import PublishService

app = FastAPI(
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
    title="Payment Processor API",
    description="API for processing payments in the Rinha de Backend",
)

app.include_router(app_router)


@app.get("/heatcheck")
async def root():
    return {"message": "service is running"}


async def run():
    publish_service = PublishService()

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

    workers = [publish_service.start_processing(n) for n in range(1, settings.NUM_WORKERS + 1)]

    await asyncio.gather(asyncio.create_task(server.serve()), *workers)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(run())
