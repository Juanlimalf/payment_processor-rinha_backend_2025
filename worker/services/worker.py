import asyncio

from config.postgresDB import AsyncPostgresDB
from services.tasks import WorkerService


async def worker(connection: AsyncPostgresDB):
    worker_service = WorkerService(connection=connection)
    while True:
        async with connection.connection() as conn:
            async with conn.transaction():
                payments = await conn.fetch(
                    """select
                        p.id,
                        p.correlation_id,
                        p.amount,
                        p.requested_at
                    from
                        payments p
                    where
                        p.was_processed = false
                    limit 50;"""
                )

        if not payments:
            await asyncio.sleep(0.1)
            continue

        tasks = [worker_service.payment_process(payment) for payment in payments]

        await asyncio.gather(*tasks, return_exceptions=True)

        await asyncio.sleep(0.1)
