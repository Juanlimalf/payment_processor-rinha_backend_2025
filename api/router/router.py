import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Query

from schemas.schema import Payment, Summary
from services.payments import PaymentService

router = APIRouter()

# Cache de resposta para otimizar
PAYMENT_RESPONSE = {
    "message": "payment request received",
    "status": "processing",
}


async def get_service():
    yield PaymentService()


@router.post("/payments")
async def router_app(payload: Payment, service: PaymentService = Depends(get_service)):
    asyncio.create_task(service.insert_payment(data=payload))

    return PAYMENT_RESPONSE


@router.get("/payments-summary", status_code=200)
async def router_app_sumary(from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = Query(None, alias="to"), service: PaymentService = Depends(get_service)) -> Summary:
    return await service.get_summary(from_, to)


@router.post("/payments-purge", status_code=204)
async def router_app_purge(service: PaymentService = Depends(get_service)) -> None:
    await service.purge_database()
