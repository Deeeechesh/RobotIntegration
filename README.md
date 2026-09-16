# ElderRobot Bridge (`robot_bridge`)

## Overview & Mission
The **ElderRobot Bridge** is an industrial-grade, edge-hosted adapter layer designed to ingest heterogeneous robot telemetry and safety alerts via an HTTP-first interface and normalize them for a central Command Center. The system prioritizes local resilience, defensive failure handling, and zero data loss through robust local persistence.

---

## 1. System Architecture & Data Flow
1. **Ingress Gate (FastAPI):** Receives HTTP POST payloads from autonomous robots. Acts as the primary security checkpoint for API key / Bearer token authentication.
2. **Validation & Normalization Layer:** Utilizes Pydantic schemas to validate incoming payloads and inject server-side UTC timestamps (`received_at`) to mitigate robot-side clock drift.
3. **Persistent Queue (SQLite + WAL Mode):** Stores validated payloads locally on disk using SQLite in Write-Ahead Logging (WAL) mode with explicit busy timeouts to handle concurrent read/write operations safely.
4. **Downstream Sync Worker:** Background worker loop that pulls from the persistent queue and synchronizes records upstream to the Platform Command Center (PCC).
5. **Dead-Letter Queue (DLQ):** Captures malformed payloads, validation failures, or permanently failing records for operator triage.

---

## 2. Directory Architecture Layout
```text
robot_bridge/
├── app/
│   ├── __init__.py
│   ├── main.py                # FastAPI app instantiation & top-level router inclusion
│   ├── config.py              # API keys, DB file paths, environment variables
│   ├── database.py            # State persistence & SQLite WAL operations
│   ├── models/
│   │   ├── __init__.py
│   │   └── alert.py           # RobotAlert, Location, and Pydantic schemas
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── auth.py            # Header API Key & Bearer token verification dependencies
│   │   └── alerts.py          # /robot/alert ingestion & DLQ management endpoints
│   └── services/
│       ├── __init__.py
│       └── deduplication.py   # Alert filtering, normalization, & state handling logic
├── docs/                      # Operational runbooks, architecture notes, and roadmaps
├── data/                      # Persistent volume directory for SQLite WAL database storage
└── test_main.py               # Test runner importing app.main:app
```

## 3. Summary of Component Roles & Responsibilities
Entry & Integration (main.py): Instantiates the FastAPI application and pulls in top-level routing to initialize the HTTP ingress gateway.

Security & Ingestion (routers/): Handles API key verification and Bearer token validation (auth.py) alongside incoming webhook/alert paths (alerts.py).

Business Logic (services/): Manages alert filtering, state handling, and de-duplication rules (deduplication.py).

Data & Schemas (database.py & models/): Persists state locally via SQLite WAL while enforcing strict typing via Pydantic schemas (alert.py).

## 4. Prerequisites & Environment Configuration
Prerequisites: Docker & Docker Compose, Python 3.10+ (for local development).

Create a .env file in the root directory with the following variables:

Code snippet
API_KEY=your-secure-bridge-api-key-here
DATABASE_URL=sqlite:///./data/elder_robot.db
PCC_API_URL=[https://pcc.internal.local/api/v1](https://pcc.internal.local/api/v1)
PCC_OAUTH_TOKEN=your-pcc-oauth-token

## 5. Quick Start (Docker Compose)
Build and start the containerized service:

Bash
docker-compose up --build -d
Verify container health and log output:

Bash
docker-compose logs -f bridge

## 6. Dead-Letter Queue (DLQ) API Summary
The edge bridge exposes administrative endpoints for managing quarantined telemetry records:

GET /api/v1/dlq/records — Retrieves a paginated list of failed records (supports filters for robot_id and error_type).

POST /api/v1/dlq/reprocess/{id} — Re-injects a quarantined record back into the active sync queue.

DELETE /api/v1/dlq/discard/{id} — Permanently purges an unrecoverable record from local storage and logs an audit trail entry.

POST /api/v1/dlq/batch — Performs bulk reprocess or discard actions on multiple record IDs simultaneously.
