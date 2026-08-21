from datetime import datetime, timezone
from app.database import load_alerts, save_alerts

COOLDOWN_SECONDS = 60

def is_duplicate_alert(new_alert: dict, existing_alerts: list) -> bool:
    new_sn = new_alert.get("robotSn")
    new_event_id = new_alert.get("eventId")
    new_state = new_alert.get("state")
    
    # Parse ISO timestamp or fall back to UTC now
    try:
        new_ts = datetime.fromisoformat(new_alert.get("timestamp").replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        new_ts = datetime.now(timezone.utc)

    for alert in existing_alerts:
        # Check 1: Direct Event ID match
        if alert.get("eventId") == new_event_id:
            return True
            
        # Check 2: Cooldown check for same robot and same state
        if alert.get("robotSn") == new_sn and alert.get("state") == new_state:
            try:
                existing_ts = datetime.fromisoformat(alert.get("timestamp").replace("Z", "+00:00"))
                time_diff = abs((new_ts - existing_ts).total_seconds())
                if time_diff < COOLDOWN_SECONDS:
                    return True
            except (AttributeError, ValueError):
                continue

    return False

def process_and_store_alert(alert_data: dict):
    alerts = load_alerts()
    
    if is_duplicate_alert(alert_data, alerts):
        return {
            "status": "IGNORED",
            "reason": "Duplicate event ID or alert triggered within cooldown window",
            "eventId": alert_data.get("eventId")
        }
        
    alerts.append(alert_data)
    save_alerts(alerts)
    return {
        "status": "INGESTED",
        "eventId": alert_data.get("eventId")
    }
