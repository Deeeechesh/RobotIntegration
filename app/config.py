# app/config.py
# app/config.py
import os

API_KEY_HEADER_NAME = "X-Bridge-API-Key"
API_KEY = os.getenv("API_KEY", "bear_robotics_prod_secret_abc123")
DB_FILE_PATH = os.getenv("DB_FILE_PATH", "alerts_db.json")
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_FILE_PATH}")


class Settings:
    API_KEY_HEADER_NAME: str = API_KEY_HEADER_NAME
    API_KEY: str = API_KEY
    DATABASE_URL: str = DATABASE_URL


settings = Settings()