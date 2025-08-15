from pydantic import BaseModel


class PaymentsTotals(BaseModel):
    totalRequests: int
    totalAmount: float


class Summary(BaseModel):
    default: PaymentsTotals
    fallback: PaymentsTotals


class Payment(BaseModel):
    correlationId: str
    amount: float
