# Agent Communication Guide

## Overview

This guide explains how agents communicate using Redis Streams in the ElevAIte platform. It covers the architecture, implementation patterns, and provides real-world examples for developers.

## Architecture

### Communication Flow

```
Frontend → Backend API → Agent Manager → Redis Streams → Target Agent(s)
    ↓                                                           ↓
Response ← Backend API ← Agent Manager ← Redis Streams ← Agent Response
```

### Key Components

1. **Redis Streams**: Message transport layer
2. **Agent Manager**: Orchestrates agent communication
3. **Backend API**: Exposes communication endpoints
4. **Frontend**: Initiates agent interactions

## Communication Patterns

### 1. Direct Agent-to-Agent Communication

**Use Case**: One agent needs to request data or action from another agent.

**Implementation**: Backend-initiated, transparent to frontend.

```python
# Agent A requests data from Agent B
class DataAnalysisAgent(Agent):
    def analyze_data(self, data):
        # Request preprocessing from another agent
        preprocessed_data = self.request_reply(
            target_stream="agent:data_preprocessor",
            message={
                "type": "preprocess_request",
                "data": data,
                "format": "json",
                "timestamp": datetime.now().isoformat()
            },
            timeout=30
        )

        if preprocessed_data:
            return self.perform_analysis(preprocessed_data["result"])
        else:
            return {"error": "Preprocessing failed"}
```

### 2. Broadcast Communication

**Use Case**: Notify multiple agents about system events or updates.

**Implementation**: Backend publishes to a broadcast stream.

```python
# System broadcasts update to all agents
def broadcast_system_update(update_message):
    redis_manager.publish_message(
        "system:broadcast",
        {
            "type": "system_update",
            "message": update_message,
            "timestamp": datetime.now().isoformat(),
            "priority": 1
        }
    )

# Agents subscribe to broadcast stream
class Agent(AgentBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Subscribe to system broadcasts
        self.register_broadcast_handler()

    def register_broadcast_handler(self):
        redis_manager.consume_messages(
            "system:broadcast",
            self.handle_broadcast,
            group_name="system_listeners",
            consumer_name=f"agent_{self.agent_id}"
        )

    def handle_broadcast(self, message):
        data = message.get("data", {})
        if data.get("type") == "system_update":
            self.handle_system_update(data)
```

### 3. Task Queue Pattern

**Use Case**: Distribute work among multiple agent instances.

**Implementation**: Backend publishes tasks, agents consume from shared queue.

```python
# Backend publishes tasks
def submit_task_to_agents(task_data):
    return redis_manager.publish_message(
        "tasks:processing_queue",
        {
            "type": "process_task",
            "task_id": str(uuid.uuid4()),
            "data": task_data,
            "priority": task_data.get("priority", 0),
            "submitted_at": datetime.now().isoformat()
        }
    )

# Multiple agent instances consume from the same queue
class TaskProcessorAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # All instances share the same consumer group
        self.register_task_handler()

    def register_task_handler(self):
        redis_manager.consume_messages(
            "tasks:processing_queue",
            self.process_task,
            group_name="task_processors",  # Shared group for load balancing
            consumer_name=f"processor_{self.agent_id}"
        )

    def process_task(self, message):
        data = message.get("data", {})
        task_id = data.get("task_id")

        try:
            result = self.execute_task(data)

            # Publish result to results stream
            redis_manager.publish_message(
                "tasks:results",
                {
                    "task_id": task_id,
                    "result": result,
                    "processed_by": str(self.agent_id),
                    "completed_at": datetime.now().isoformat()
                }
            )

            return {"status": "completed", "task_id": task_id}

        except Exception as e:
            return {"status": "failed", "task_id": task_id, "error": str(e)}
```

## Real-World Implementation Examples

### Example 1: Multi-Agent Data Pipeline

**Scenario**: A user uploads a document that needs to be processed by multiple specialized agents.

**Agents Involved**:

