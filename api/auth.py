import os

from fastapi import HTTPException, Security
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

api_key_header = APIKeyHeader(
    name="X-API-KEY",
    auto_error=False,
)


async def verify_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    """Validate the X-API-KEY header against the configured API_KEY."""
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
        )
    return api_key
