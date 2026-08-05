# app/routers/alerts.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any

from app.models.alert import RobotAlertPayload
from app.routers.auth import verify_api_key
from app.database import load_db, save_db
from app.services.deduplication import process_and_store_alert

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
    dependencies=[Depends(verify_api_key)],
)

@router.post("", status_code=status.HTTP_201_CREATED)
async def ingest_alert(payload: RobotAlertPayload):
    """
    Ingests dynamic robot alert status payloads. Returns 201 on success or
    409 Conflict if duplicate eventId + robotSn payload exists.
    """
    db_data = load_db()
    result = process_and_store_alert(payload, db_data)
    
    if not result["inserted"]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Duplicate alert detected for this robot and event",
        )
    
    save_db(db_data)
    return {"status": "accepted", "alert": payload.model_dump()}

@router.get("", response_model=List[Dict[str, Any]])
async def get_alerts():
    """
    Retrieves all ingested robot alerts.
    """
    db_data = load_db()
    return db_data.get("alerts", [])