- Document Parser Agent
- Content Analyzer Agent
- Summary Generator Agent
- Quality Checker Agent

**Implementation Flow**:

#### 1. Frontend Initiates Request

```javascript
// Frontend uploads document
const response = await fetch("/api/agents/process-document", {
  method: "POST",
  body: formData,
  headers: { "Content-Type": "multipart/form-data" },
});

const { pipeline_id } = await response.json();

// Poll for results
const pollResults = async () => {
  const result = await fetch(`/api/agents/pipeline/${pipeline_id}/status`);
  const data = await result.json();

  if (data.status === "completed") {
    displayResults(data.result);
  } else if (data.status === "processing") {
    setTimeout(pollResults, 2000); // Poll every 2 seconds
  }
};
```

#### 2. Backend Orchestrates Pipeline

```python
# Backend API endpoint
@app.post("/api/agents/process-document")
async def process_document(file: UploadFile):
    pipeline_id = str(uuid.uuid4())

    # Store file and create pipeline record
    file_path = await save_uploaded_file(file)

    # Initiate pipeline by sending to first agent
    redis_manager.publish_message(
        "agent:document_parser",
        {
            "type": "parse_document",
            "pipeline_id": pipeline_id,
            "file_path": file_path,
            "next_agents": ["content_analyzer", "summary_generator"],
            "final_callback": "pipeline_complete"
        }
    )

    return {"pipeline_id": pipeline_id, "status": "initiated"}

@app.get("/api/agents/pipeline/{pipeline_id}/status")
async def get_pipeline_status(pipeline_id: str):
    # Check pipeline status in database
    status = await get_pipeline_status_from_db(pipeline_id)
    return status
```

#### 3. Agent Implementation

```python
class DocumentParserAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_message_handler(self.handle_parse_request)

    def handle_parse_request(self, message):
        data = message.get("data", {})
        pipeline_id = data.get("pipeline_id")
        file_path = data.get("file_path")

        try:
            # Parse the document
            parsed_content = self.parse_document(file_path)

            # Send to next agents in pipeline
            for next_agent in data.get("next_agents", []):
                self.send_message(
                    f"agent:{next_agent}",
                    {
                        "type": "analyze_content",
                        "pipeline_id": pipeline_id,
                        "content": parsed_content,
                        "source_agent": "document_parser"
                    }
                )

            # Update pipeline status
            self.update_pipeline_status(pipeline_id, "parsing_complete")

            return {"status": "success", "pipeline_id": pipeline_id}

        except Exception as e:
            self.handle_pipeline_error(pipeline_id, "parsing_failed", str(e))
            return {"status": "error", "pipeline_id": pipeline_id}

class ContentAnalyzerAgent(Agent):
    def handle_analyze_content(self, message):
        data = message.get("data", {})
        pipeline_id = data.get("pipeline_id")
        content = data.get("content")

        # Perform content analysis
        analysis_result = self.analyze_content(content)

        # Check if this is the final step
        if self.is_pipeline_complete(pipeline_id):
            # Send final result
            self.send_message(
                "system:pipeline_results",
                {
                    "type": "pipeline_complete",
                    "pipeline_id": pipeline_id,
                    "final_result": self.compile_pipeline_results(pipeline_id)
                }
            )

        return {"status": "analysis_complete"}
```

### Example 2: Real-Time Collaboration

**Scenario**: Multiple agents collaborate on a complex task in real-time.

**Use Case**: Code review system where different agents check different aspects.

#### Frontend Implementation

