# test_main.py
API_KEY = "bear_robotics_prod_secret_abc123"

# --- SECURITY GATE TESTS ---
def test_alert_missing_api_key(client):
    response = client.post(
        "/robot/alert",
        json={
            "robotSn": "bot_01",
            "location": {"mapId": "Floor_1_North"},
            "alert_type": "OBSTACLE_STUCK",
        },
    )
    assert response.status_code == 401


def test_alert_invalid_api_key(client):
    response = client.post(
        "/robot/alert",
        headers={"X-Bridge-API-Key": "wrong-key"},
        json={
            "robotSn": "bot_01",
            "location": {"mapId": "Floor_1_North"},
            "alert_type": "OBSTACLE_STUCK",
        },
    )
    assert response.status_code == 401


# --- ROBOT INGESTION & DE-DUPLICATION TESTS ---
def test_successful_alert_ingestion(client):
    payload = {
        "robotSn": "bot_01",
        "eventId": "evt_1001",
        "state": "OBSTACLE_STUCK",
        "location": {"mapId": "Floor_1_North"},
        "severity": "HIGH",
        "timestamp": "2026-08-03T21:48:00Z",
    }
    response = client.post(
        "/robot/alert", headers={"X-Bridge-API-Key": API_KEY}, json=payload
    )
    assert response.status_code == 200, response.json()


def test_duplicate_alert_filtering(client):
    payload = {
        "robotSn": "bot_01",
        "eventId": "evt_1001",
        "state": "OBSTACLE_STUCK",
        "location": {"mapId": "Floor_1_North"},
        "severity": "HIGH",
        "timestamp": "2026-08-03T21:48:00Z",
    }
    headers = {"X-Bridge-API-Key": API_KEY}

    res1 = client.post("/robot/alert", headers=headers, json=payload)
    assert res1.status_code == 200, res1.json()

    res2 = client.post("/robot/alert", headers=headers, json=payload)
    assert res2.status_code == 200, res2.json()


# --- PCC OAUTH & STATE INSPECTION TESTS ---
def test_pcc_state_lifecycle(client):
    res1 = client.get("/pcc/inspect-token")
    assert res1.json()["status"] == "EMPTY"

    res2 = client.get("/pcc/callback?code=test_auth_code_99")
    assert res2.status_code == 200

    res3 = client.get("/pcc/inspect-token")
    assert res3.json()["status"] == "ACTIVE_IN_RAM"
    assert "pcc_live_bearer_token" in res3.json()["current_state"]["access_token"]


def test_cooldown_alert_filtering(client):
    payload_initial = {
        "robotSn": "bot_99",
        "eventId": "evt_2001",
        "state": "BATTERY_CRITICAL",
        "location": {"mapId": "Floor_2"},
        "severity": "HIGH",
        "timestamp": "2026-08-20T20:00:00Z",
    }

    payload_rapid_fire = {
        "robotSn": "bot_99",
        "eventId": "evt_2002",
        "state": "BATTERY_CRITICAL",
        "location": {"mapId": "Floor_2"},
        "severity": "HIGH",
        "timestamp": "2026-08-20T20:00:15Z",
    }

    headers = {"X-Bridge-API-Key": API_KEY}

    res1 = client.post("/robot/alert", headers=headers, json=payload_initial)
    assert res1.json()["status"] == "INGESTED"

    res2 = client.post("/robot/alert", headers=headers, json=payload_rapid_fire)
    assert res2.json()["status"] == "IGNORED"
