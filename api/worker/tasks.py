from datetime import datetime
from typing import Dict, Any
import httpx
import redis

from api.config import settings
from ..config import app_celery
from ..config.duck_db import insert_payment

REDIS_URL = settings.REDIS_URL
PAYMENT_DEFAULT = settings.PAYMENT_PROCESSOR_DEFAULT
PAYMENT_FALLBACK = settings.PAYMENT_PROCESSOR_FALLBACK

redis_client = redis.Redis.from_url(
    REDIS_URL,
    decode_responses=True,
    max_connections=50,
    retry_on_timeout=True,
    socket_keepalive=True,
    health_check_interval=30,
)

http_client = httpx.Client(
    limits=httpx.Limits(max_connections=200, max_keepalive_connections=40),
    timeout=httpx.Timeout(10.0, connect=10.0, read=10.0, write=10.0),
)


def task_process(url: str, data: Dict[str, Any], processor_type: str) -> bool:
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = http_client.post(url, json=data, headers=headers)
        response.raise_for_status()

        payment_data = {"id": data.get("correlationId"), "amount": data.get("amount"), "requested_at": data.get("requestedAt")}

        table_name = f"{processor_type}_payments"

        return insert_payment(table_name, payment_data)

    except Exception as exc:
        print(f"Erro ao processar o pagamento com o processador {processor_type}: {exc}")
        return False


@app_celery.task(name="payment_process", bind=True, max_retries=2, default_retry_delay=5)
def payment_process(self, data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        amount = data.get("amount", 0)
        code = data.get("correlationId", "default_correlation_id")
        now = datetime.now()

        default_url = f"{PAYMENT_DEFAULT}/payments"
        fallback_url = f"{PAYMENT_FALLBACK}/payments"

        payment_data = {
            "correlationId": code,
            "amount": amount,
            "requestedAt": now.isoformat() + "Z",
        }

        response_default = task_process(default_url, payment_data, "default")

        if not response_default:
            response_fallback = task_process(fallback_url, payment_data, "fallback")

            if not response_fallback:
                raise Exception("Não foi possível processar o pagamento com nenhum dos processadores disponíveis")

        return {"status": "success", "message": "Pagamento processado com sucesso"}

    except Exception as e:
        print(f"Reprocessar o pagamento devido ao erro: {e}")
        self.retry(exc=e)