```javascript
// Real-time code review interface
class CodeReviewInterface {
  constructor(reviewId) {
    this.reviewId = reviewId;
    this.eventSource = new EventSource(`/api/agents/review/${reviewId}/stream`);
    this.setupEventHandlers();
  }

  setupEventHandlers() {
    this.eventSource.onmessage = (event) => {
      const data = JSON.parse(event.data);
      this.handleAgentUpdate(data);
    };
  }

  handleAgentUpdate(data) {
    switch (data.type) {
      case "syntax_check_complete":
        this.updateSyntaxResults(data.result);
        break;
      case "security_scan_complete":
        this.updateSecurityResults(data.result);
        break;
      case "performance_analysis_complete":
        this.updatePerformanceResults(data.result);
        break;
      case "review_complete":
        this.showFinalResults(data.result);
        break;
    }
  }

  async submitCode(code) {
    const response = await fetch(`/api/agents/review/${this.reviewId}/submit`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code }),
    });

    return response.json();
  }
}
```

#### Backend Stream Handler

```python
@app.post("/api/agents/review/{review_id}/submit")
async def submit_code_for_review(review_id: str, request: CodeSubmission):
    # Initiate parallel agent processing
    agents = ["syntax_checker", "security_scanner", "performance_analyzer"]

    for agent_name in agents:
        redis_manager.publish_message(
            f"agent:{agent_name}",
            {
                "type": "review_code",
                "review_id": review_id,
                "code": request.code,
                "language": request.language,
                "callback_stream": f"review:{review_id}:results"
            }
        )

    return {"status": "review_initiated", "review_id": review_id}

@app.get("/api/agents/review/{review_id}/stream")
async def stream_review_results(review_id: str):
    async def event_generator():
        # Subscribe to review results stream
        consumer = RedisConsumer(f"review:{review_id}:results")

        async for message in consumer.listen():
            data = message.get("data", {})
            yield f"data: {json.dumps(data)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/plain")
```

## Implementation Responsibilities

### Frontend Developer

- **Initiates communication** through API calls
- **Handles real-time updates** via WebSockets/SSE
- **Manages UI state** based on agent responses
- **Does NOT** directly interact with Redis

### Backend Developer

- **Exposes API endpoints** for agent communication
- **Orchestrates agent workflows** and pipelines
- **Manages Redis message routing** and coordination
- **Handles authentication/authorization** for agent access
- **Implements real-time streaming** to frontend

### Agent Developer

- **Implements agent message handlers** for specific tasks
- **Defines agent communication protocols** and message formats
- **Handles agent-to-agent coordination** within workflows
- **Manages agent state** and error handling

## Best Practices

### Message Design

```python
# Standard message format
{
    "type": "action_name",           # Required: Action identifier
    "data": {...},                   # Required: Action payload
    "metadata": {
        "timestamp": "ISO-8601",     # When message was created
        "source_agent": "agent_id",  # Who sent the message
        "correlation_id": "uuid",    # For request-reply tracking
        "priority": 1,               # Message priority (0-10)
        "timeout": 30                # Response timeout in seconds
    }
}
```

### Error Handling

```python
# Standardized error responses
{
    "status": "error",
    "error_code": "PROCESSING_FAILED",
    "error_message": "Human readable error",
    "details": {...},               # Additional error context
    "retry_after": 5,               # Seconds before retry
    "correlation_id": "uuid"        # Original request ID
}
```

### Stream Naming Conventions

- **Agent streams**: `agent:{agent_name}` (e.g., `agent:document_parser`)
- **System streams**: `system:{purpose}` (e.g., `system:broadcast`)
- **Task queues**: `tasks:{queue_name}` (e.g., `tasks:processing_queue`)
- **Results**: `results:{context}` (e.g., `results:pipeline_123`)
- **Temporary**: `temp:{session_id}:{purpose}`

## Step-by-Step Implementation Process

### For Frontend Developers

#### 1. Initiate Agent Communication

```javascript
// Example: Document processing request
const processDocument = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("processing_type", "full_analysis");

  try {
    const response = await fetch("/api/agents/process-document", {
      method: "POST",
      body: formData,
    });

    const { task_id } = await response.json();
    return task_id;
  } catch (error) {
    console.error("Failed to initiate document processing:", error);
    throw error;
  }
};
```

#### 2. Handle Real-Time Updates

