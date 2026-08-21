import json
import os

DB_FILE = "alerts_db.json"

def load_alerts() -> list:
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_alerts(alerts: list) -> None:
    with open(DB_FILE, "w") as f:
        json.dump(alerts, f, indent=2)
