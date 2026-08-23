Learning integrations

Architecture
robot_bridge/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app instantiation & top-level router inclusion
│   ├── config.py            # API keys, DB file paths, environment variables
│   ├── database.py          # State persistence & JSON file operations (`alerts_db.json`)
│   ├── models/
│   │   ├── __init__.py
│   │   └── alert.py         # RobotAlert, Location, and Pydantic schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py          # OAuth & Header API Key verification dependencies
│   │   └── alerts.py        # /robot/alert ingestion & de-duplication endpoints
│   └── services/
│       ├── __init__.py
│       └── deduplication.py # Alert filtering & state handling logic
└── test_main.py             # Refactored to import app.main:app