```javascript
// Set up real-time communication
const setupAgentUpdates = (taskId) => {
  const eventSource = new EventSource(`/api/agents/task/${taskId}/stream`);

  eventSource.onmessage = (event) => {
    const update = JSON.parse(event.data);
    handleAgentUpdate(update);
  };

  eventSource.onerror = (error) => {
    console.error("Agent communication error:", error);
    // Implement fallback polling
    startPolling(taskId);
  };

  return eventSource;
};

const handleAgentUpdate = (update) => {
  switch (update.type) {
    case "progress":
      updateProgressBar(update.progress);
      break;
    case "agent_result":
      displayAgentResult(update.agent_name, update.result);
      break;
    case "complete":
      showFinalResults(update.final_result);
      break;
    case "error":
      showError(update.error_message);
      break;
  }
};
```

### For Backend Developers

#### 1. Create API Endpoints

```python
from fastapi import FastAPI, UploadFile, BackgroundTasks
from fastapi.responses import StreamingResponse
import asyncio
import json

app = FastAPI()

@app.post("/api/agents/process-document")
async def process_document(file: UploadFile, background_tasks: BackgroundTasks):
    task_id = str(uuid.uuid4())

    # Save file
    file_path = await save_file(file, task_id)

    # Start agent processing in background
    background_tasks.add_task(initiate_agent_processing, task_id, file_path)

    return {"task_id": task_id, "status": "initiated"}

async def initiate_agent_processing(task_id: str, file_path: str):
    """Orchestrate multi-agent processing pipeline"""

    # Step 1: Document parsing
    redis_manager.publish_message(
        "agent:document_parser",
        {
            "type": "parse_document",
            "task_id": task_id,
            "file_path": file_path,
            "callback_stream": f"task:{task_id}:updates"
        }
    )

    # Step 2: Set up result aggregation
    await setup_result_aggregation(task_id)

@app.get("/api/agents/task/{task_id}/stream")
async def stream_task_updates(task_id: str):
    """Stream real-time updates to frontend"""

    async def event_generator():
        # Subscribe to task updates
        consumer = RedisStreamConsumer(f"task:{task_id}:updates")

        try:
            async for message in consumer.listen():
                data = message.get("data", {})
                yield f"data: {json.dumps(data)}\n\n"

                # End stream when task is complete
                if data.get("type") == "complete":
                    break

        except Exception as e:
            error_data = {"type": "error", "message": str(e)}
            yield f"data: {json.dumps(error_data)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/plain",
        headers={"Cache-Control": "no-cache"}
    )
```

#### 2. Implement Agent Coordination

```python
class AgentOrchestrator:
    def __init__(self):
        self.redis_manager = RedisManager()
        self.active_tasks = {}

    async def setup_result_aggregation(self, task_id: str):
        """Set up result collection for multi-agent task"""

        self.active_tasks[task_id] = {
            "status": "processing",
            "results": {},
            "expected_agents": ["document_parser", "content_analyzer", "summarizer"],
            "completed_agents": []
        }

        # Listen for agent results
        self.redis_manager.consume_messages(
            f"task:{task_id}:results",
            lambda msg: self.handle_agent_result(task_id, msg),
            group_name="orchestrator",
            consumer_name=f"orchestrator_{task_id}"
        )

    def handle_agent_result(self, task_id: str, message):
        """Handle individual agent results"""
        data = message.get("data", {})
        agent_name = data.get("agent_name")
        result = data.get("result")

        task_info = self.active_tasks.get(task_id)
        if not task_info:
            return

        # Store agent result
        task_info["results"][agent_name] = result
        task_info["completed_agents"].append(agent_name)

        # Send progress update to frontend
        self.send_progress_update(task_id, agent_name, result)

        # Check if all agents completed
        if len(task_info["completed_agents"]) >= len(task_info["expected_agents"]):
            self.finalize_task(task_id)

    def send_progress_update(self, task_id: str, agent_name: str, result):
        """Send progress update to frontend stream"""
        self.redis_manager.publish_message(
            f"task:{task_id}:updates",
            {
                "type": "agent_result",
                "agent_name": agent_name,
                "result": result,
                "timestamp": datetime.now().isoformat()
            }
        )

    def finalize_task(self, task_id: str):
        """Compile final results and notify frontend"""
        task_info = self.active_tasks[task_id]

        final_result = self.compile_results(task_info["results"])

        # Send completion notification
        self.redis_manager.publish_message(
            f"task:{task_id}:updates",
            {
                "type": "complete",
                "final_result": final_result,
                "timestamp": datetime.now().isoformat()
            }
        )

        # Cleanup
        del self.active_tasks[task_id]
        self.redis_manager.stop_consumer(f"task:{task_id}:results")
```

