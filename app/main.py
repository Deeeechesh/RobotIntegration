# app/main.py
from fastapi import FastAPI
from app.routers.alerts import router as alerts_router

app = FastAPI(
    title="Robot Alert Bridge Service",
    version="1.0.0",
)

# Include feature routers
app.include_router(alerts_router)

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}