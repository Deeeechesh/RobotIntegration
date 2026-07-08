from fastapi import FastAPI
from fastapi import Security, HTTPException, status
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel
from typing import Optional
import requests
import uvicorn
import json
import os

# UPGRADED MOCK ROSTER WITH ESCALATION PATHS
MOCK_PCC_ROSTER = {
    "West Wing": {
        "primary_nurse": {
            "name": "Sarah Jenkins, RN",
            "phone": "+19195551111"
        },
        "floor_supervisor": {
            "name": "David Miller, BSN",
            "phone": "+19195559999"
        },
        "shift": "Day"
    },
    "Memory Care": {
        "primary_nurse": {
            "name": "Marcus Vance, LPN",
            "phone": "+19195552222"
        },
        "floor_supervisor": {
            "name": "David Miller, BSN",
            "phone": "+19195559999"
        },
        "shift": "Day"
    }
}

# ACTIVE EVENTS TRACKER
# This acts as an in-memory cache to remember which alerts we are currently handling.
ACTIVE_ALERTS_CACHE = []

# 1. PASTE YOUR TELEGRAM DATA HERE
TELEGRAM_BOT_TOKEN = "8967549226:AAHZ1WGazmNdTk2lvCDJkHkwxYNULu4AoZs"
TELEGRAM_CHAT_ID = "8615303117"

app = FastAPI(title="Eldercare Robotics Integration Bridge")

# DATABASE CONFIGURATION
DB_FILE = "alerts_db.json"

# SECURITY CONFIGURATION
API_KEY_NAME = "X-Bridge-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# In production, this would live safely inside an environment variable
VALID_API_KEYS = {
    "bear_robotics_prod_secret_abc123",
    "keenon_robotics_test_xyz789"
}

def verify_api_key(api_key: str = Security(api_key_header)):
    """Validates the incoming header token against our approved security registry."""
    if api_key not in VALID_API_KEYS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Bridge-API-Key credentials."
        )
    return api_key

# Helper function to ensure the file exists on your hard drive
def initialize_database():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)  # Initialize with an empty JSON array
        print("💾 [DATABASE INITIALIZED] Created clean alerts_db.json file.")

# Run the initialization immediately when the server boots
initialize_database()

def read_active_alerts():
    """Reads the current active alerts directly from the hard drive."""
    with open(DB_FILE, "r") as f:
        return json.load(f)

def write_active_alert(event_id: str):
    """Saves a new active alert ID to the local JSON database file."""
    alerts = read_active_alerts()
    if event_id not in alerts:
        alerts.append(event_id)
        with open(DB_FILE, "w") as f:
            json.dump(alerts, f, indent=4)

class LocationData(BaseModel):
    mapId: str
    x: float
    y: float

class RobotAlertPayload(BaseModel):
    eventId: str
    robotSn: str
    timestamp: str
    state: str
    errorCode: Optional[str] = "NONE"
    location: LocationData

def send_telegram_alert(wing_name: str, robot_id: str, error: str):
    """Fires a live push notification to your Telegram app."""
    try:
        message_body = f"⚠️ [ROBOT ALERT]\nUnit: {robot_id}\nStatus: STUCK\nLocation: {wing_name}\nError: {error}\n\nPlease clear the corridor immediately."

        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message_body
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            print("📱 Alert successfully broadcasted via Telegram!")
        else:
            print(f"❌ Telegram API Error: {response.text}")
    except Exception as e:
        print(f"❌ Failed to send notification: {str(e)}")

