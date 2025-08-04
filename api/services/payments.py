from datetime import datetime
from typing import Optional

import asyncpg
from fastapi import HTTPException, status

from schemas.schema import Default, Fallback, Summary


class PaymentService:
    def __init__(self, session: asyncpg.Connection):
        self.session = session

    async def get_summary(self, initial: Optional[str] = None, final: Optional[str] = None) -> Summary:
        try:
            initial_date = datetime.fromisoformat(initial.replace("Z", "").replace("T", " ")) if initial else None
            final_date = datetime.fromisoformat(final.replace("Z", "").replace("T", " ")) if final else None
            default_total_requests = 0
            default_total_amount = 0
            fallback_total_requests = 0
            fallback_total_amount = 0

            stmt = """select
                p.processor_type,
                sum(p.amount) valor,
                count(p.id) total
            from
                payments p """
            params = []

            if initial_date and final_date:
                params = [initial_date, final_date]

                stmt += """where
                    requested_at between $1 and $2 """

            stmt += """group by
                p.processor_type"""

            results = await self.session.fetch(stmt, *params)

            for row in results:
                processor_type = row["processor_type"]
                valor = row["valor"]
                total = row["total"]

                if processor_type == "default":
                    default_total_requests = total
                    default_total_amount = valor
                else:
                    fallback_total_requests = total
                    fallback_total_amount = valor

            default_summary = Default(totalRequests=default_total_requests, totalAmount=default_total_amount)
            fallback_summary = Fallback(totalRequests=fallback_total_requests, totalAmount=fallback_total_amount)

            return Summary(default=default_summary, fallback=fallback_summary)

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Formato de data inválido: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao obter resumo: {str(e)}")

    async def purge_database(self) -> None:
        transaction = self.session.transaction()
        try:
            await transaction.start()

            await self.session.execute("DELETE FROM payments")
            await self.session.execute("ALTER SEQUENCE payments_id_seq RESTART WITH 1")

            await transaction.commit()
            print("Database purged successfully. records deleted.")

        except Exception as e:
            await transaction.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao limpar o banco de dados: {str(e)}")
