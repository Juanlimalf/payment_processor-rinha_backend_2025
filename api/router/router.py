import asyncio
from typing import Optional

from fastapi import APIRouter, Depends, Query, status

from schemas.schema import Payment, Summary
from services.payments import PaymentService

router = APIRouter()


async def get_service():
    yield PaymentService()


@router.post("/payments", status_code=status.HTTP_202_ACCEPTED)
async def router_app(payload: Payment, service: PaymentService = Depends(get_service)):
    asyncio.create_task(service.insert_payment(payload))


@router.get("/payments-summary", status_code=status.HTTP_200_OK)
async def router_app_sumary(from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = Query(None, alias="to"), service: PaymentService = Depends(get_service)) -> Summary:
    return await service.get_summary(from_, to)


@router.post("/payments-purge", status_code=status.HTTP_204_NO_CONTENT)
async def router_app_purge(service: PaymentService = Depends(get_service)) -> None:
    await service.purge_database()
