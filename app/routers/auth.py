# app/routers/auth.py
from fastapi import Header, HTTPException, status
from app.config import settings

# Pull API key from central configuration, with fallback to test key string
EXPECTED_API_KEY = getattr(settings, "API_KEY", "bear_robotics_prod_secret_abc123")


def verify_api_key(x_bridge_api_key: str = Header(None, alias="X-Bridge-API-Key")):
    """Validates presence and correctness of the X-Bridge-API-Key header."""
    if not x_bridge_api_key or x_bridge_api_key != EXPECTED_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API key",
        )
    return x_bridge_api_key