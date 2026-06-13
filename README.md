# AegisFlow

AegisFlow is a FastAPI backend for ingesting, validating, persisting, and risk-checking order-like events. The project is designed around clean backend architecture, database-backed persistence, structured API validation, and testable service-layer logic.

## Tech Stack

- **Backend:** Python, FastAPI, Pydantic
- **Database:** PostgreSQL, SQLAlchemy ORM, Alembic
- **Testing:** pytest, FastAPI TestClient
- **Tooling:** Git, GitHub, Docker

## Features

- REST API for event creation, retrieval, and listing
- Layered route, service, and storage architecture
- PostgreSQL persistence with SQLAlchemy ORM
- Alembic migrations for version-controlled database schema changes
- UUID primary keys and timezone-aware event timestamps
- Pydantic request and response validation
- Event normalization, including uppercase asset symbols
- Database-level check constraints for core data integrity rules
- Risk evaluation based on computed order value
- Rejected events persisted for auditability
- 50+ pytest tests covering API behavior, validation, risk decisions, UUID handling, timestamp formatting, and database-backed isolation

## Current API

### Health Check

```http
GET /health
```

Returns service health status.

### Create Event

```http
POST /events
```

Creates a validated event, computes order value, runs risk evaluation, persists the event, and returns the created record.

### Get Event by ID

```http
GET /events/{event_id}
```

Retrieves a single event by UUID.

### List Events

```http
GET /events
```

Returns all persisted events.

## Example Event Request

```json
{
  "event_type": "ORDER_SUBMITTED",
  "asset": "aapl",
  "side": "BUY",
  "quantity": 10,
  "price": 175.50
}
```

## Example Event Response

```json
{
  "event_id": "00000000-0000-0000-0000-000000000000",
  "status": "accepted",
  "created_at": "2026-05-01T12:00:00Z",
  "risk_approved": true,
  "risk_reason": null,
  "order_value": 1755.0,
  "event_type": "ORDER_SUBMITTED",
  "asset": "AAPL",
  "side": "BUY",
  "quantity": 10,
  "price": 175.5
}
```

## Project Structure

```text
app/
  api/
    routes/
  db/
    models.py
    session.py
  schemas/
  services/
  storage/
alembic/
  versions/
tests/
```

## Local Setup

### 1. Clone the repository

```bash
git clone <repository-url>
cd aegisflow
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start PostgreSQL with Docker

```bash
docker run --name aegisflow-postgres \
  -e POSTGRES_USER=aegisflow \
  -e POSTGRES_PASSWORD=aegisflow \
  -e POSTGRES_DB=aegisflow_dev \
  -p 5432:5432 \
  -d postgres:16
```

If the container already exists but is stopped:

```bash
docker start aegisflow-postgres
```

### 5. Configure environment variables

Create a `.env` file:

```env
DATABASE_URL=postgresql+psycopg://aegisflow:aegisflow@localhost:5432/aegisflow_dev
```

### 6. Apply database migrations

```bash
PYTHONPATH=. alembic upgrade head
```

### 7. Run the application

```bash
uvicorn app.main:app --reload
```

The API will be available at:

```text
http://127.0.0.1:8000
```

Interactive API docs:

```text
http://127.0.0.1:8000/docs
```

## Running Tests

```bash
pytest
```

The test suite covers endpoint behavior, validation errors, UUID handling, timestamp formatting, risk approval/rejection logic, and database-backed test isolation.

## Roadmap

Planned improvements include:

- Tenant model and tenant-scoped event ownership
- API-key authentication with hashed key storage
- Explicit permission scopes such as `events:read` and `events:write`
- Tenant-isolated event retrieval
- Idempotency keys for duplicate request protection
- Request signing and replay protection
- Audit log expansion
- Rate limiting and abuse controls

## Status

AegisFlow is an active backend engineering project focused on building production-style API architecture, persistence, validation, testing, and security-oriented design patterns.