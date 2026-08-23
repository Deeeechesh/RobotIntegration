# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.database import create_db_and_tables
from app.routers.alerts import router as alerts_router
from app.routers.pcc import router as pcc_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Robot Alert Bridge Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(alerts_router)
app.include_router(pcc_router)


@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy"}