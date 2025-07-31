from typing import Any, Optional

from fastapi import APIRouter, Query

from api.worker.summary import get_summary, purge_summary
from api.worker.tasks import payment_process

router = APIRouter()

# Cache de resposta para otimizar
PAYMENT_RESPONSE = {
    "message": "payment request received",
    "status": "processing",
}


@router.post("/payments")
async def router_app(
    payload: dict[str, Any],
):
    payment_process.delay(payload)
    return PAYMENT_RESPONSE


@router.get("/payments-summary")
async def router_app_sumary(from_: Optional[str] = Query(None, alias="from"), to: Optional[str] = Query(None, alias="to")):
    print(from_, to)
    return get_summary(from_, to)


@router.post("/payments-purge")
async def router_app_purge():
    return purge_summary()
