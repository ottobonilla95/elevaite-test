# Multi-Trigger Workflow Restructuring

**Branch:** `feature/multi-trigger-workflows`  
**Key Changes:** 3 commits covering ~2,500 lines removed, ~1,500 lines added

## Overview

This restructuring introduces **multi-trigger workflow capabilities** through three major changes:

| Commit | Summary |
|--------|---------|
| `8eb648ac` | Add input, merge, and output node types |
| `34166057` | Consolidate SDK re-exports (~2,300 LOC removed) |
| `5520b38c` | Add typed schemas and consolidate streaming |

---

## New Node Types

Three new step types enable workflows with multiple entry points and data convergence.

### Input Node (`input_step`)

**Purpose:** Data entry point for workflows — receives data without execution logic.

| Property | Description |
|----------|-------------|
| `kind` | `webhook`, `schedule`, `gmail`, `slack`, `chat`, `manual`, `form` |
| `schedule` | Optional cron/interval configuration |
| `schema` | Optional JSON schema for input validation |

**Behavior:**
- Completes when data is provided (via trigger or manual)
- Must have no dependencies (entry point)
- Data passed via `step_io_data[step_id]` or `trigger_raw`

**Output:**
```json
{"kind": "webhook", "step_id": "input_1", "data": {...}, "source": "direct"}
```

### Merge Node (`merge_step`)

**Purpose:** Combines outputs from multiple inputs with OR/AND logic.

| Mode | Behavior |
|------|----------|
| `first_available` | Completes when ANY dependency completes (OR logic) |
| `wait_all` | Waits for ALL dependencies to complete (AND logic) |

| Combine Mode | Output Format |
|--------------|---------------|
| `object` | `{step_id: output, ...}` |
| `array` | `[output1, output2, ...]` |
| `first` | First completed output only |

**Constraints:** Must have 2+ dependencies.

### Output Node (`output_step`)

**Purpose:** Pass-through endpoint for displaying workflow output on canvas.

| Property | Description |
|----------|-------------|
| `label` | Display label for UI |
| `format` | Format hint: `json`, `text`, `markdown`, `auto` |

**Behavior:** Passes input data through unchanged — marks visual endpoints.

---

## Typed Schema System

Replaced dict-based configuration with Pydantic models.

### Core Types

| Type | Purpose |
|------|---------|
| `WorkflowConfig` | Root workflow configuration |
| `StepBase` | Base step with execution control fields |
| `StepConfig` | Union of `TriggerStepConfig`, `InputStepConfig`, `MergeStepConfig`, `StepBase` |

### StepBase Execution Control Fields (New)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `critical` | `bool` | `True` | If True, step failure fails entire workflow |
| `timeout_seconds` | `int?` | `None` | Maximum execution time |
| `max_retries` | `int` | `3` | Maximum retry attempts |
| `retry_strategy` | `str` | `exponential_backoff` | `none`, `fixed_delay`, `linear_backoff` |
| `retry_delay_seconds` | `float` | `1.0` | Initial retry delay |
| `max_retry_delay_seconds` | `float` | `60.0` | Maximum retry delay |
| `conditions` | `str\|Dict\|List?` | `None` | Conditional execution rules |

---

## ExecutionContext Changes

The `ExecutionContext` now:
- Accepts `WorkflowConfig` (typed) or `Dict` (auto-converted)
- Uses typed `StepBase` list instead of raw dicts
- Auto-generates unique `step_id` values if missing
- Tracks step metadata (`step_type`, `duration_ms`) in results

### Step ID Normalization

| Condition | Generated ID |
|-----------|--------------|
| Trigger step | `trigger` |
| Named step | Slugified name (e.g., "My Agent" → `my_agent`) |
| Fallback | `{step_type}_{index}` |
| Conflicts | Numeric suffix (`_2`, `_3`, ...) |

---

## SDK Consolidation

**Removed ~2,300 lines** of redundant re-export wrappers from `workflow-engine-poc`:

| Deleted File | Was Re-exporting |
|--------------|------------------|
| `dbos_impl/adapter.py` | `workflow_core_sdk.dbos_impl.adapter` |
| `dbos_impl/runtime.py` | `workflow_core_sdk.dbos_impl.runtime` |
| `dbos_impl/steps.py` | `workflow_core_sdk.dbos_impl.steps` |
| `dbos_impl/workflows.py` | `workflow_core_sdk.dbos_impl.workflows` |
| `monitoring.py` | `workflow_core_sdk.monitoring` |
| `decorators.py` | `workflow_core_sdk.decorators` |

**After:** All imports use `workflow_core_sdk` directly.

---

## Streaming Consolidation

- Single `stream_manager` singleton across all modules
- Reduced verbose debug logging
- Events include `step_type` and `duration_ms` for observability
- `output_data` included in step events for UI rendering

---

## Data Flow Architecture

```
┌─────────────┐     ┌─────────────┐
│  input_1    │     │  input_2    │   ← Multiple entry points
│  (webhook)  │     │  (schedule) │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └─────────┬─────────┘
                 ▼
         ┌───────────────┐
         │    merge      │   ← OR: first_available, AND: wait_all
         └───────┬───────┘
                 ▼
         ┌───────────────┐
         │    agent      │   ← Processing step
         └───────┬───────┘
                 ▼
         ┌───────────────┐
         │    output     │   ← Visual endpoint
         └───────────────┘
```

---

## File Locations

| Component | Path |
|-----------|------|
| Workflow schemas | `workflow_core_sdk/schemas/workflows.py` |
| Input step | `workflow_core_sdk/steps/input_steps.py` |
| Merge step | `workflow_core_sdk/steps/merge_steps.py` |
| Output step | `workflow_core_sdk/steps/output_steps.py` |
| Step registry | `workflow_core_sdk/step_registry.py` |
| ExecutionContext | `workflow_core_sdk/execution_context.py` |

