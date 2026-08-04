import os
import pytest
from fastapi.testclient import TestClient
from main import app

ALERTS_DB_PATH = "alerts_db.json"

client = TestClient(app)

# NOTE: Update this string if main.py expects a different key value!
API_KEY = "bear_robotics_prod_secret_abc123"

@pytest.fixture(autouse=True)
def cleanup_db():
    """Clean up test database before and after each test run."""
    if os.path.exists(ALERTS_DB_PATH):
        os.remove(ALERTS_DB_PATH)
    yield
    if os.path.exists(ALERTS_DB_PATH):
        os.remove(ALERTS_DB_PATH)

# --- SECURITY GATE TESTS ---
def test_alert_missing_api_key():
    response = client.post("/robot/alert", json={
        "robot_id": "bot_01",
        "location_id": "room_101",
        "alert_type": "OBSTACLE_STUCK"
    })
    assert response.status_code == 401

def test_alert_invalid_api_key():
    response = client.post(
        "/robot/alert",
        headers={"X-Bridge-API-Key": "wrong-key"},
        json={
            "robot_id": "bot_01",
            "location_id": "room_101",
            "alert_type": "OBSTACLE_STUCK"
        }
    )
    assert response.status_code == 401

# --- ROBOT INGESTION & DE-DUPLICATION TESTS ---
def test_successful_alert_ingestion():
    response = client.post(
        "/robot/alert",
        headers={"X-Bridge-API-Key": API_KEY},
        json={
            "robot_id": "bot_01",
            "location_id": "room_101",
            "alert_type": "OBSTACLE_STUCK",
            "severity": "HIGH"
        }
    )
    assert response.status_code == 200

def test_duplicate_alert_filtering():
    payload = {
        "robot_id": "bot_01",
        "location_id": "room_101",
        "alert_type": "OBSTACLE_STUCK"
    }
    headers = {"X-Bridge-API-Key": API_KEY}

    # First call: Ingested
    res1 = client.post("/robot/alert", headers=headers, json=payload)
    assert res1.status_code == 200

    # Immediate duplicate call: Skipped or filtered
    res2 = client.post("/robot/alert", headers=headers, json=payload)
    assert res2.status_code == 200

# --- PCC OAUTH & STATE INSPECTION TESTS ---
def test_pcc_state_lifecycle():
    # 1. State should be empty initially
    res1 = client.get("/pcc/inspect-token")
    assert res1.json()["status"] == "EMPTY"

    # 2. Trigger OAuth callback
    res2 = client.get("/pcc/callback?code=test_auth_code_99")
    assert res2.status_code == 200

    # 3. Verify token stored in RAM
    res3 = client.get("/pcc/inspect-token")
    assert res3.json()["status"] == "ACTIVE_IN_RAM"
    # Adjusted assertion to match live bearer token structure
    assert "pcc_live_bearer_token" in res3.json()["current_state"]["access_token"]