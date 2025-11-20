# Elevaite Ingestion Service & DBOS Integration Plan

## 1. Goals and Constraints

- Extract elevaite-ingestion capabilities into a dedicated ingestion service.
- Use DBOS for durable, parallel execution of ingestion jobs.
- Expose a simple HTTP (REST) control plane for creating and inspecting jobs.
- Integrate cleanly with the existing workflow engine without tight HTTP polling.
- Avoid showing user-visible `WAITING` for ingestion; workflows should appear "running/ingesting" instead of "paused".

## 2. High-Level Architecture

### 2.1 Components

- **Ingestion Service**
  - FastAPI (or similar) app with a small REST API.
  - Uses DBOS workflows/steps to run ingestion jobs.
  - Calls into the existing `elevaite_ingestion` package using its native config model.

- **Workflow Engine (Agent Studio / workflow-core-sdk)**
  - Gains a new **ingestion step type** which calls the ingestion service.
  - Uses DBOS event topics to wait for ingestion completion **without** exposing `WAITING` to the user.

### 2.2 Execution Flow (Happy Path)

1. A workflow contains an **ingestion step** with an `ingestion_config` payload.
2. When that step executes for the first time, it:
   - Computes a **DBOS callback topic** derived from `(execution_id, step_id)` and a custom suffix, e.g. `ingestion_done`.
   - Calls `POST /ingestion/jobs` on the ingestion service, passing the ingestion config and callback topic.
   - Returns a step result with `status="ingesting"` and `success=False` so the engine knows to block but *not* mark the workflow as `WAITING`.
3. The DBOS workflow engine detects `status="ingesting"`, keeps the execution in a running state, and blocks on `DBOS.recv_async(topic=callback_topic, ...)`.
4. The ingestion service runs the job via a DBOS workflow. When finished, it sends an event on the callback topic.
5. The blocked DBOS workflow receives the event, re-runs the ingestion step, which now returns `success=True`, and the workflow continues to the next step.

## 3. Ingestion Service Design

### 3.1 Data Model

- **JobStatus enum**: `PENDING`, `RUNNING`, `SUCCEEDED`, `FAILED`.
- **IngestionJob** table/entity (minimal):
  - `id`: UUID/ULID primary key.
  - `config`: JSON (validated by the elevaite_ingestion config model).
  - `status`: JobStatus.
  - `error_message`: optional text.
  - `created_at`, `updated_at` timestamps.
  - `callback_topic`: string (DBOS topic to notify when complete).
  - Optional: `tenant_id` / `organization_id`, `job_type` (e.g. `BULK_DATASET`, `ADHOC_FILE`).

### 3.2 REST API

**POST /ingestion/jobs**

- Request body (conceptual):
  - `config`: JSON that conforms to the `elevaite_ingestion` config schema.
  - `metadata`:
    - `tenant_id` / `organization_id`.
    - `execution_id`, `step_id` (optional but recommended for workflows).
    - `callback_topic`: DBOS topic string where completion events should be sent.
    - Optional correlation IDs.

- Behavior:
  1. Validate `config` against the ingestion config model.
  2. Create an `IngestionJob` with `status=PENDING` and store `callback_topic`.
  3. Start a DBOS ingestion workflow (see 3.3) with `job_id`.
  4. Return `{ job_id, status: "PENDING" }`.

**GET /ingestion/jobs/{job_id}**

- Returns job status and summary (`status`, `error_message`, optional metrics).
- Intended for debugging/UIs, **not** for tight polling by the workflow engine.

### 3.3 DBOS Ingestion Workflow

- `@DBOS.workflow()` entrypoint, e.g. `run_ingestion_job(job_id: str) -> None`.

Workflow steps (conceptual):

1. Load the `IngestionJob` by `job_id` and set `status=RUNNING`.
2. Deserialize the stored `config` into the native `IngestionConfig` type.
3. Invoke the `elevaite_ingestion` pipeline for that config.
4. On success:
   - Set `status=SUCCEEDED` and store any result summary.
   - If `callback_topic` is set, send an event to that topic with `{ job_id, status: "SUCCEEDED", summary }`.
5. On failure:
   - Set `status=FAILED` and store `error_message`.
   - Optionally send an event with `{ job_id, status: "FAILED", error_message }`.

The ingestion service can either:

- Use DBOS directly to send events, or
- Call back into the workflow engine via an internal HTTP endpoint which then publishes the DBOS event.

## 4. Workflow Engine Integration

### 4.1 New Ingestion Step Type

- Add a new `step_type` / `node_type` (e.g. `"ingestion"` or `"elevaite_ingestion"`).
- Step config should include:
  - `ingestion_config`: JSON payload matching the ingestion package config, or a reference to such a config.
  - Any engine-specific metadata needed for mapping triggers/outputs.

### 4.2 Ingestion Step Executor Logic

