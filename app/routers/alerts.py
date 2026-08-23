# app/routers/alerts.py
from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from app.database import get_session
from app.models.alert import RobotAlertPayload
from app.routers.auth import verify_api_key
from app.services.deduplication import process_and_store_alert

router = APIRouter(prefix="/robot", tags=["Alerts"])


@router.post("/alert", status_code=status.HTTP_200_OK)
def receive_alert(
    payload: RobotAlertPayload,
    api_key: str = Depends(verify_api_key),
    session: Session = Depends(get_session),
):
    """
    Ingests inbound robot alerts, validates payload structure via Pydantic,
    and delegates deduplication & persistence to process_and_store_alert.
    """
    result = process_and_store_alert(session, payload)
    return result