from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, Numeric, String

from api.config import Base


class PaymentModel(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, autoincrement=True)
    correlationId = Column(String)
    amount = Column(Numeric(precision=10, scale=2), nullable=False)
    processor_type = Column(String, nullable=False)
    requested_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"Transaction(id='{self.id}', amount={self.amount}, requested_at='{self.requested_at}')>"
