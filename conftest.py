# conftest.py
import os

# 1. Force in-memory SQLite and test API key before any app module imports
TEST_DATABASE_URL = "sqlite://"
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ["API_KEY"] = "bear_robotics_prod_secret_abc123"

import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlalchemy.pool import StaticPool

# 2. Use StaticPool to ensure all connections share the same in-memory instance
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# 3. Patch the app's database engine BEFORE importing app components
import app.database
app.database.engine = test_engine

from app.main import app
from app.database import get_session
from app.models.alert import Alert  # noqa: F401 Register Alert model metadata


@pytest.fixture(autouse=True)
def setup_database():
    """Automatically creates tables before each test and drops them after."""
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture(name="client")
def client_fixture():
    """Provides a fresh TestClient instance with session overrides for every test."""
    def override_get_session():
        with Session(test_engine) as session:
            yield session

    app.dependency_overrides[get_session] = override_get_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
