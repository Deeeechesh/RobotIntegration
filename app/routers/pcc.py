# app/routers/pcc.py
from typing import Any, Dict
from fastapi import APIRouter

router = APIRouter(prefix="/pcc", tags=["PCC"])

_pcc_token_store: Dict[str, Any] = {}


@router.get("/inspect-token")
def inspect_token():
    access_token = _pcc_token_store.get("access_token")
    if not access_token:
        return {"status": "EMPTY", "current_state": None}

    return {
        "status": "ACTIVE_IN_RAM",
        "current_state": {"access_token": access_token},
    }


@router.get("/callback")
def pcc_callback(code: str):
    _pcc_token_store["access_token"] = f"pcc_live_bearer_token_{code}"
    return {"status": "SUCCESS"}