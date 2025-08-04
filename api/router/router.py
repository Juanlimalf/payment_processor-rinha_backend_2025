import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Query
from redis import Redis
from rq import Queue, Retry

from config import AsyncPostgresDB, settings
from schemas.schema import Payment, Summary
from services.payments import PaymentService

router = APIRouter()

# Cache de resposta para otimizar
PAYMENT_RESPONSE = {
    "message": "payment request received",
    "status": "processing",
}

connection = AsyncPostgresDB()
redis_conn = Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)
q = Queue("worker", connection=redis_conn)


async def get_service():
    async with connection.connection() as session:
        yield PaymentService(session)


@router.post("/payments")
async def router_app(payload: Payment):
    asyncio.create_task(
        asyncio.to_thread(
            q.enqueue,
            "services.worker.task",
            payload.model_dump(),
            retry=Retry(max=3, interval=1),
        )
    )

    return PAYMENT_RESPONSE


@router.get("/payments-summary", status_code=200)
async def router_app_sumary(from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = Query(None, alias="to"), service: PaymentService = Depends(get_service)) -> Summary:
    return await service.get_summary(from_, to)


@router.post("/payments-purge", status_code=204)
async def router_app_purge(service: PaymentService = Depends(get_service)) -> None:
    await service.purge_database()
