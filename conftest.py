import os
import json
import pytest

DB_FILE = "alerts_db.json"

@pytest.fixture(autouse=True)
def reset_database():
    # Setup: Reset alerts_db.json before each test runs
    with open(DB_FILE, "w") as f:
        json.dump([], f)
        
    yield  # Test executes here
    
    # Teardown: Clean up after test completes
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump([], f)
