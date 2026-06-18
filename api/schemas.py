# ---------------------------------------------------------------------------
# PYDANTIC SCHEMAS (Request/Response Models)
# ---------------------------------------------------------------------------
# Pydantic models define the shape of API request bodies and responses.
# FastAPI automatically:
#   - Validates incoming data against these schemas
#   - Returns 422 Unprocessable Entity for invalid data
#   - Generates OpenAPI/Swagger documentation from the schemas
#   - Serializes responses to JSON

# BaseModel is the base class for all Pydantic models.
# Field adds extra validation and metadata to individual fields.
from pydantic import BaseModel, Field

# Optional is used for fields that may be absent (legacy style for Pydantic v2).
from typing import Optional


class Customer(BaseModel):
    """Represents a single customer record returned by GET /customers.

    Maps directly to the columns of the customers_rag_safe table.
    """

    customer_id: int
    first_name: str
    last_name: str
    age: int
    occupation: str
    annual_income: int
    customer_segment: str
    preferred_product: str

    class Config:
        # from_attributes allows constructing this model from ORM-style objects
        # (e.g. psycopg2 RealDictCursor rows).
        from_attributes = True


class AnalyticsResponse(BaseModel):
    """Aggregated customer analytics returned by GET /analytics.

    This schema is used for response_model validation, ensuring the
    endpoint always returns the expected fields.
    """

    total_customers: int
    average_income: float
    platinum_customers: int
    gold_customers: int
    silver_customers: int


class HealthResponse(BaseModel):
    """Health check response model for GET /health.

    Returns a simple {"status": "healthy"} payload.
    """

    status: str


class ChatRequest(BaseModel):
    """Request body model for POST /chat.

    Validates that the question field:
      - Is required (Field(...))
      - Has at least 1 character (min_length=1)
      - Does not exceed 2000 characters (max_length=2000)

    This prevents empty or overly long questions from reaching the LLM.
    """

    question: str = Field(..., min_length=1, max_length=2000)