@app.post("/robot/alert")
async def receive_robot_alert(
    payload: RobotAlertPayload,
    api_key: str = Security(verify_api_key)  # <-- The gatekeeper is active!
):
    # Keep your exact same try/except logic here...
    print(f"\n[🚨 AUTHORIZED SIGNAL] Webhook validated via key: {api_key[:10]}...")

    try:
        # Ensure critical identification data is present
        if not payload.eventId or not payload.location:
            raise ValueError("Payload missing critical tracking fields (eventId or location).")

        # 1. READ PERSISTENT CACHE FROM DISK
        current_active_alerts = read_active_alerts()

        # 2. DE-DUPLICATION CHECK
        if payload.eventId in current_active_alerts:
            print(f"🛑 [DUPLICATE BLOCKED] Event {payload.eventId} is already active on disk.")
            return {
                "status": "SUPPRESSED",
                "message": f"Alert for event {payload.eventId} is already active. No redundant actions taken."
            }

        # 3. PROCESS NEW CRITICAL ALERT
        if payload.state in ["ABORTED", "STUCK", "EMERGENCY"]:
            write_active_alert(payload.eventId)
            print(f"💾 [DATABASE WRITE] Logged event {payload.eventId} to disk.")

            # Access location safely using dot notation
            robot_location = payload.location.mapId
            print(f"⚠️ Querying PointClickCare Roster for zone: {robot_location}...")

            if robot_location in MOCK_PCC_ROSTER:
                nurse_name = MOCK_PCC_ROSTER[robot_location]["primary_nurse"]["name"]
                return {
                    "status": "SUCCESS",
                    "action": "STAFF_DISPATCHED",
                    "dispatched_to": nurse_name,
                    "event_tracked_id": payload.eventId
                }
            else:
                # Handle unknown location footprints safely without crashing
                print(f"⚠️ [ROSTER MISS] Location '{robot_location}' not mapped in current PointClickCare shift sheet.")
                return {
                    "status": "UNMAPPED_LOCATION",
                    "message": f"Alert captured but zone '{robot_location}' has no assigned clinician."
                }

        return {"status": "SUCCESS", "action": "LOGGED"}

    except Exception as e:
        # The safety net: catch anomalies, log the traceback, and protect the server runtime
        print(f"❌ [CRITICAL ERROR CAUGHT] Malformed webhook processed: {str(e)}")
        return {
            "status": "ERROR",
            "message": "Internal gateway processed an invalid payload structure."
        }

def remove_active_alert(event_id: str):
    """Removes a resolved event ID from the local JSON database file."""
    alerts = read_active_alerts()
    if event_id in alerts:
        alerts.remove(event_id)
        with open(DB_FILE, "w") as f:
            json.dump(alerts, f, indent=4)
        return True
    return False

@app.post("/robot/resolve")
async def resolve_robot_alert(
    payload: RobotAlertPayload,
    api_key: str = Security(verify_api_key)  # <-- The gatekeeper is active!
):
    # Keep your exact same resolution logic here...
    print(f"\n[✅ AUTHORIZED RESOLUTION] Token validated: {api_key[:10]}...")

    # Attempt to remove the alert from our persistent storage
    was_removed = remove_active_alert(payload.eventId)

    if was_removed:
        print(f"🧹 [DATABASE CLEANUP] Event {payload.eventId} successfully cleared from {DB_FILE}.")
        return {
            "status": "RESOLVED",
            "message": f"Event {payload.eventId} has been cleared. Channel is reset for this device."
        }
    else:
        print(f"❓ [NOTICE] Received resolution for Event {payload.eventId}, but it wasn't active in the DB.")
        return {
            "status": "NO_ACTION",
            "message": "Event was not found in active cache. No cleanup required."
        }

@app.post("/robot/alert/escalate")
async def simulate_escalation_check(payload: RobotAlertPayload, primary_responded: bool = False):
    robot_location = payload.location.mapId

    print(f"\n[⏱️ TIMEOUT CHECK] Checking status of crisis event {payload.eventId} in {robot_location}...")

    if robot_location not in MOCK_PCC_ROSTER:
        return {"status": "ERROR", "message": "Unknown facility location"}

    facility_zone = MOCK_PCC_ROSTER[robot_location]
    primary_contact = facility_zone["primary_nurse"]["name"]
    supervisor_contact = facility_zone["floor_supervisor"]["name"]
    supervisor_phone = facility_zone["floor_supervisor"]["phone"]

    # Scenario A: The primary nurse cleared the obstacle
    if primary_responded:
        print(f"✅ [RESOLVED] {primary_contact} cleared the robot. Closing ticket.")
        return {"status": "RESOLVED", "message": f"Ticket closed by {primary_contact}."}

    # Scenario B: 3 minutes passed with zero response (The Escalation Trigger)
    print(f"🚨 [TIMEOUT] No response from {primary_contact} within 3 minutes!")
    print(f"⚡ [ESCALATING] Dispatching emergency notification to Supervisor: {supervisor_contact} ({supervisor_phone})")

    # NOTE: When you test this at home later, this is where the Telegram/Twilio
    # function would dynamically text the supervisor's phone instead!

    return {
        "status": "ESCALATED",
        "action": "SUPERVISOR_NOTIFIED",
        "notified_party": supervisor_contact,
        "priority": "HIGH"
    }

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)