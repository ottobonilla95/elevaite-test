# Workflow Core SDK - Dependency Architecture

## Overview

The workflow-core-sdk is designed as a **pure library** with minimal required dependencies. Heavy workspace dependencies (llm-gateway, elevaite-ingestion, db-core, elevaite-logger) are **optional** and imported conditionally.

## Design Principles

### 1. SDK is a Pure Library
- No workspace dependencies in required dependencies
- All workspace packages are optional imports with graceful fallbacks
- Consuming applications declare their own dependencies

### 2. Optional Import Pattern
All workspace dependencies use try/except import pattern:

```python
try:
    from llm_gateway.services import TextGenerationService
    LLM_GATEWAY_AVAILABLE = True
except ImportError:
    LLM_GATEWAY_AVAILABLE = False
```

### 3. Consuming Applications Own Their Dependencies
Applications that use the SDK must explicitly declare which features they need:

```toml
# Example: workflow-engine-poc/pyproject.toml
dependencies = [
    "workflow_core_sdk",
    "llm-gateway",           # For AI steps
    "elevaite-ingestion",    # For file processing steps
    "db-core",               # For database utilities
]
```

## Current Dependencies

### Required Dependencies
These are always installed with the SDK:

- **fastapi** - Web framework (used by services layer)
- **pydantic** - Data validation
- **sqlmodel** - Database ORM
- **sqlalchemy** - Database toolkit
- **asyncpg** - PostgreSQL async driver
- **aiohttp** - Async HTTP client
- **httpx** - Modern HTTP client (used by ingestion step)
- **python-multipart** - File upload support
- **croniter** - Cron expression parsing
- **openai** - OpenAI API client
- **requests** - HTTP library
- **typing-extensions** - Type hints backports
- **dbos** - Durable execution framework

### Optional Workspace Dependencies
These are imported conditionally and must be declared by consuming applications:

- **llm-gateway** - LLM integration (used in `ai_steps.py`)
- **elevaite-ingestion** - Document ingestion pipeline (used in `file_steps.py`)
- **db-core** - Database utilities (not currently used in SDK)
- **elevaite-logger** - Logging utilities (not currently used in SDK)

## Dependency Usage by Module

### Steps Module

#### `ai_steps.py`
- **Required**: sqlmodel, openai
- **Optional**: llm-gateway (for AgentStep)
- **Behavior**: Raises error if llm-gateway not available when creating AgentStep

#### `file_steps.py`
- **Required**: None (basic file operations)
- **Optional**: elevaite-ingestion (for parsing, chunking, embedding)
- **Behavior**: Gracefully degrades if elevaite-ingestion not available

#### `ingestion_steps.py`
- **Required**: httpx (for HTTP calls to ingestion service)
- **Optional**: None
- **Behavior**: Calls external ingestion service via HTTP

#### Other step modules
- Use only standard library and core dependencies

### Database Module (`db/`)
- **Required**: sqlmodel, sqlalchemy, asyncpg
- **Optional**: None

### Clients Module (`clients/`)
- **Required**: httpx, aiohttp
- **Optional**: None

### DBOS Module (`dbos_impl/`)
- **Required**: dbos
- **Optional**: None

## Migration Guide

### For SDK Developers
When adding new features to the SDK:

1. **Avoid adding workspace dependencies** to required dependencies
2. **Use optional imports** for workspace packages:
   ```python
   try:
       from workspace_package import Feature
       FEATURE_AVAILABLE = True
   except ImportError:
       FEATURE_AVAILABLE = False
   ```
3. **Provide graceful fallbacks** or clear error messages
4. **Document** which features require which optional dependencies

### For Application Developers
When using the SDK in your application:

1. **Install the SDK**: `uv add workflow_core_sdk`
2. **Add workspace dependencies** you need:
   ```bash
   # For AI features
   uv add llm-gateway
   
   # For ingestion features
   uv add elevaite-ingestion
   ```
3. **Check availability** before using optional features:
   ```python
   from workflow_core_sdk.steps.ai_steps import LLM_GATEWAY_AVAILABLE
   
   if not LLM_GATEWAY_AVAILABLE:
       raise RuntimeError("llm-gateway required for AI steps")
   ```

## Examples

### Minimal Installation (No AI, No Ingestion)
```toml
dependencies = [
    "workflow_core_sdk",
]
```
**Can use**: Basic steps, database models, DBOS workflows, HTTP clients

### With AI Features
```toml
dependencies = [
    "workflow_core_sdk",
    "llm-gateway",
]
```
**Can use**: Everything above + AgentStep, LLM integration

### With Ingestion Features
```toml
dependencies = [
    "workflow_core_sdk",
    "elevaite-ingestion",
]
```
**Can use**: Everything in minimal + File parsing, chunking, embedding

### Full Installation
```toml
dependencies = [
    "workflow_core_sdk",
    "llm-gateway",
    "elevaite-ingestion",
    "db-core",
    "elevaite-logger",
]
```
**Can use**: All features

## Benefits

1. **Smaller installations** - Applications only install what they need
2. **Faster builds** - Avoid heavy dependencies like NVIDIA/torch if not needed
3. **Clearer dependencies** - Each application owns its dependency tree
4. **Better separation** - SDK is truly a library, not an application
5. **Easier testing** - Can test SDK without all workspace dependencies

