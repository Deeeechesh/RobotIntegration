from fastapi import APIRouter, Header, HTTPException, status
from pydantic import BaseModel
import os
from app.logger import logger

router = APIRouter()

EXPECTED_API_KEY = os.getenv("API_KEY", "bear_robotics_prod_secret_abc123")

# RAM-backed token state
RAM_TOKEN_STORE = {}

class TokenRequest(BaseModel):
    grant_type: str
    client_id: str
    client_secret: str

def verify_api_key(x_bridge_api_key: str = Header(None, alias="X-Bridge-API-Key")):
    if not x_bridge_api_key:
        logger.warning("Authentication failed: Missing X-Bridge-API-Key header.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing API key")
        
    if x_bridge_api_key != EXPECTED_API_KEY:
        logger.warning(f"Authentication failed: Invalid API key provided: '{x_bridge_api_key}'")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
        
    logger.debug("API key authenticated successfully.")
    return x_bridge_api_key

@router.post("/pcc/oauth/token")
def issue_pcc_token(req: TokenRequest):
    logger.info(f"PCC OAuth token request received for client_id: {req.client_id}")
    RAM_TOKEN_STORE["ACTIVE_IN_RAM"] = True
    RAM_TOKEN_STORE["client_id"] = req.client_id
    
    return {
        "access_token": "mock-pcc-bearer-token-12345",
        "token_type": "Bearer",
        "expires_in": 3600,
        "pcc_state": "ACTIVE_IN_RAM"
    }
