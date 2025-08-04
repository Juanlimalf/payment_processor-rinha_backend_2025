from datetime import datetime
from typing import Any, Dict

import httpx
import psycopg2

from config import settings

PAYMENT_DEFAULT = settings.PAYMENT_PROCESSOR_DEFAULT
PAYMENT_FALLBACK = settings.PAYMENT_PROCESSOR_FALLBACK

conn = psycopg2.connect(settings.DATABASE_URL)
session = conn.cursor()


http_client = httpx.Client(
    limits=httpx.Limits(max_connections=200, max_keepalive_connections=40),
    timeout=httpx.Timeout(10.0, connect=10.0, read=10.0, write=10.0),
)


def task_process(url: str, data: Dict[str, Any], processor_type: str, now: datetime) -> bool:
    try:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        print(f"Processando o pagamento com o processador {processor_type}")

        response = http_client.post(url, json=data, headers=headers)
        print(response)

        if response.status_code == 422:
            return True

        if response.status_code != 200:
            print(f"Pagamento processado com sucesso com o processador {processor_type}")
            return False

        session.execute(
            """
            INSERT INTO payments (
                "correlationId",
                amount,
                processor_type,
                requested_at
            ) VALUES (%s, %s, %s, %s)
            """,
            (data["correlationId"], data["amount"], processor_type, now),
        )

        conn.commit()

        return True

    except Exception as exc:
        print(f"Erro ao processar o pagamento com o processador {processor_type}: {exc}")
        return False


def payment_process(data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        amount = data.get("amount", 0)
        code = data.get("correlationId", "default_correlation_id")
        now = datetime.now()

        print(data)

        default_url = f"{PAYMENT_DEFAULT}/payments"
        fallback_url = f"{PAYMENT_FALLBACK}/payments"

        payment_data = {
            "correlationId": code,
            "amount": amount,
            "requestedAt": now.isoformat() + "Z",
        }

        response_default = task_process(default_url, payment_data, "default", now)

        if not response_default:
            response_fallback = task_process(fallback_url, payment_data, "fallback", now)

            if not response_fallback:
                raise Exception("Não foi possível processar o pagamento com nenhum dos processadores disponíveis")

        return {"status": "success", "message": "Pagamento processado com sucesso"}

    except Exception as e:
        print(f"Reprocessar o pagamento devido ao erro: {e}")
        raise
