# ---------------------------------------------------------------------------
# AUTHENTICATION MODULE (reserved for future use)
# ---------------------------------------------------------------------------
# This module provides API key authentication via the X-API-KEY header.
# It is currently NOT used by any endpoint — all endpoints are public.
#
# To re-enable authentication on specific endpoints, add:
#   api_key: str = Depends(verify_api_key)
# as a parameter to the desired route function in main.py.
#
# The API key value is read from the .env file (API_KEY=customer-rag-secret-key).

import os

# HTTPException lets us return structured error responses (e.g. 401 Unauthorized).
# Security is a dependency marker similar to Depends but specific to security schemes.
from fastapi import HTTPException, Security

# APIKeyHeader is a FastAPI security utility that extracts the X-API-KEY
# header from incoming HTTP requests and passes it as a dependency.
from fastapi.security import APIKeyHeader

# python-dotenv loads .env file variables into os.environ.
from dotenv import load_dotenv

load_dotenv()

# Read the expected API key from the environment.
API_KEY = os.getenv("API_KEY")

# Define the header-based API key security scheme.
# name:        the HTTP header to look for ("X-API-KEY")
# auto_error:  if True, FastAPI automatically returns 403 when the header
#              is missing. We set it to False so we can return 401 ourselves
#              with a consistent error format.
api_key_header = APIKeyHeader(
    name="X-API-KEY",
    auto_error=False,
)


async def verify_api_key(
    api_key: str = Security(api_key_header),
) -> str:
    """Validate the X-API-KEY header against the configured API_KEY.

    Args:
        api_key: The value of the X-API-KEY header, extracted by FastAPI.

    Returns:
        The validated API key string if it matches.

    Raises:
        HTTPException (401): If the header value does not match API_KEY.
    """
    if api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key",
        )
    return api_key
