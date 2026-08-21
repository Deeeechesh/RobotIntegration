from fastapi import APIRouter, Depends
from app.models.alert import RobotAlertPayload
from app.routers.auth import verify_api_key
from app.services.deduplication import process_and_store_alert

router = APIRouter(tags=["Alerts"])

pcc_token_store = {
    "status": "EMPTY",
    "current_state": {}
}

@router.post("/robot/alert")
async def receive_robot_alert(
    payload: RobotAlertPayload, 
    api_key: str = Depends(verify_api_key)
):
    result = process_and_store_alert(payload.model_dump())
    return result

@router.get("/pcc/inspect-token")
async def inspect_token():
    return pcc_token_store

@router.get("/pcc/callback")
async def pcc_callback(code: str):
    pcc_token_store["status"] = "ACTIVE_IN_RAM"
    pcc_token_store["current_state"] = {
        "access_token": f"pcc_live_bearer_token_{code}"
    }
    return {"message": "Token stored successfully", "code": code}
