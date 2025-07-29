# Agent Analytics Test Script

This script comprehensively tests the Agent API and Analytics endpoints, demonstrating real-time monitoring of agent executions and retrieval of detailed analytics.

## Features

- **Agent Execution Testing**: Tests both regular and streaming agent execution
- **Parallel Analytics Monitoring**: Monitors analytics while executions are running
- **Comprehensive Reporting**: Retrieves and displays detailed execution and session analytics
- **OpenAI Schema Validation**: Tests the new OpenAI-compatible schema endpoint
- **Real-time Feedback**: Shows execution progress and analytics updates

## Installation

```bash
pip install -r test_requirements.txt
```

## Usage

### Quick Test
```bash
python test_agent_analytics.py quick
```

### Full Comprehensive Test
```bash
python test_agent_analytics.py
```

### Custom Options
```bash
# Test specific agent
python test_agent_analytics.py --agent-id "your-agent-id"

# Use streaming execution
python test_agent_analytics.py --streaming

# Custom API base URL
python test_agent_analytics.py --base-url "http://your-api-server:8000"
```

## What the Script Tests

### 1. Agent API Endpoints
- `GET /api/agents/` - List available agents
- `GET /api/agents/{agent_id}/schema` - Get OpenAI-compatible schema
- `POST /api/agents/{agent_id}/execute` - Execute agent
- `POST /api/agents/{agent_id}/execute/stream` - Execute agent with streaming

### 2. Analytics Endpoints
- `GET /api/analytics/summary` - Overall analytics summary
- `GET /api/analytics/agents/usage` - Agent usage statistics
- `GET /api/analytics/executions/{execution_id}` - Detailed execution info
- `GET /api/analytics/sessions/{session_id}` - Detailed session info

### 3. Real-time Monitoring
- Monitors analytics while executions are running
- Shows execution progress and timing
- Displays tool usage and success rates
- Tracks session activity

## Output Example

```
🧪 Starting Comprehensive Agent Analytics Test
============================================================
🤖 Using first available agent: CommandAgent (123e4567-...)

📋 Getting agent schema...
✅ Agent Schema Retrieved:
   Name: CommandAgent
   Model: gpt-4o-mini
   Tools: 5
   Temperature: 0.7

🔄 Test 1/3
----------------------------------------
🚀 Executing agent 123e4567-... with query: 'Hello, can you help me with a simple task?'
📊 Starting analytics monitoring for 10.0s...
📈 Current agent stats: 1 agents have recent activity
   - CommandAgent: 1 executions, 100.0% success rate
✅ Agent execution completed in 2.34s

📊 Retrieving analytics after execution...
📈 Analytics Summary: 1 agents with recent activity

============================================================
📋 EXECUTION DETAILS
============================================================
Execution ID: exec_789abc...
Agent: CommandAgent (123e4567-...)
Status: success
Query: Hello, can you help me with a simple task?
Start Time: 2024-01-15T10:30:00Z
End Time: 2024-01-15T10:30:02Z
Duration: 2340ms
Tool Count: 2
Retry Count: 0
API Calls: 1
Tokens Used: 150
Session ID: test_session_1705312200

🔧 Tools Called:
   - web_search: {"query": "help simple task"}
   - print_to_console: {"message": "Task completed"}

💬 Response: I'd be happy to help you with a simple task! What would you like assistance with?
```

## Key Features Demonstrated

1. **Parallel Execution**: Analytics monitoring runs concurrently with agent execution
2. **Comprehensive Tracking**: Every execution is tracked with detailed metrics
3. **Real-time Updates**: Shows analytics updates as they happen
4. **Error Handling**: Gracefully handles API errors and missing data
5. **Session Correlation**: Links multiple executions within a session
6. **Tool Usage Tracking**: Shows which tools were called and their performance

## Troubleshooting

- Ensure the Agent Studio API is running on the specified base URL
- Check that agents are available and properly configured
- Verify analytics service is enabled and recording metrics
- Allow a few seconds for analytics to be recorded after execution

## Integration Testing

This script is perfect for:
- Validating API functionality after deployments
- Performance testing and monitoring
- Debugging execution issues
- Demonstrating analytics capabilities
- Load testing with multiple concurrent executions
