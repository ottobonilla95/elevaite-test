# Step Type API Documentation

## Overview

The Step Type API provides endpoints for managing and querying workflow step types. It returns step schemas in OpenAI function calling format, making it easy to build UI components for workflow configuration.

## Key Features

- **OpenAI Schema Format**: All schemas use the OpenAI function calling format, compatible with existing tool/function UI components
- **Automatic Schema Generation**: Utility functions to generate schemas from Python functions
- **Database & Registry Sync**: Sync in-memory step types (from StepRegistry) to database for API access
- **CRUD Operations**: Full create, read, update, delete support for step types

## API Endpoints

### GET /api/steps/schemas

Get all step types with their input/output schemas in OpenAI format.

**Query Parameters:**
- `category` (optional): Filter by step category (e.g., "data_processing", "ai_llm")
- `is_active` (optional): Filter by active status (default: true)

**Response:**
```json
[
  {
    "step_type": "tool_execution",
    "name": "Tool Execution",
    "description": "Executes a tool by name or ID",
    "category": "utility",
    "input_schema": {
      "type": "function",
      "function": {
        "name": "tool_execution",
        "description": "Input parameters for Tool Execution",
        "parameters": {
          "type": "object",
          "properties": {
            "tool_name": {
              "type": "string",
              "description": "Name of the tool to execute"
            },
            "tool_id": {
              "type": "string",
              "description": "UUID of the tool"
            },
            "param_mapping": {
              "type": "object",
              "description": "Map tool parameters to input_data fields"
            },
            "static_params": {
              "type": "object",
              "description": "Static parameter values"
            }
          }
        }
      }
    },
    "output_schema": {
      "type": "function",
      "function": {
        "name": "tool_execution_output",
        "description": "Output from Tool Execution",
        "parameters": {
          "type": "object",
          "properties": {
            "success": {"type": "boolean"},
            "tool": {
              "type": "object",
              "properties": {
                "name": {"type": "string"}
              }
            },
            "params": {"type": "object"},
            "result": {"description": "The tool's return value"},
            "executed_at": {"type": "string", "format": "date-time"},
            "error": {"type": "string"}
          },
          "required": ["success"]
        }
      }
    }
  }
]
```

**Use Cases:**
- Building workflow editor UI
- Creating step configuration forms
- Generating mapping interfaces between steps

### GET /api/steps/types

List all registered step types with full details.

**Query Parameters:**
- `category` (optional): Filter by category
- `is_active` (optional): Filter by active status

**Response:**
```json
[
  {
    "id": "uuid-here",
    "step_type": "tool_execution",
    "name": "Tool Execution",
    "description": "Executes a tool by name or ID",
    "category": "utility",
    "execution_type": "local",
    "function_reference": "workflow_engine_poc.steps.tool_steps.tool_execution_step",
    "parameters_schema": {...},
    "response_schema": {...},
    "is_active": true,
    "version": "1.0.0",
    "created_at": "2025-10-06T12:00:00Z"
  }
]
```

### GET /api/steps/schemas/{step_type}

Get input/output schemas for a specific step type.

**Path Parameters:**
- `step_type`: Step type identifier (e.g., "tool_execution")

**Response:**
```json
{
  "step_type": "tool_execution",
  "name": "Tool Execution",
  "description": "Executes a tool by name or ID",
  "category": "utility",
  "input_schema": {...},
  "output_schema": {...}
}
```

### GET /api/steps/types/{step_type}

Get full details for a specific step type.

**Path Parameters:**
- `step_type`: Step type identifier

**Response:** Same as individual item in `/api/steps/types` list

### POST /api/steps/types

Register a new step type.

**Request Body:**
```json
{
  "step_type": "custom_processor",
  "name": "Custom Processor",
  "description": "Processes data in a custom way",
  "category": "data_processing",
  "execution_type": "local",
  "function_reference": "my_module.custom_processor_step",
  "parameters_schema": {
    "type": "object",
    "properties": {
      "input_field": {
        "type": "string",
        "description": "Field to process"
      }
    },
    "required": ["input_field"]
  },
  "response_schema": {
    "type": "object",
    "properties": {
      "success": {"type": "boolean"},
      "result": {"type": "object"}
    }
  }
}
```

