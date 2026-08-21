from app.database import load_db, save_db

def process_and_store_alert(payload_dict):
    alerts = load_db()
    
    # Simple deduplication check based on eventId
    for existing in alerts:
        if existing.get("eventId") == payload_dict.get("eventId"):
            return {"status": "duplicate", "alert": existing}
            
    alerts.append(payload_dict)
    save_db(alerts)
    return {"status": "created", "alert": payload_dict}
