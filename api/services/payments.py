from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.models.model import PaymentModel
from api.schemas.schema import Default, Fallback, Summary


class PaymentService:
    def __init__(self, session: Session):
        self.session = session

    def get_summary(self, initial: Optional[str] = None, final: Optional[str] = None) -> Summary:
        try:
            initial_date = initial.replace("Z", "").replace("T", " ") if initial else None
            final_date = final.replace("Z", "").replace("T", " ") if final else None

            stmt = """select
                p.processor_type,
                sum(p.amount) valor,
                count(p.id) total
            from
                payments p """
            params = {}

            if initial_date and final_date:
                params["initial"] = initial_date
                params["final"] = final_date

                stmt += """where
                    requested_at between :initial and :final """

            stmt += """group by
                p.processor_type"""

            stmt_text = text(stmt)

            results = self.session.execute(stmt_text, params).fetchall()

            default_total_requests = 0
            default_total_amount = 0
            fallback_total_requests = 0
            fallback_total_amount = 0

            for result in results:
                if result.processor_type == "default":
                    default_total_requests = result.total
                    default_total_amount = result.valor
                else:
                    fallback_total_requests = result.total
                    fallback_total_amount = result.valor

            default_summary = Default(totalRequests=default_total_requests, totalAmount=default_total_amount)
            fallback_summary = Fallback(totalRequests=fallback_total_requests, totalAmount=fallback_total_amount)

            return Summary(default=default_summary, fallback=fallback_summary)

        except ValueError as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Formato de data inválido: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao obter resumo: {str(e)}")

    def purge_database(self) -> None:
        try:
            # Deletar todos os registros da tabela payments
            deleted_count = self.session.query(PaymentModel).delete()

            # Confirmar a transação
            self.session.commit()

            print(f"Database purged successfully. {deleted_count} records deleted.")

        except Exception as e:
            # Fazer rollback em caso de erro
            self.session.rollback()
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Erro ao limpar o banco de dados: {str(e)}")
