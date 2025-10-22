# Node Type Discrimination Migration Guide

## Overview

This document describes the migration from using `agent_type` for node discrimination to using a dedicated `node_type` field.

## Background

Previously, the system used `agent_type` for two purposes:
1. **Node discrimination**: Determining if a node is an agent or a tool (`agent_type == "tool"`)
2. **Agent classification**: Specifying the type of agent (router, web_search, data, etc.)

This dual purpose was confusing and made it difficult to add new agent types or tool types.

## New Structure

### Node Type Field

We now use `node_type` to discriminate between different node categories:

- **`node_type: "agent"`** - Agent execution step (uses LLM, has system prompt, can call tools)
- **`node_type: "tool"`** - Tool execution step (calls a specific tool function, no LLM)

### Agent Type Field

The `agent_type` field is now exclusively used for agent-specific information:

- **`agent_type: "router"`** - Router agent that directs queries to other agents
- **`agent_type: "web_search"`** - Web search agent
- **`agent_type: "data"`** - Data extraction agent
- **`agent_type: "troubleshooting"`** - Troubleshooting agent
- **`agent_type: "api"`** - API integration agent
- **`agent_type: "weather"`** - Weather information agent
- **`agent_type: "toshiba"`** - Toshiba-specific agent
- **`agent_type: "custom"`** - Custom agent type

## Migration Path

### Backend (Python)

#### Before
```python
# Old way: using agent_type for discrimination
if agent.get("agent_type") == "tool":
    # Create tool step
    pass
else:
    # Create agent step
    pass
```

#### After
```python
# New way: using node_type for discrimination
node_type = agent.get("node_type", "agent")  # Default to "agent" for backward compatibility

if node_type == "tool":
    # Create tool step
    pass
else:
    # Create agent step
    # agent_type still available for agent classification
    agent_type = agent.get("agent_type", "custom")
    pass
```

### Frontend (TypeScript/React)

#### Before
```typescript
// Old way: agent_type used for both purposes
interface AgentNode {
  agent_id: string;
  agent_type: "router" | "web_search" | "data" | "tool";  // Mixed purposes
  config: any;
}

// Checking if it's a tool
if (node.agent_type === "tool") {
  // Handle tool node
}
```

#### After
```typescript
// New way: separate fields
interface AgentNode {
  agent_id: string;
  node_type: "agent" | "tool";  // Node discrimination
  agent_type?: "router" | "web_search" | "data" | "troubleshooting" | "api" | "custom";  // Agent classification (only for agent nodes)
  config: any;
}

// Checking if it's a tool
if (node.node_type === "tool") {
  // Handle tool node
} else {
  // Handle agent node
  // Can access node.agent_type for agent-specific logic
}
```

### API Request Format

#### Creating a Workflow with Agent Nodes

```json
{
  "name": "My Workflow",
  "configuration": {
    "agents": [
      {
        "agent_id": "agent-1",
        "node_type": "agent",
        "agent_type": "router",
        "name": "Router Agent",
        "config": {
          "system_prompt": "You are a router agent..."
        }
      },
      {
        "agent_id": "agent-2",
        "node_type": "agent",
        "agent_type": "web_search",
        "name": "Web Search Agent",
        "config": {
          "system_prompt": "You are a web search agent..."
        }
      }
    ]
  }
}
```

#### Creating a Workflow with Tool Nodes

```json
{
  "name": "My Workflow",
  "configuration": {
    "agents": [
      {
        "agent_id": "tool-1",
        "node_type": "tool",
        "name": "Calculator Tool",
        "config": {
          "tool_name": "calculator",
          "param_mapping": {},
          "static_params": {}
        }
      }
    ]
  }
}
```

## Backward Compatibility

The system maintains backward compatibility by:

1. **Fallback logic**: If `node_type` is not present, the system checks if `agent_type == "tool"` to determine if it's a tool node
2. **Default behavior**: If neither field indicates a tool, the node is treated as an agent node

### Backward Compatible Code

```python
# This works with both old and new formats
node_type = agent.get("node_type") or ("tool" if agent.get("agent_type") == "tool" else "agent")

if node_type == "tool":
    # Handle tool
    pass
else:
    # Handle agent
    agent_type = agent.get("agent_type", "custom")
    pass
```

## Migration Checklist

### Backend
- [x] Update `request_adapter.py` to use `node_type` for discrimination
- [x] Add backward compatibility fallback logic
- [x] Update documentation
- [ ] Update database schemas to include `node_type` field (optional, for future)
- [ ] Update API documentation

### Frontend
- [ ] Update TypeScript interfaces to include `node_type`
- [ ] Update workflow builder to set `node_type` when creating nodes
- [ ] Update node rendering logic to use `node_type`
- [ ] Update node configuration panels
- [ ] Update validation logic

### Testing
- [x] Verify existing tests still pass with backward compatibility
- [ ] Add tests for new `node_type` field
- [ ] Test mixed workflows (old and new format)

## Benefits

1. **Clarity**: Clear separation between node category and agent classification
2. **Extensibility**: Easy to add new agent types without affecting node discrimination
3. **Type Safety**: Better TypeScript typing with discriminated unions
4. **Maintainability**: Easier to understand and maintain code

## Examples

### Example 1: Router Agent with Tool Nodes

```json
{
  "name": "Router with Tools",
  "configuration": {
    "agents": [
      {
        "agent_id": "router-1",
        "node_type": "agent",
        "agent_type": "router",
        "name": "Main Router",
        "config": {
          "system_prompt": "Route queries to appropriate tools"
        }
      },
      {
        "agent_id": "calc-tool",
        "node_type": "tool",
        "name": "Calculator",
        "config": {
          "tool_name": "calculator"
        }
      },
      {
        "agent_id": "search-tool",
        "node_type": "tool",
        "name": "Web Search",
        "config": {
          "tool_name": "web_search"
        }
      }
    ],
    "connections": [
      {
        "source_agent_id": "router-1",
        "target_agent_id": "calc-tool"
      },
      {
        "source_agent_id": "router-1",
        "target_agent_id": "search-tool"
      }
    ]
  }
}
```

### Example 2: Multi-Agent Workflow

```json
{
  "name": "Multi-Agent Workflow",
  "configuration": {
    "agents": [
      {
        "agent_id": "agent-1",
        "node_type": "agent",
        "agent_type": "router",
        "name": "Router"
      },
      {
        "agent_id": "agent-2",
        "node_type": "agent",
        "agent_type": "data",
        "name": "Data Extractor"
      },
      {
        "agent_id": "agent-3",
        "node_type": "agent",
        "agent_type": "web_search",
        "name": "Web Searcher"
      }
    ],
    "connections": [
      {
        "source_agent_id": "agent-1",
        "target_agent_id": "agent-2"
      },
      {
        "source_agent_id": "agent-1",
        "target_agent_id": "agent-3"
      }
    ]
  }
}
```

## Timeline

- **Phase 1** (Current): Backend support with backward compatibility
- **Phase 2**: Frontend migration to use `node_type`
- **Phase 3**: Database schema updates (optional)
- **Phase 4**: Deprecate old format (future)

## Questions?

For questions or issues, please contact the development team or create an issue in the repository.

