from datetime import datetime
from typing import Optional

from fastapi import HTTPException, status

from infra.postgres_client import AsyncPostgresDB
from infra.redis_client import RedisClient
from schemas.schema import Payment, PaymentsTotals, Summary
from services.queue import queue_payments


class PaymentService:
    def __init__(self) -> None:
        self.redis_client = RedisClient().get_client()
        self.db = AsyncPostgresDB()

    async def insert_payment(self, data: Payment):
        queue_payments.put_nowait(data)

    async def get_summary(self, initial: Optional[str] = None, final: Optional[str] = None) -> Summary:
        try:
            initial_date = datetime.fromisoformat(initial.replace("Z", "").replace("T", " ")) if initial else None
            final_date = datetime.fromisoformat(final.replace("Z", "").replace("T", " ")) if final else None

            default_total_requests = 0
            default_total_amount = 0
            fallback_total_requests = 0
            fallback_total_amount = 0
            async with self.db.connection() as conn:
                async with conn.transaction():
                    stmt = """select
                        p.process_type,
                        round(sum(p.amount), 2) valor,
                        count(p.id) total
                    from
                        payments p """
                    params = []

                    if initial_date and final_date:
                        params = [initial_date, final_date]

                        stmt += """where
                            p.requested_at between $1 and $2 """

                    stmt += """group by
                        p.process_type;"""

                    results = await conn.fetch(stmt, *params)

            for row in results:
                processor_type = row["process_type"]
                valor = row["valor"]
                total = row["total"]

                if processor_type == "default":
                    default_total_requests = total
                    default_total_amount = valor
                elif processor_type == "fallback":
                    fallback_total_requests = total
                    fallback_total_amount = valor
                else:
                    continue

            default_summary = PaymentsTotals(totalRequests=default_total_requests, totalAmount=default_total_amount)
            fallback_summary = PaymentsTotals(totalRequests=fallback_total_requests, totalAmount=fallback_total_amount)

            return Summary(default=default_summary, fallback=fallback_summary)

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Formato de data inválido: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao obter resumo: {str(e)}")

    async def purge_database(self) -> None:
        try:
            async with self.db.connection() as conn:
                async with conn.transaction():
                    await conn.execute("DELETE FROM payments")
                    await conn.execute("ALTER SEQUENCE payments_id_seq RESTART WITH 1")

            print("Database purged successfully. records deleted.")

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao limpar o banco de dados: {str(e)}")
