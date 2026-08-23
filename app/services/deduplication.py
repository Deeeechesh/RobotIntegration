# app/services/deduplication.py
from datetime import datetime, timezone, timedelta
from sqlmodel import Session, select
from app.models.alert import Alert


def process_and_store_alert(session: Session, payload):
    """
    Handles alert ingestion, deduplication, and cooldown window enforcement.
    Safely handles both Pydantic models and raw dictionaries without raising AttributeErrors.
    """
    # Universal payload normalization to dictionary
    if hasattr(payload, "model_dump"):
        data = payload.model_dump()
    elif hasattr(payload, "dict"):
        data = payload.dict()
    elif isinstance(payload, dict):
        data = payload
    else:
        # Fallback if it's an object with attributes
        data = {
            "robotSn": getattr(payload, "robotSn", None) or getattr(payload, "robot_sn", "unknown_robot"),
            "eventId": getattr(payload, "eventId", None) or getattr(payload, "event_id", None),
            "state": getattr(payload, "state", None) or getattr(payload, "alert_type", "UNKNOWN"),
            "severity": getattr(payload, "severity", "MEDIUM"),
            "timestamp": getattr(payload, "timestamp", None),
        }

    # Extract fields safely using the normalized dictionary
    robot_sn = data.get("robotSn") or data.get("robot_sn") or "unknown_robot"
    event_id = data.get("eventId") or data.get("event_id")
    
    alert_state = (
        data.get("state")
        or data.get("alert_type")
        or "UNKNOWN"
    )

    # 1. Exact Event ID Deduplication
    if event_id:
        existing_event = session.exec(
            select(Alert).where(Alert.event_id == event_id)
        ).first()
        if existing_event:
            return {"status": "DUPLICATE_IGNORED", "event_id": event_id}

    # Extract & parse timestamp with fallback to current UTC time
    event_time_raw = data.get("timestamp")
    if isinstance(event_time_raw, str) and event_time_raw:
        try:
            event_time = datetime.fromisoformat(event_time_raw.replace("Z", "+00:00"))
        except ValueError:
            event_time = datetime.now(timezone.utc)
    elif isinstance(event_time_raw, datetime):
        event_time = event_time_raw
    else:
        event_time = datetime.now(timezone.utc)
        event_time_raw = event_time.isoformat()

    # 2. Cooldown Filtering (60-second window for same robot & state)
    cooldown_threshold = event_time - timedelta(seconds=60)

    existing_alerts = session.exec(
        select(Alert).where(
            Alert.robot_sn == robot_sn,
            Alert.state == alert_state,
        )
    ).all()

    for past_alert in existing_alerts:
        try:
            past_time = datetime.fromisoformat(
                past_alert.timestamp.replace("Z", "+00:00")
            )
            if past_time >= cooldown_threshold:
                return {"status": "IGNORED", "reason": "COOLDOWN_ACTIVE"}
        except (ValueError, AttributeError):
            continue

    # 3. Store New Alert
    severity = data.get("severity") or "MEDIUM"

    new_alert = Alert(
        robot_sn=robot_sn,
        event_id=event_id,
        state=alert_state,
        severity=severity,
        timestamp=event_time_raw if isinstance(event_time_raw, str) else event_time.isoformat(),
    )

    session.add(new_alert)
    session.commit()
    session.refresh(new_alert)

    return {"status": "INGESTED", "alert_id": new_alert.id}