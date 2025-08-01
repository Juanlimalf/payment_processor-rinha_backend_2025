from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.config import PostgresDB
from api.schemas.schema import Payment, Summary
from api.services.payments import PaymentService
from api.services.tasks import payment_process

router = APIRouter()

# Cache de resposta para otimizar
PAYMENT_RESPONSE = {
    "message": "payment request received",
    "status": "processing",
}

connection = PostgresDB()
session = next(connection.get_session())


def get_service():
    return PaymentService(session)


@router.post("/payments")
async def router_app(payload: Payment):
    payment_process.delay(payload.model_dump())
    return PAYMENT_RESPONSE


@router.get("/payments-summary")
async def router_app_sumary(from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = Query(None, alias="to"), service: PaymentService = Depends(get_service)) -> Summary:
    return service.get_summary(from_, to)


@router.post("/payments-purge")
async def router_app_purge(service: PaymentService = Depends(get_service)) -> None:
    service.purge_database()
