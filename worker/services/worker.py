import asyncio

from config.postgresDB import AsyncPostgresDB
from services.tasks import WorkerService


async def worker():
    connection = AsyncPostgresDB()
    worker_service = WorkerService(connection=connection)
    while True:
        # tasks_group = [asyncio.create_task(worker_service.get_payments_lote()) for _ in range(3)]

        # await asyncio.gather(*tasks_group)
        await asyncio.create_task(worker_service.get_payments_lote())

        await asyncio.sleep(0.2)
