# Unified Workflow Execution Engine PoC

A clean, agnostic workflow execution engine that supports conditional, sequential, and parallel execution patterns without the baggage of existing systems.

## Features

- **Agnostic Execution**: Doesn't care about workflow structure - executes the right function at the right step
- **RPC-like Step Registration**: Clients can register custom steps without redeployment
- **Multi-Provider LLM Integration**: Real LLM calls via llm-gateway supporting OpenAI, Gemini, Bedrock, and On-Prem models
- **Simplified Agent Execution**: Clean agent execution with graceful fallback to simulation
- **Database-backed Configuration**: All configurations stored in database
- **Multiple Execution Patterns**: Sequential, parallel, and conditional execution
- **Clean API**: RESTful endpoints for workflow execution and management

## Architecture

```
Workflow Engine (Agnostic)
├── Execution Context (workflow config, step I/O, analytics IDs)
├── Step Registry (RPC-like registration)
├── Execution Strategies (sequential, parallel, conditional)
└── Database Models (streamlined, version-agnostic)
```

## Quick Start

1. Install dependencies:

   ```bash
   uv sync
   ```

2. Run the server:

   ```bash
   uv run python main.py
   ```

3. Test the PoC:

   ```bash
   uv run python test_poc.py
   ```

4. Test with real LLM providers (optional):

   ```bash
   # Set API keys for your preferred provider
   export OPENAI_API_KEY="your-openai-key"
   # or
   export GOOGLE_API_KEY="your-google-key"

   # Run real LLM tests
   uv run python -m workflow_engine_poc.test_real_llm
   ```

5. Access the API documentation:
   ```
   http://localhost:8006/docs
   ```

## API Endpoints

- `POST /workflows/execute` - Execute a workflow
- `GET /executions/{execution_id}` - Get execution status
- `GET /executions/{execution_id}/results` - Get execution results
- `POST /steps/register` - Register a new step type
- `GET /steps` - List registered steps
- `POST /workflows/validate` - Validate workflow configuration

## Example Workflow

```json
{
  "name": "Simple Test Workflow",
  "execution_pattern": "sequential",
  "steps": [
    {
      "step_id": "input_data",
      "step_type": "data_input",
      "config": {
        "input_type": "static",
        "data": { "message": "Hello, World!" }
      }
    },
    {
      "step_id": "process_data",
      "step_type": "data_processing",
      "dependencies": ["input_data"],
      "input_mapping": {
        "input": "input_data.data"
      },
      "config": {
        "processing_type": "uppercase"
      }
    }
  ]
}
```

## LLM Provider Configuration

The workflow engine supports multiple LLM providers through the llm-gateway package:

### OpenAI

```bash
export OPENAI_API_KEY="your-openai-api-key"
```

### Google Gemini

```bash
export GOOGLE_API_KEY="your-google-api-key"
```

### AWS Bedrock

```bash
export AWS_ACCESS_KEY_ID="your-aws-access-key"
export AWS_SECRET_ACCESS_KEY="your-aws-secret-key"
export AWS_DEFAULT_REGION="us-east-1"
```

### Agent Configuration Examples

```python
# OpenAI Agent
{
    "agent_name": "OpenAI Analyzer",
    "model": "gpt-4o-mini",
    "provider_type": "openai_textgen",
    "system_prompt": "You are an expert analyst...",
    "temperature": 0.1,
    "max_tokens": 1000
}

# Gemini Agent
{
    "agent_name": "Gemini Analyzer",
    "model": "gemini-1.5-flash",
    "provider_type": "gemini_textgen",
    "system_prompt": "You are an expert analyst...",
    "temperature": 0.1,
    "max_tokens": 1000
}

# Bedrock Agent
{
    "agent_name": "Claude Analyzer",
    "model": "anthropic.claude-instant-v1",
    "provider_type": "bedrock_textgen",
    "system_prompt": "You are Claude, an AI assistant...",
    "temperature": 0.1,
    "max_tokens": 1000
}
```

If no providers are configured, the system gracefully falls back to simulation mode.

## Development

This is a proof of concept for a unified workflow execution engine. It demonstrates:

- Clean separation of concerns
- Agnostic workflow execution
- RPC-like extensibility
- Simplified agent integration
- Database-backed configuration

The goal is to replace complex workflow systems with a simple, extensible engine that focuses on core functionality.
