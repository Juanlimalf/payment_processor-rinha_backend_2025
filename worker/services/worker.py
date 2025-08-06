import asyncio

import httpx

from config.postgresDB import AsyncPostgresDB
from services.tasks import WorkerService


async def worker():
    connection = AsyncPostgresDB()
    http_client = httpx.AsyncClient(
        limits=httpx.Limits(max_connections=350, max_keepalive_connections=50),
        timeout=httpx.Timeout(2.0, connect=2.0, read=2.0, write=2.0),
    )
    worker_service = WorkerService(connection=connection, http_client=http_client)
    while True:
        try:
            await asyncio.create_task(worker_service.start_process())
        except Exception as e:
            print(e)

        await asyncio.sleep(0.2)
