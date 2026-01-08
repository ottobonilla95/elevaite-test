# Tools Reference

Available tools that agents and workflows can invoke for LLM function calling.

## Overview

Tools are registered in the tool registry and exposed via:
- **API:** `GET /api/tools` - List all tools
- **API:** `GET /api/tools/{name}` - Get tool by name
- **API:** `GET /api/tools/schemas/openai` - Get OpenAI function calling schemas

Tools have three sources:
- **Local:** Built-in tools in the SDK
- **Database:** Custom tools registered via API
- **MCP:** Model Context Protocol servers (future)

---

## Tool Categories

| Category | Description |
|----------|-------------|
| Web | Web search and URL processing |
| Database | SQL, PostgreSQL, Redis operations |
| ServiceNow | ITSM and CSM integrations |
| Salesforce | CSM case management |
| File | File operations and info |
| Utility | Math, time, debugging |

---

## Web Tools

### `web_search`

Search the web using Google Custom Search and return AI-summarized results.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | The search query |
| `num` | integer | No | Number of results (default: 2) |

**Example:**
```json
{
  "name": "web_search",
  "arguments": {
    "query": "latest Python 3.12 features"
  }
}
```

### `url_to_markdown`

Convert a webpage URL to Markdown format.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `url` | string | Yes | The URL to convert |

---

## Database Tools

### `postgres_query`

Perform PostgreSQL database operations.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query_type` | string | Yes | `select`, `insert`, `update`, `delete`, `count` |
| `table` | string | Yes | Table name |
| `conditions` | string | No | WHERE clause |
| `data` | string | No | JSON data for insert/update |
| `limit` | integer | No | Max results (default: 10) |

**Example:**
```json
{
  "name": "postgres_query",
  "arguments": {
    "query_type": "select",
    "table": "campaigns",
    "conditions": "brand = 'nike' AND conversion_rate > 0.04",
    "limit": 5
  }
}
```

### `sql_database`

Execute SQL queries on a database.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query` | string | Yes | SQL query to execute |
| `database` | string | No | Database name (default: "default") |

### `redis_cache_operation`

Perform Redis cache operations.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | string | Yes | `get`, `set`, `delete`, `list` |
| `key` | string | Conditional | Cache key (required for get/set/delete) |
| `value` | string | No | Value for set operation |
| `ttl` | integer | No | TTL in seconds for set |

---

## ServiceNow Tools

### `ServiceNow_ITSM`

IT Service Management operations (incidents).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | string | Yes | `create`, `get`, `update` |
| `short_description` | string | Conditional | Required for create |
| `description` | string | No | Full description |
| `priority` | string | No | 1-5 (default: 3) |
| `impact` | string | No | 1-3 (default: 3) |
| `urgency` | string | No | 1-3 (default: 3) |
| `category` | string | No | Category (default: "inquiry") |
| `sys_id` | string | Conditional | Required for get/update |
| `state` | string | No | For update (1=New, 6=Resolved, 7=Closed) |
| `work_notes` | string | No | Internal notes |
| `close_notes` | string | No | Resolution notes |

**Operations:**
- `create` - Create new incident
- `get` - Retrieve incident by sys_id or number
- `update` - Update incident status, notes, etc.

**Example:**
```json
{
  "name": "ServiceNow_ITSM",
  "arguments": {
    "operation": "create",
    "short_description": "User cannot access email",
    "description": "User reports Outlook not loading",
    "priority": "2",
    "category": "software"
  }
}
```

### `ServiceNow_CSM`

Customer Service Management operations (cases).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | string | Yes | `create`, `get`, `update` |
| `short_description` | string | Conditional | Required for create |
| `description` | string | No | Full description |
| `priority` | string | No | 1-5 (default: 4) |
| `contact` | string | No | Contact email |
| `account` | string | No | Account ID |
| `origin` | string | No | `phone`, `email`, `web` |
| `escalation` | string | No | 0=Normal, 1=Manager, 2=Executive |
| `sys_id` | string | Conditional | Required for get/update |
| `state` | string | No | Case state |
| `work_notes` | string | No | Internal notes |

