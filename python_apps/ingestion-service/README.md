# Elevaite Ingestion Service

A microservice for running ingestion jobs with DBOS durable execution.

## Overview

The Ingestion Service provides a REST API for creating and managing ingestion jobs that execute the `elevaite_ingestion` pipeline. It uses DBOS for durable, parallel execution and integrates with the workflow engine via DBOS event topics.

## Architecture

- **FastAPI** for REST API endpoints
- **DBOS** for durable workflow execution
- **SQLModel** for database models
- **PostgreSQL** for job persistence

## API Endpoints

### POST /ingestion/jobs

Create a new ingestion job.

**Request:**
```json
{
  "config": {
    // elevaite_ingestion configuration
  },
  "metadata": {
    "tenant_id": "org-123",
    "execution_id": "exec-456",
    "step_id": "ingestion-step",
    "callback_topic": "wf:exec-456:ingestion-step:ingestion_done"
  }
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "status": "PENDING",
  "created_at": "2024-01-01T00:00:00Z"
}
```

### GET /ingestion/jobs/{job_id}

Get the status of an ingestion job.

**Response:**
```json
{
  "job_id": "uuid",
  "status": "SUCCEEDED",
  "result_summary": {
    "files_processed": 10,
    "chunks_created": 500,
    "embeddings_generated": 500
  },
  "created_at": "2024-01-01T00:00:00Z",
  "completed_at": "2024-01-01T00:05:00Z"
}
```

## Setup

1. Install dependencies:
```bash
cd python_apps/ingestion-service
pip install -e .
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env with your database URLs
```

3. Run database migrations:
```bash
alembic upgrade head
```

4. Start the service:
```bash
uvicorn ingestion_service.main:app --host 0.0.0.0 --port 8000
```

## Integration with Workflow Engine

The ingestion service integrates with the workflow engine via:

1. **Ingestion Step**: A workflow step type that calls the ingestion service
2. **DBOS Events**: Completion events sent on callback topics
3. **Durable Execution**: DBOS ensures jobs complete even if the service restarts

### Workflow Integration Flow

1. Workflow executes an ingestion step
2. Step calls `POST /ingestion/jobs` with callback topic
3. Service creates job and starts DBOS workflow
4. Step returns `status="ingesting"` (not `WAITING`)
5. Workflow engine blocks on callback topic via DBOS
6. Ingestion completes and sends event on callback topic
7. Workflow engine receives event and re-runs step
8. Step checks job status and returns `success=True`

## Development

Run tests:
```bash
pytest
```

Format code:
```bash
black .
ruff check --fix .
```

## Configuration

Environment variables:

- `DATABASE_URL`: PostgreSQL connection string for job storage
- `DBOS_DATABASE_URL`: PostgreSQL connection string for DBOS system tables
- `SERVICE_HOST`: Host to bind to (default: 0.0.0.0)
- `SERVICE_PORT`: Port to bind to (default: 8000)
- `LOG_LEVEL`: Logging level (default: INFO)

