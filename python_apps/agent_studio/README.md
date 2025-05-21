# Agent Studio

Agent Studio is a platform for creating, managing, and deploying AI agents with different capabilities.

### Initializing Pre-Configured (prevoiously hard-coded) Agents

Before using the dynamic deployment system, you can initialize a set of pre-configured (prevoiously hard-coded) agents in the database. This step is useful for setting up a baseline set of agents with predefined capabilities:

```bash
cd agent-studio
python3 scripts/initialize_db.py
```

This script:

- Creates default prompts in the database
- Creates default agents with deployment codes
- Makes agents available for deployment

#### Script Options

The initialization script supports the following options:

```bash
python3 scripts/initialize_db.py --help
```

- `--server-url [url]`: URL of the agent_studio server (default: http://localhost:8000)

### Available Agents and Deployment Codes

The following agents are available for deployment:

| Agent     | Deployment Code | Description                                     |
| --------- | --------------- | ----------------------------------------------- |
| WebAgent  | `w`             | Agent for web search and information retrieval  |
| DataAgent | `d`             | Agent for database queries and data analysis    |
| APIAgent  | `a`             | Agent for making API calls to external services |