---

## Salesforce Tools

### `Salesforce_CSM`

Salesforce Customer Service Management operations.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | string | Yes | `create`, `get`, `update` |
| `status` | string | No | Case status (default: "New") |
| `case_origin` | string | No | Origin (default: "Email") |
| `priority` | string | No | Low, Medium, High (default: Medium) |
| `subject` | string | No | Case subject |
| `description` | string | No | Case description |
| `first_name` | string | No | Contact first name |
| `last_name` | string | No | Contact last name |
| `email_address` | string | No | Contact email |
| `contact_phone` | string | No | Contact phone |
| `account_id` | string | No | Salesforce Account ID |
| `case_id` | string | Conditional | Required for get/update |
| `internal_comments` | string | No | Internal notes |

**Example:**
```json
{
  "name": "Salesforce_CSM",
  "arguments": {
    "operation": "create",
    "subject": "Login issue reported",
    "description": "Customer cannot log in to portal",
    "priority": "High",
    "email_address": "customer@example.com"
  }
}
```

---

## File Tools

### `file_operations`

Perform file system operations.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | string | Yes | `read`, `write`, `list`, `exists` |
| `path` | string | Yes | File or directory path |
| `content` | string | No | Content for write operation |

### `get_file_info`

Get metadata about a file.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `file_path` | string | Yes | Path to the file |

**Returns:** File size, modification time, permissions, type.

---

## Utility Tools

### `add_numbers`

Add two numbers and return the sum.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `a` | integer | Yes | First number |
| `b` | integer | Yes | Second number |

### `get_current_time`

Get the current time in a specified timezone.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `timezone` | string | No | Timezone (default: "UTC") |

### `calculate`

Perform mathematical calculations.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `expression` | string | Yes | Math expression to evaluate |

### `weather_forecast`

Get weather forecast for a location (mock).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `location` | string | Yes | Location name |
| `days` | integer | No | Forecast days (default: 1) |

### `print_to_console`

Print a debug message to the console.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `message` | string | Yes | Message to print |

### `json_operations`

Perform JSON operations (parse, format, validate).

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `operation` | string | Yes | `parse`, `format`, `validate` |
| `data` | string | Yes | JSON string to process |

---

## Tool Registration API

### List All Tools

```http
GET /api/tools
X-elevAIte-UserId: user-123
```

### Get Tool Details

```http
GET /api/tools/web_search
```

**Response:**
```json
{
  "id": "uuid",
  "name": "web_search",
  "description": "Search the web...",
  "parameters_schema": {
    "type": "object",
    "properties": {
      "query": { "type": "string", "description": "The search query" }
    },
    "required": ["query"]
  },
  "source": "local",
  "is_active": true
}
```

### Register Custom Tool

```http
POST /api/tools/db
Content-Type: application/json

{
  "name": "my_custom_tool",
  "description": "A custom tool",
  "tool_type": "api",
  "execution_type": "api",
  "api_endpoint": "https://api.example.com/action",
  "http_method": "POST",
  "parameters_schema": {
    "type": "object",
    "properties": {
      "input": { "type": "string" }
    }
  }
}
```

### Sync Local Tools to Database

```http
POST /api/tools/sync?source=local
```

---

## OpenAI Function Calling Format

All tools expose schemas compatible with OpenAI function calling:

```http
GET /api/tools/schemas/openai
```

**Response:**
```json
{
  "schemas": {
    "web_search": {
      "type": "function",
      "function": {
        "name": "web_search",
        "description": "Search the web...",
        "parameters": {
          "type": "object",
          "properties": {...},
          "required": ["query"]
        }
      }
    }
  },
  "total_count": 25,
  "format": "openai_function_calling"
}
```