### For Agent Developers

#### 1. Implement Agent Message Handlers

```python
class DocumentParserAgent(Agent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_message_handler(self.handle_parse_request)

    def handle_parse_request(self, message):
        """Handle document parsing requests"""
        data = message.get("data", {})
        task_id = data.get("task_id")
        file_path = data.get("file_path")
        callback_stream = data.get("callback_stream")

        try:
            # Parse the document
            parsed_content = self.parse_document(file_path)

            # Send result to orchestrator
            self.send_message(
                f"task:{task_id}:results",
                {
                    "agent_name": "document_parser",
                    "result": {
                        "content": parsed_content,
                        "metadata": self.extract_metadata(file_path),
                        "status": "success"
                    }
                }
            )

            # Trigger next agent in pipeline
            self.send_message(
                "agent:content_analyzer",
                {
                    "type": "analyze_content",
                    "task_id": task_id,
                    "content": parsed_content,
                    "callback_stream": callback_stream
                }
            )

            return {"status": "completed", "task_id": task_id}

        except Exception as e:
            # Send error notification
            self.send_message(
                callback_stream,
                {
                    "type": "error",
                    "agent_name": "document_parser",
                    "error_message": str(e),
                    "task_id": task_id
                }
            )
            return {"status": "error", "error": str(e)}
```

#### 2. Implement Agent-to-Agent Communication

```python
class ContentAnalyzerAgent(Agent):
    def analyze_content_with_collaboration(self, content, task_id):
        """Analyze content with help from other agents"""

        # Request sentiment analysis from specialized agent
        sentiment_result = self.request_reply(
            "agent:sentiment_analyzer",
            {
                "type": "analyze_sentiment",
                "text": content,
                "task_id": task_id
            },
            timeout=30
        )

        # Request entity extraction from NER agent
        entities_result = self.request_reply(
            "agent:entity_extractor",
            {
                "type": "extract_entities",
                "text": content,
                "task_id": task_id
            },
            timeout=30
        )

        # Combine results
        analysis = {
            "sentiment": sentiment_result.get("sentiment") if sentiment_result else None,
            "entities": entities_result.get("entities") if entities_result else [],
            "content_summary": self.generate_summary(content),
            "analysis_timestamp": datetime.now().isoformat()
        }

        return analysis
```

## Quick Start Checklist

### Frontend Developer Checklist

- [ ] Create API calls to initiate agent communication
- [ ] Implement real-time update handling (WebSocket/SSE)
- [ ] Add progress indicators and status displays
- [ ] Handle error states and retry logic
- [ ] Test with mock agent responses

### Backend Developer Checklist

- [ ] Create API endpoints for agent communication
- [ ] Implement Redis message routing
- [ ] Set up real-time streaming to frontend
- [ ] Add authentication/authorization
- [ ] Implement error handling and logging
- [ ] Create agent orchestration logic

### Agent Developer Checklist

- [ ] Define agent message handlers
- [ ] Implement agent-to-agent communication
- [ ] Add error handling and recovery
- [ ] Create agent state management
- [ ] Write agent tests
- [ ] Document agent capabilities and message formats

This architecture provides scalable, reliable agent communication while maintaining clear separation of concerns between frontend, backend, and agent implementations.
