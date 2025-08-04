# Workflow Async Execution API with Tracing

This document describes the new async workflow execution system with detailed tracing capabilities for real-time monitoring.

## Overview

The workflow async execution system allows you to:
- Execute workflows asynchronously with immediate 202 response
- Track detailed step-by-step execution progress
- Monitor agent execution paths and branching decisions
- Get real-time updates for client-side progress displays

## API Endpoints

### 1. Execute Workflow Async

**POST** `/api/workflows/{workflow_id}/execute/async`

Execute a workflow asynchronously with detailed tracing.

**Request Body:**
```json
{
  "query": "Your query here",
  "session_id": "optional_session_id",
  "user_id": "optional_user_id",
  "chat_history": []
}
```

**Response (202 Accepted):**
```json
{
  "execution_id": "uuid-string",
  "status": "accepted",
  "type": "workflow",
  "estimated_completion_time": "2024-01-01T12:00:30Z",
  "status_url": "/api/executions/{execution_id}/status",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

### 2. Get Execution Status

**GET** `/api/executions/{execution_id}/status`

Get the current status of an async execution.

**Response:**
```json
{
  "execution_id": "uuid-string",
  "type": "workflow",
  "status": "running",
  "progress": 0.65,
  "current_step": "Executing DataAgent",
  "workflow_id": "workflow-uuid",
  "query": "Your original query",
  "created_at": "2024-01-01T12:00:00Z",
  "started_at": "2024-01-01T12:00:01Z",
  "workflow_trace": {
    "execution_id": "uuid-string",
    "workflow_id": "workflow-uuid",
    "current_step_index": 2,
    "total_steps": 4,
    "execution_path": ["CommandAgent", "DataAgent"],
    "branch_decisions": {
      "data_processing_choice": {
        "outcome": "use_fast_path",
        "timestamp": "2024-01-01T12:00:15Z"
      }
    }
  }
}
```

### 3. Get Workflow Steps (Real-time Monitoring)

**GET** `/api/executions/{execution_id}/steps`

Get detailed workflow steps for real-time monitoring.

**Response:**
```json
{
  "execution_id": "uuid-string",
  "current_step_index": 2,
  "total_steps": 4,
  "steps": [
    {
      "step_id": "init_step",
      "step_type": "data_processing",
      "agent_name": null,
      "tool_name": null,
      "status": "completed",
      "started_at": "2024-01-01T12:00:01Z",
      "completed_at": "2024-01-01T12:00:02Z",
      "duration_ms": 1000,
      "error": null,
      "metadata": {"description": "Initialize workflow"}
    },
    {
      "step_id": "agent_step_1",
      "step_type": "agent_execution",
      "agent_name": "CommandAgent",
      "tool_name": null,
      "status": "completed",
      "started_at": "2024-01-01T12:00:02Z",
      "completed_at": "2024-01-01T12:00:10Z",
      "duration_ms": 8000,
      "error": null,
      "metadata": {"agent_type": "orchestrator"}
    },
    {
      "step_id": "agent_step_2",
      "step_type": "agent_execution",
      "agent_name": "DataAgent",
      "tool_name": null,
      "status": "running",
      "started_at": "2024-01-01T12:00:10Z",
      "completed_at": null,
      "duration_ms": null,
      "error": null,
      "metadata": {"orchestrated": true}
    }
  ],
  "execution_path": ["CommandAgent", "DataAgent"],
  "branch_decisions": {
    "data_processing_choice": {
      "outcome": "use_fast_path",
      "timestamp": "2024-01-01T12:00:15Z"
    }
  }
}
```

### 4. Get Execution Progress (Optimized for Polling)

**GET** `/api/executions/{execution_id}/progress`

Get simplified progress information optimized for frequent frontend polling.

**Response:**
```json
{
  "execution_id": "uuid-string",
  "status": "running",
  "progress": 0.65,
  "current_step": "Executing DataAgent",
  "type": "workflow",
  "workflow_progress": {
    "current_step_index": 2,
    "total_steps": 4,
    "current_step_info": {
      "step_type": "agent_execution",
      "agent_name": "DataAgent",
      "status": "running"
    },
    "execution_path": ["CommandAgent", "DataAgent"]
  }
}
```

### 5. Get Full Execution Trace

**GET** `/api/executions/{execution_id}/trace`

Get the complete workflow trace data (for debugging/analysis).

**Response:**
```json
{
  "execution_id": "uuid-string",
  "workflow_id": "workflow-uuid",
  "current_step_index": 4,
  "total_steps": 4,
  "steps": [...],
  "execution_path": ["CommandAgent", "DataAgent"],
  "branch_decisions": {...}
}
```

## Step Types

- **`agent_execution`**: Execution of an individual agent
- **`tool_call`**: Individual tool/function call within an agent
- **`decision_point`**: Branching logic or conditional execution
- **`data_processing`**: Data transformation or system operations

## Step Status Values

- **`pending`**: Step is queued but not started
- **`running`**: Step is currently executing
- **`completed`**: Step completed successfully
- **`failed`**: Step failed with an error
- **`skipped`**: Step was skipped due to conditions

## Real-time Frontend Integration

For real-time progress display in your frontend:

1. Start workflow execution with POST `/api/workflows/{id}/execute/async`
2. Poll `/api/executions/{execution_id}/progress` every 1-2 seconds for basic progress
3. Poll `/api/executions/{execution_id}/steps` every 3-5 seconds for detailed step information
4. Stop polling when status is `completed`, `failed`, or `cancelled`

## Example Frontend Usage

```typescript
// Start workflow execution
const response = await fetch('/api/workflows/my-workflow-id/execute/async', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'Process my data' })
});

const { execution_id } = await response.json();

// Poll for progress
const pollProgress = async () => {
  const progressResponse = await fetch(`/api/executions/${execution_id}/progress`);
  const progress = await progressResponse.json();
  
  updateProgressBar(progress.progress);
  updateCurrentStep(progress.current_step);
  
  if (progress.workflow_progress) {
    updateStepIndicator(
      progress.workflow_progress.current_step_index,
      progress.workflow_progress.total_steps
    );
    updateExecutionPath(progress.workflow_progress.execution_path);
  }
  
  if (!['completed', 'failed', 'cancelled'].includes(progress.status)) {
    setTimeout(pollProgress, 2000); // Poll every 2 seconds
  }
};

pollProgress();
```

## Benefits

- **Real-time Visibility**: See exactly where your workflow is in execution
- **Debugging**: Detailed error information and execution paths
- **Performance Monitoring**: Step-by-step timing information
- **User Experience**: Rich progress indicators for long-running workflows
- **Scalability**: Non-blocking execution with efficient polling endpoints