**Response:** Created step type details (201 Created)

### PUT /api/steps/types/{step_type}

Update a step type.

**Path Parameters:**
- `step_type`: Step type identifier

**Request Body:** Partial update (all fields optional)
```json
{
  "description": "Updated description",
  "parameters_schema": {...}
}
```

**Response:** Updated step type details

### DELETE /api/steps/types/{step_type}

Delete a step type (soft delete - sets `is_active=false`).

**Path Parameters:**
- `step_type`: Step type identifier

**Response:** 204 No Content

### POST /api/steps/sync-registry

Sync step types from the in-memory StepRegistry to the database.

This is useful for persisting step types that were registered during application startup.

**Request Body:**
```json
{
  "update_existing": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Synced 5 new step types, updated 0, skipped 3",
  "created": 5,
  "updated": 0,
  "skipped": 3
}
```

## Schema Utilities

The SDK provides utilities for generating OpenAI-compatible schemas:

### function_to_openai_schema()

Automatically generate a schema from a Python function:

```python
from workflow_core_sdk.utils.schema_utils import function_to_openai_schema

def my_tool(query: str, max_results: int = 10) -> dict:
    '''Search for information based on a query.'''
    return {'results': []}

schema = function_to_openai_schema(my_tool)
# Returns OpenAI function calling schema
```

### create_step_input_schema()

Create an input schema for a step type:

```python
from workflow_core_sdk.utils.schema_utils import create_step_input_schema

input_schema = create_step_input_schema(
    step_type="my_step",
    parameters_schema={
        "type": "object",
        "properties": {
            "input": {"type": "string"}
        }
    },
    description="Input parameters for my step"
)
```

### create_step_output_schema()

Create an output schema for a step type:

```python
from workflow_core_sdk.utils.schema_utils import create_step_output_schema

output_schema = create_step_output_schema(
    step_type="my_step",
    output_schema={
        "type": "object",
        "properties": {
            "result": {"type": "string"}
        }
    },
    description="Output from my step"
)
```

### extract_output_fields()

Extract available output fields for UI mapping:

```python
from workflow_core_sdk.utils.schema_utils import extract_output_fields

fields = extract_output_fields(output_schema, "step1")
# Returns:
# [
#   {
#     "path": "step1.result",
#     "name": "result",
#     "type": "string",
#     "description": "..."
#   }
# ]
```

## Frontend Integration

The OpenAI schema format is compatible with existing tool/function UI components:

```typescript
// TypeScript types (already exist in your codebase)
import { ChatCompletionToolParam } from 'openai/resources/chat/completions';

interface StepSchemaResponse {
  step_type: string;
  name: string;
  description: string;
  category: string;
  input_schema: ChatCompletionToolParam;
  output_schema: ChatCompletionToolParam;
}

// Fetch step schemas
const response = await fetch('/api/steps/schemas');
const schemas: StepSchemaResponse[] = await response.json();

// Use with existing tool UI components
schemas.forEach(schema => {
  // schema.input_schema and schema.output_schema are already
  // in the format your tool UI components expect
});
```

## Example: Building a Workflow Mapping UI

1. **Fetch available step types:**
```typescript
const stepSchemas = await fetch('/api/steps/schemas').then(r => r.json());
```

2. **Display step configuration form:**
```typescript
// Use input_schema to build form fields
const inputSchema = stepSchemas.find(s => s.step_type === 'tool_execution').input_schema;
// Render form based on inputSchema.function.parameters
```

3. **Build output mapping:**
```typescript
// Use output_schema to show available fields for mapping
const outputSchema = stepSchemas.find(s => s.step_type === 'tool_execution').output_schema;
const fields = extractOutputFields(outputSchema, 'step1');
// Show dropdown with fields: ["step1.success", "step1.result", "step1.tool.name", ...]
```

4. **Create workflow step:**
```typescript
const step = {
  step_id: "my_tool_step",
  step_type: "tool_execution",
  dependencies: ["previous_step"],
  input_mapping: {
    // Map from previous step outputs
    "tool_params": "previous_step.result.data"
  },
  config: {
    tool_name: "my_tool",
    param_mapping: {
      // Map from input_data to tool params
      "query": "tool_params.query"
    }
  }
};
```

