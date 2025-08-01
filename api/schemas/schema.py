from pydantic import BaseModel


class Default(BaseModel):
    totalRequests: int
    totalAmount: float


class Fallback(BaseModel):
    totalRequests: int
    totalAmount: float


class Summary(BaseModel):
    default: Default
    fallback: Fallback


class Payment(BaseModel):
    correlationId: str
    amount: float
