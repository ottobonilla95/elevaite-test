# Asynchronous Workflow Execution with Streaming Responses

This document describes the new asynchronous workflow execution functionality that supports streaming responses for real-time interaction with deployed workflows.

## Overview

The async streaming functionality allows you to execute workflows and receive responses in real-time as they are generated, providing a better user experience for long-running operations and interactive conversations.

## Key Features

- **Asynchronous Execution**: Non-blocking workflow execution using Python's asyncio
- **Streaming Responses**: Real-time response chunks delivered via Server-Sent Events (SSE)
- **Structured Output**: JSON-formatted response chunks with metadata
- **Error Handling**: Graceful error handling with detailed error messages
- **Chat History Support**: Maintains conversation context for interactive workflows

## API Endpoints

### Streaming Execution Endpoint

```
POST /api/workflows/execute/stream
```

**Request Body:**
```json
{
  "deployment_name": "my_workflow_deployment",
  "query": "Your query here",
  "chat_history": [
    {"actor": "user", "content": "Previous message"},
    {"actor": "assistant", "content": "Previous response"}
  ],
  "runtime_overrides": {}
}
```

**Response:**
- Content-Type: `text/event-stream`
- Format: Server-Sent Events (SSE)

**Response Chunks:**
Each chunk is a JSON object with the following structure:

```json
{
  "type": "content|status",
  "data": "Response content",
  "status": "started|completed|error",
  "error": "Error message (if applicable)",
  "deployment_name": "deployment_name",
  "workflow_id": "workflow_uuid",
  "timestamp": "2024-01-01T12:00:00.000Z"
}
```

## Usage Examples

### Python Client Example

```python
import requests
import json

def stream_workflow_execution(deployment_name, query, chat_history=None):
    url = "http://localhost:8000/api/workflows/execute/stream"
    data = {
        "deployment_name": deployment_name,
        "query": query,
        "chat_history": chat_history or []
    }
    
    response = requests.post(url, json=data, stream=True)
    
    for line in response.iter_lines(decode_unicode=True):
        if line.startswith("data: "):
            chunk_data = line[6:]  # Remove "data: " prefix
            try:
                chunk = json.loads(chunk_data)
                print(f"Received: {chunk}")
                
                if chunk.get("status") == "completed":
                    print("Workflow execution completed")
                    break
                elif chunk.get("status") == "error":
                    print(f"Error: {chunk.get('error')}")
                    break
                    
            except json.JSONDecodeError:
                print(f"Raw data: {chunk_data}")

# Usage
stream_workflow_execution(
    deployment_name="my_deployment",
    query="What is the weather today?",
    chat_history=[
        {"actor": "user", "content": "Hello"},
        {"actor": "assistant", "content": "Hi! How can I help you?"}
    ]
)
```

### JavaScript/Frontend Example

```javascript
async function streamWorkflowExecution(deploymentName, query, chatHistory = []) {
    const response = await fetch('/api/workflows/execute/stream', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            deployment_name: deploymentName,
            query: query,
            chat_history: chatHistory
        })
    });

    const reader = response.body.getReader();
    const decoder = new TextDecoder();

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                const data = line.slice(6);
                try {
                    const parsed = JSON.parse(data);
                    console.log('Received chunk:', parsed);
                    
                    if (parsed.status === 'completed') {
                        console.log('Workflow completed');
                        return;
                    } else if (parsed.status === 'error') {
                        console.error('Workflow error:', parsed.error);
                        return;
                    }
                } catch (e) {
                    console.log('Raw data:', data);
                }
            }
        }
    }
}
```

## Implementation Details

### WorkflowService.execute_workflow_async()

The core async execution method in `services/workflow_service.py`:

- Validates deployment exists
- Sends initial status chunk
- Executes workflow with streaming support
- Handles both streaming and non-streaming execution modes
- Sends completion/error status
- Updates deployment statistics

### Streaming Response Format

All streaming responses follow the Server-Sent Events (SSE) format:
- Each line starts with `data: `
- JSON payload contains structured information
- Automatic reconnection support
- CORS headers for cross-origin requests

### Error Handling

- Network errors are handled gracefully
- Workflow execution errors are captured and streamed
- Database errors are logged and reported
- Client disconnections are detected

## Testing

Use the provided test script to verify functionality:

```bash
cd python_apps/agent_studio/agent-studio
python test_async_workflow.py
```

The test script will:
1. Create a test workflow
2. Deploy the workflow
3. Test regular execution
4. Test streaming execution
5. Verify response format and error handling

## Performance Considerations

- Small delay (0.01s) between chunks to prevent client overwhelming
- Structured JSON format for easy parsing
- Efficient memory usage with generators
- Database connection pooling for concurrent requests

## Future Enhancements

- WebSocket support for bidirectional communication
- Progress tracking for long-running workflows
- Workflow execution cancellation
- Real-time workflow status monitoring
- Batch execution with streaming results
