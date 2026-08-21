from datetime import datetime, timezone
from app.database import load_alerts, save_alerts
from app.logger import logger

COOLDOWN_SECONDS = 60

def is_duplicate_alert(new_alert: dict, existing_alerts: list) -> bool:
    new_sn = new_alert.get("robotSn")
    new_event_id = new_alert.get("eventId")
    new_state = new_alert.get("state")
    
    try:
        new_ts = datetime.fromisoformat(new_alert.get("timestamp").replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        new_ts = datetime.now(timezone.utc)

    for alert in existing_alerts:
        if alert.get("eventId") == new_event_id:
            logger.debug(f"Duplicate check hit: Exact Event ID match '{new_event_id}'")
            return True
            
        if alert.get("robotSn") == new_sn and alert.get("state") == new_state:
            try:
                existing_ts = datetime.fromisoformat(alert.get("timestamp").replace("Z", "+00:00"))
                time_diff = abs((new_ts - existing_ts).total_seconds())
                if time_diff < COOLDOWN_SECONDS:
                    logger.debug(f"Duplicate check hit: Cooldown active for robot '{new_sn}' in state '{new_state}' ({time_diff}s < {COOLDOWN_SECONDS}s)")
                    return True
            except (AttributeError, ValueError):
                continue

    return False

def process_and_store_alert(alert_data: dict):
    alerts = load_alerts()
    event_id = alert_data.get("eventId")
    robot_sn = alert_data.get("robotSn")
    state = alert_data.get("state")

    if is_duplicate_alert(alert_data, alerts):
        logger.info(f"Alert IGNORED [Duplicate/Cooldown] | Robot: {robot_sn} | Event: {event_id} | State: {state}")
        return {
            "status": "IGNORED",
            "reason": "Duplicate event ID or alert triggered within cooldown window",
            "eventId": event_id
        }
        
    alerts.append(alert_data)
    save_alerts(alerts)
    logger.success(f"Alert INGESTED | Robot: {robot_sn} | Event: {event_id} | State: {state}")
    
    return {
        "status": "INGESTED",
        "eventId": event_id
    }
