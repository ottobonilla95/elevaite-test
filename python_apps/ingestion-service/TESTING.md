# Ingestion Service Testing Guide

This document describes the comprehensive test suite for the ingestion service.

## Test Structure

The test suite is organized into several categories:

### 1. API Tests (`tests/test_api.py`)

Tests for the FastAPI endpoints:

- **POST /ingestion/jobs**
  - Successful job creation
  - Validation errors for invalid config
  - DBOS workflow start verification

- **GET /ingestion/jobs/{job_id}**
  - Successful job retrieval
  - 404 handling for non-existent jobs
  - Response format validation

- **GET /health**
  - Health check endpoint

### 2. Workflow Tests (`tests/test_workflows.py`)

Tests for DBOS workflow execution:

- **execute_ingestion_pipeline**
  - Pipeline execution placeholder
  - Result structure validation

- **send_completion_event**
  - Successful event dispatch
  - Missing callback_topic handling
  - Event send failure logging

- **run_ingestion_job**
  - Successful job execution flow
  - Job not found handling
  - Pipeline execution failure
  - Status transitions (PENDING → RUNNING → SUCCEEDED/FAILED)
  - Event dispatch on completion

### 3. Model Tests (`tests/test_models.py`)

Tests for data models:

- **JobStatus enum**
  - All status values defined
  - String value validation

- **IngestionJob model**
  - Minimal job creation
  - Full job creation with all fields
  - Status transitions
  - Failed jobs with error messages
  - Completion timestamps

- **CreateJobRequest model**
  - Minimal request
  - Request with metadata
  - Complex nested config

- **JobResponse model**
  - Response from job
  - Failed job response

### 4. End-to-End Tests (`tests/test_e2e.py`)

Complete lifecycle tests:

- **Complete job lifecycle**
  - Create → Execute → Complete (success)
  - Create → Execute → Fail

- **Concurrent jobs**
  - Multiple jobs created concurrently
  - Job ID uniqueness

- **Error scenarios**
  - Database connection failure
  - DBOS workflow start failure
  - Invalid job configuration
  - Malformed JSON

- **Idempotency**
  - Getting same job multiple times returns consistent results

### 5. Error Scenario Tests (`tests/test_error_scenarios.py`)

Edge cases and error handling:

- **Workflow error handling**
  - Database session failure
  - Pipeline timeout
  - Partial pipeline failure
  - Event send failure doesn't fail job

- **Edge cases**
  - Empty configuration
  - Very large configuration (10,000 files)
  - Empty callback topic
  - None result summary

- **Concurrency and race conditions**
  - Concurrent status updates
  - Job already running (duplicate workflow start)

### 6. SDK Integration Tests

Tests for workflow-core-sdk integration:

- **Unit tests** (`workflow-core-sdk/tests/steps/test_ingestion_step_unit.py`)
  - Job creation HTTP call
  - Status check HTTP call
  - Callback topic format
  - Idempotent behavior
  - Error handling

- **Integration tests** (`workflow-core-sdk/tests/integration/test_ingestion_workflow.py`)
  - Complete workflow with ingestion step
  - Two-phase execution (create → wait → complete)
  - DBOS event handling
  - Idempotency verification

## Running Tests

### Run all ingestion service tests:
```bash
cd python_apps/ingestion-service
pytest
```

### Run specific test categories:
```bash
# API tests only
pytest tests/test_api.py -v

# Workflow tests only
pytest tests/test_workflows.py -v

# Model tests only
pytest tests/test_models.py -v

# E2E tests only
pytest tests/test_e2e.py -v

# Error scenario tests only
pytest tests/test_error_scenarios.py -v
```

### Run SDK integration tests:
```bash
cd python_packages/workflow-core-sdk
pytest tests/steps/test_ingestion_step_unit.py -v
pytest tests/integration/test_ingestion_workflow.py -v
```

### Run with coverage:
```bash
pytest --cov=ingestion_service --cov-report=html
```

## Test Coverage

The test suite covers:

- ✅ All API endpoints
- ✅ DBOS workflow execution
- ✅ Data model validation
- ✅ Status transitions
- ✅ Error handling
- ✅ Edge cases
- ✅ Concurrency scenarios
- ✅ Idempotency
- ✅ SDK integration
- ✅ Event dispatch
- ✅ HTTP client interactions

## Mocking Strategy

Tests use mocking to avoid external dependencies:

- **Database**: Mocked with `MagicMock` for session operations
- **DBOS**: Mocked workflow start and event sending
- **HTTP Client**: Mocked `httpx.AsyncClient` for service calls
- **Pipeline Execution**: Mocked `execute_ingestion_pipeline` function

## Future Test Additions

Consider adding:

- Performance tests for large-scale ingestion
- Load tests for concurrent job handling
- Integration tests with real DBOS instance
- Integration tests with real elevaite_ingestion pipeline
- Chaos engineering tests (service failures, network issues)

