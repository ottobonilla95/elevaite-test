# Granular Actions Reference

This document lists all granular actions available in the Workflow Engine API for fine-grained permission control.

## Overview

All endpoints now use specific action names instead of generic `view_project` and `edit_project` actions. This allows administrators to configure role permissions at a granular level using the Auth API's dynamic policy management.

## Actions by Resource Type

### Workflows (`/api/workflows`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_workflow` | GET | `/` | List all workflows |
| `view_workflow` | GET | `/{workflow_id}` | Get workflow by ID |
| `view_workflow` | GET | `/{workflow_id}/stream` | Stream workflow execution |
| `view_workflow` | POST | `/validate` | Validate workflow configuration |
| `create_workflow` | POST | `/` | Create new workflow |
| `delete_workflow` | DELETE | `/{workflow_id}` | Delete workflow |
| `execute_workflow` | POST | `/{workflow_id}/execute` | Execute workflow (default backend) |
| `execute_workflow` | POST | `/{workflow_id}/execute/{backend}` | Execute workflow (specific backend) |

### Agents (`/api/agents`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_agent` | GET | `/` | List all agents |
| `view_agent` | GET | `/{agent_id}` | Get agent by ID |
| `view_agent` | GET | `/{agent_id}/tools` | List agent's tools |
| `create_agent` | POST | `/` | Create new agent |
| `edit_agent` | PATCH | `/{agent_id}` | Update agent |
| `edit_agent` | POST | `/{agent_id}/tools` | Attach tool to agent |
| `edit_agent` | PATCH | `/{agent_id}/tools/{binding_id}` | Update tool binding |
| `edit_agent` | DELETE | `/{agent_id}/tools/{binding_id}` | Detach tool from agent |
| `delete_agent` | DELETE | `/{agent_id}` | Delete agent |

### Prompts (`/api/prompts`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_prompt` | GET | `/` | List all prompts |
| `view_prompt` | GET | `/{prompt_id}` | Get prompt by ID |
| `create_prompt` | POST | `/` | Create new prompt |
| `edit_prompt` | PATCH | `/{prompt_id}` | Update prompt |
| `delete_prompt` | DELETE | `/{prompt_id}` | Delete prompt |

### Tools (`/api/tools`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_tool` | GET | `/` | List all tools (unified) |
| `view_tool` | GET | `/{tool_name}` | Get tool by name |
| `view_tool` | GET | `/db` | List database tools |
| `view_tool` | GET | `/db/{tool_id}` | Get database tool by ID |
| `create_tool` | POST | `/db` | Create new tool in database |
| `edit_tool` | PATCH | `/db/{tool_id}` | Update database tool |
| `edit_tool` | PATCH | `/{tool_name}` | Update tool (stub) |
| `delete_tool` | DELETE | `/db/{tool_id}` | Delete database tool |
| `delete_tool` | DELETE | `/{tool_name}` | Delete tool (stub) |
| `sync_tools` | POST | `/sync` | Sync tools from source to database |

### Tool Categories (`/api/tools/categories`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_tool_category` | GET | `/categories` | List all categories |
| `view_tool_category` | GET | `/categories/{category_id}` | Get category by ID |
| `create_tool_category` | POST | `/categories` | Create new category |
| `edit_tool_category` | PATCH | `/categories/{category_id}` | Update category |
| `delete_tool_category` | DELETE | `/categories/{category_id}` | Delete category |

### MCP Servers (`/api/tools/mcp-servers`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_mcp_server` | GET | `/mcp-servers` | List all MCP servers |
| `view_mcp_server` | GET | `/mcp-servers/{server_id}` | Get MCP server by ID |
| `create_mcp_server` | POST | `/mcp-servers` | Create new MCP server |
| `edit_mcp_server` | PATCH | `/mcp-servers/{server_id}` | Update MCP server |
| `delete_mcp_server` | DELETE | `/mcp-servers/{server_id}` | Delete MCP server |

### Steps (`/api/steps`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_step` | GET | `/` | List all registered steps |
| `view_step` | GET | `/{step_type}` | Get step info by type |
| `register_step` | POST | `/register` | Register new step type |

### Approvals (`/api/approvals`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_approval` | GET | `/` | List all approval requests |
| `view_approval` | GET | `/{approval_id}` | Get approval request by ID |
| `approve_request` | POST | `/{approval_id}/approve` | Approve a request |
| `deny_request` | POST | `/{approval_id}/deny` | Deny a request |

### Messages (`/api/executions/{execution_id}/steps/{step_id}/messages`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_message` | GET | `/messages` | List messages for a step |
| `send_message` | POST | `/messages` | Send message to a step |

### Executions (`/api/executions`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `view_execution` | GET | `/` | List execution analytics |
| `view_execution` | GET | `/{execution_id}` | Get execution status |
| `view_execution` | GET | `/{execution_id}/results` | Get execution results |
| `view_execution` | GET | `/{execution_id}/stream` | Stream execution updates |

### Files (`/api/files`)

| Action | HTTP Method | Endpoint | Description |
|--------|-------------|----------|-------------|
| `upload_file` | POST | `/upload` | Upload file |

## Configuring Permissions

### Example: Allow Viewers to Execute Workflows

```bash
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "workflow_engine",
    "actions": {
      "viewer": ["view_workflow", "view_execution", "execute_workflow"],
      "editor": ["view_workflow", "view_execution", "execute_workflow", "create_workflow", "edit_workflow"],
      "admin": ["view_workflow", "view_execution", "execute_workflow", "create_workflow", "edit_workflow", "delete_workflow"]
    }
  }'
```

### Example: Restrict Tool Management to Admins Only

```bash
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "workflow_engine",
    "actions": {
      "viewer": ["view_tool"],
      "editor": ["view_tool"],
      "admin": ["view_tool", "create_tool", "edit_tool", "delete_tool", "sync_tools"]
    }
  }'
```

### Example: Allow Editors to Approve Requests

```bash
curl -X POST http://localhost:8004/api/policies/generate \
  -H "Authorization: Bearer $SUPERUSER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "workflow_engine",
    "actions": {
      "viewer": ["view_approval"],
      "editor": ["view_approval", "approve_request", "deny_request"],
      "admin": ["view_approval", "approve_request", "deny_request"]
    }
  }'
```

## Common Permission Patterns

### Read-Only Access
Grant only `view_*` actions:
- `view_workflow`
- `view_agent`
- `view_tool`
- `view_execution`
- `view_approval`
- `view_message`

### Standard Editor Access
Grant view + create + edit actions:
- All `view_*` actions
- All `create_*` actions
- All `edit_*` actions
- `execute_workflow`
- `send_message`

### Full Admin Access
Grant all actions including delete:
- All `view_*` actions
- All `create_*` actions
- All `edit_*` actions
- All `delete_*` actions
- All execution and approval actions

## Future: Scoped Permissions

In the future, project admins will be able to override these permissions for their specific projects:

```bash
# Project admin allows viewers to execute workflows in their project only
curl -X POST http://localhost:8004/api/policies/scoped \
  -H "Authorization: Bearer $PROJECT_ADMIN_TOKEN" \
  -d '{
    "resource_type": "project",
    "resource_id": "project-uuid",
    "role": "viewer",
    "service_name": "workflow_engine",
    "allowed_actions": ["view_workflow", "view_execution", "execute_workflow"]
  }'
```

See [DELEGATED_PERMISSIONS.md](./DELEGATED_PERMISSIONS.md) for more details on the planned scoped permissions feature.

