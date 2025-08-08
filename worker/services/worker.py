import asyncio

import httpx
from redis import Redis

from services.tasks import WorkerService


async def worker():
    http_client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=350, max_keepalive_connections=50),
        timeout=httpx.Timeout(10.0, connect=10.0, read=10.0, write=10.0),
    )

    redis_client = Redis(host="redis", port=6379, db=0)
    worker_service = WorkerService(http_client=http_client, redis_client=redis_client)

    while True:
        try:
            await asyncio.create_task(worker_service.start_process())
        except Exception as e:
            print(e)
