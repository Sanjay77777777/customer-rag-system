from pydantic import BaseModel, Field
from typing import Optional


class Customer(BaseModel):
    """Represents a single customer record."""

    customer_id: int
    first_name: str
    last_name: str
    age: int
    occupation: str
    annual_income: int
    customer_segment: str
    preferred_product: str

    class Config:
        from_attributes = True


class AnalyticsResponse(BaseModel):
    """Aggregated customer analytics."""

    total_customers: int
    average_income: float
    platinum_customers: int
    gold_customers: int
    silver_customers: int


class HealthResponse(BaseModel):
    """Health check response."""

    status: str


class ChatRequest(BaseModel):
    """Chat question request body."""

    question: str = Field(..., min_length=1, max_length=2000)
