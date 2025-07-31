from datetime import datetime

import httpx
import redis

from api.config import settings

from ..config import app_celery, default_tbl, fallback_tbl

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


def task_process(url, data, type, now) -> bool:
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        response = http_client.post(url, json=data, headers=headers)
        response.raise_for_status()

        data_db = {
            "id": data.get("correlationId"),
            "valor": data.get("amount"),
            "data": now.strftime("%Y-%m-%d %H:%M:%S"),
        }

        if type == "default":
            default_tbl.insert(data_db)
        else:
            fallback_tbl.insert(data_db)

        return True
    except (httpx.HTTPStatusError, httpx.RequestError) as exc:
        print(f"Error processing {type} payment: {exc}")
        return False


@app_celery.task(name="payment_process", bind=True, max_retries=2, default_retry_delay=5)
def payment_process(self, data: dict):
    try:
        amount = data.get("amount", 0)
        code = data.get("correlationId", "default_correlation_id")
        now = datetime.now()

        defaut_url = f"{PAYMENT_DEFAULT}/payments"
        fallback_url = f"{PAYMENT_FALLBACK}/payments"

        data_json = {
            "correlationId": code,
            "amount": amount,
            "requestedAt": now.isoformat(),
        }

        response_default = task_process(defaut_url, data_json, "default", now)

        if not response_default:
            response_fallback = task_process(fallback_url, data_json, "fallback", now)
            if not response_fallback:
                raise Exception("Both default and fallback payment processors failed")

        return {"status": "success", "message": "Payment processed"}
    except Exception as e:
        print(f"Retrying payment process due to: {e}")
        self.retry(exc=e)
