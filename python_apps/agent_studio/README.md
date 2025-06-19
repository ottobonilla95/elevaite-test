# Agent Studio

Agent Studio is a platform for creating, managing, and deploying AI agents with
different capabilities.

## System Initialization

Before using the system, you need to initialize the database with default
prompts, tools, and agents. This can be done in two ways:

### Option 1: Via API Endpoint (Recommended)

Start the Agent Studio server and call the initialization endpoint:

```bash
# Start the server
cd agent-studio
python main.py

# In another terminal, initialize the system
python scripts/initialize_system.py
```

Or make a direct API call:

```bash
curl -X POST http://localhost:8000/admin/initialize
```

### Option 2: Via Script

```bash
cd agent-studio
python scripts/initialize_system.py --host localhost --port 8000
```

### What Gets Initialized

The initialization process sets up:

1. **Prompts** - System prompts for different agent types (required for agents)
2. **Tool Categories** - Organized categories for tools (Search & Retrieval, Web
   & API, etc.)
3. **Tools** - Local tools from the existing tool_store (web_search,
   query_retriever2, etc.)
4. **Agents** - Pre-configured agents with deployment codes

### Individual Component Initialization

You can also initialize components separately via the demo endpoints:

```bash
# Initialize only prompts
curl -X POST http://localhost:8000/demo/initialize/prompts

# Initialize only tools
curl -X POST http://localhost:8000/demo/initialize/tools

# Initialize only agents (requires prompts to exist first)
curl -X POST http://localhost:8000/demo/initialize/agents

# Initialize everything
curl -X POST http://localhost:8000/demo/initialize/complete
```

### Available Agents and Deployment Codes

The following agents are available for deployment:

| Agent     | Deployment Code | Description                                     |
| --------- | --------------- | ----------------------------------------------- |
| WebAgent  | `w`             | Agent for web search and information retrieval  |
| DataAgent | `d`             | Agent for database queries and data analysis    |
| APIAgent  | `a`             | Agent for making API calls to external services |