The ingestion step implementation should be **idempotent** and support two phases:

1. **First Execution (job creation)**

   - Build `callback_topic` using the existing helper, but with a dedicated suffix, e.g. `"ingestion_done"`:
     - `topic = make_decision_topic(execution_id, step_id, suffix="ingestion_done")`.
   - Call `POST /ingestion/jobs` with the ingestion config and metadata (`execution_id`, `step_id`, `callback_topic`, tenant info).
   - Persist `job_id` and `callback_topic` in the step's `output_data` so they are available on re-entry.
   - Return a step result:

     - `success=False` (so the engine knows not to advance),
     - `status="ingesting"`,
     - `output_data` containing `ingestion_job_id` and `callback_topic`.

2. **Second Execution (after callback event)**

   - Triggered when the DBOS workflow receives the ingestion completion event on `callback_topic`.
   - The ingestion step re-runs; it can:
     - Read `ingestion_job_id` from the prior `output_data`,
     - Optionally confirm job status via `GET /ingestion/jobs/{job_id}`.
   - Return a final result with `success=True`, `status="completed"`, and any useful output data (e.g. job summary, index IDs).

### 4.3 DBOS Workflow Behaviour ("ingesting" status)

Within `dbos_execute_workflow_durable` (in `workflow_core_sdk/dbos_impl/workflows.py`):

- Currently, when `res.get("status") == "waiting"`, the engine:
  - Emits events with `status="waiting"`.
  - Persists the execution as `WAITING` in the DB.
  - Blocks via `DBOS.recv_async(...)` on a `user_msg` topic.

- For ingestion, add a **separate branch** for `status="ingesting"`:
  - Do **not** mark the execution as `WAITING` in the DB.
  - Optionally emit a **step-level** event with `step_status="ingesting"` so the UI can show that the step is in an ingestion phase.
  - Determine the `callback_topic` (either from `output_data` or by recomputing it).
  - Block on `DBOS.recv_async(topic=callback_topic, timeout_seconds=...)`.
  - Once an event is received, loop and re-run the ingestion step. This time it should return `success=True`.

This preserves DBOS's durable blocking semantics *without* exposing `WAITING` to the user during ingestion.

## 5. Event Callback Strategy

There are two primary options for delivering ingestion completion events back to the workflow engine:

### Option A: HTTP Callback + Engine Publishes DBOS Event

- Ingestion workflow, on completion, calls:
  - `POST /internal/ingestion-callback` on the workflow engine.
- The engine's internal handler:
  - Validates the request (shared secret / service auth).
  - Builds `callback_topic` using `execution_id`, `step_id`, and the `ingestion_done` suffix.
  - Uses DBOS to send an event on that topic.

Pros:
- Ingestion microservice stays DBOS-agnostic.
- Only the workflow engine owns DBOS integration.

### Option B: Direct DBOS Event from Ingestion Service

- Ingestion service is DBOS-aware and configured with the same backend.
- On completion, `run_ingestion_job` calls:
  - `DBOS.send_async(topic=callback_topic, payload=event_payload)`.

Pros:
- Fewer moving pieces (no extra HTTP hop back into the engine).
- Simpler runtime behavior.

Trade-off:
- Tighter coupling between ingestion and DBOS.

## 6. Implementation Task List

### 6.1 Ingestion Service

- [ ] Define `JobStatus` enum and `IngestionJob` data model (DB schema/entity).
- [ ] Expose `POST /ingestion/jobs` endpoint that validates config, creates jobs, and starts a DBOS ingestion workflow.
- [ ] Expose `GET /ingestion/jobs/{job_id}` for status inspection and debugging.
- [ ] Implement `run_ingestion_job(job_id: str)` DBOS workflow that executes `elevaite_ingestion` and updates job status.
- [ ] Implement completion event dispatch (Option A: HTTP callback, or Option B: direct DBOS event).

### 6.2 Workflow Engine Integration

- [ ] Add an ingestion step type (`step_type` / `node_type`) and config schema supporting `ingestion_config`.
- [ ] Implement the ingestion step executor with two-phase behavior (job creation vs. completion).
- [ ] Update `dbos_execute_workflow_durable` to handle `status="ingesting"` by blocking on a callback topic (without marking execution as `WAITING`).
- [ ] Emit appropriate step-level events for `step_status="ingesting"` to support UI.

### 6.3 Wiring, Configuration, and Tests

- [ ] Add configuration for `INGESTION_SERVICE_URL` (and callback auth if using HTTP callbacks).
- [ ] Add unit tests for the ingestion step executor (first-run and second-run behavior).
- [ ] Add tests for the DBOS workflow behavior when a step returns `status="ingesting"`.
- [ ] Add end-to-end tests that exercise a workflow with an ingestion step and verify that:
  - The workflow remains in a running/ingesting state (no user-visible `WAITING`).
  - The ingestion job completes and triggers workflow continuation.

