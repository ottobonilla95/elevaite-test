# Workflow UI Metadata

## Overview

The workflow schema now supports UI metadata for visual workflow editors, including:
- **Step positions** (x, y coordinates for canvas placement)
- **Step connections** (visual edges between steps)
- **Tool overrides** (workflow-specific tool customization)

This metadata is stored in the workflow's `configuration` JSON field and is completely optional - workflows without UI metadata will continue to work normally.

## Features

### 1. Step Positions

Each step can have a `position` field specifying its location on the visual canvas:

```python
{
  "step_id": "step-1",
  "step_type": "tool",
  "name": "Send Email",
  "position": {
    "x": 250.5,
    "y": 100.0
  },
  "config": {
    "tool_name": "send_email"
  }
}
```

**Schema:**
```python
class UIPosition(BaseModel):
    x: float  # X coordinate on canvas
    y: float  # Y coordinate on canvas
```

### 2. Step Connections

The workflow configuration includes a `connections` array that defines visual edges between steps:

```python
{
  "name": "My Workflow",
  "steps": [...],
  "connections": [
    {
      "source_step_id": "step-1",
      "target_step_id": "step-2",
      "connection_type": "default",
      "animated": true
    },
    {
      "source_step_id": "step-2",
      "target_step_id": "step-3",
      "source_handle": "success",
      "target_handle": "input",
      "connection_type": "conditional",
      "label": "On Success"
    }
  ]
}
```

**Schema:**
```python
class StepConnection(BaseModel):
    source_step_id: str              # ID of the source step
    target_step_id: str              # ID of the target step
    source_handle: Optional[str]     # For multi-output steps (e.g., "success", "error")
    target_handle: Optional[str]     # For multi-input steps
    connection_type: Optional[str]   # "default", "conditional", "error", etc.
    label: Optional[str]             # Display label for the connection
    animated: bool = False           # Whether to animate the connection line
```

**Connection Types:**
- `default` - Standard sequential flow
- `conditional` - Conditional branching
- `error` - Error handling path
- `parallel` - Parallel execution branch
- Custom types as needed by your UI

### 3. Tool Overrides

For tool steps, you can override the tool's title, description, and parameter metadata specifically for this workflow:

```python
{
  "step_id": "email-step",
  "step_type": "tool",
  "name": "Send Notification Email",
  "config": {
    "tool_name": "send_email"
  },
  "tool_override": {
    "title": "Customer Notification",
    "description": "Send email notification to customer about order status",
    "parameter_overrides": {
      "recipient": {
        "title": "Customer Email",
        "description": "Email address of the customer to notify"
      },
      "subject": {
        "title": "Email Subject",
        "description": "Subject line for the notification email"
      }
    }
  }
}
```

**Schema:**
```python
class ToolOverride(BaseModel):
    title: Optional[str]                          # Override tool title
    description: Optional[str]                    # Override tool description
    parameter_overrides: Dict[str, Any]           # Override parameter metadata
```

**Parameter Override Structure:**
```python
{
  "parameter_name": {
    "title": "Custom Title",
    "description": "Custom description for this workflow",
    "placeholder": "Custom placeholder text",
    "help_text": "Additional help text"
  }
}
```

## Complete Example

Here's a complete workflow with all UI metadata:

```json
{
  "name": "Customer Onboarding",
  "description": "Automated customer onboarding workflow",
  "version": "1.0.0",
  "steps": [
    {
      "step_id": "trigger-1",
      "step_type": "trigger",
      "position": {
        "x": 100,
        "y": 100
      },
      "parameters": {
        "kind": "webhook"
      }
    },
    {
      "step_id": "validate-1",
      "step_type": "tool",
      "name": "Validate Customer Data",
      "position": {
        "x": 300,
        "y": 100
      },
      "dependencies": ["trigger-1"],
      "config": {
        "tool_name": "validate_data"
      },
      "tool_override": {
        "title": "Customer Data Validation",
        "description": "Validate customer information before creating account"
      }
    },
    {
      "step_id": "create-account-1",
      "step_type": "tool",
      "name": "Create Account",
      "position": {
        "x": 500,
        "y": 100
      },
      "dependencies": ["validate-1"],
      "config": {
        "tool_name": "create_user_account"
      }
    },
    {
      "step_id": "send-email-1",
      "step_type": "tool",
      "name": "Send Welcome Email",
      "position": {
        "x": 700,
        "y": 100
      },
      "dependencies": ["create-account-1"],
      "config": {
        "tool_name": "send_email"
      },
      "tool_override": {
        "title": "Welcome Email",
        "description": "Send welcome email to new customer",
        "parameter_overrides": {
          "recipient": {
            "title": "New Customer Email",
            "description": "Email address of the newly registered customer"
          },
          "subject": {
            "title": "Welcome Email Subject"
          }
        }
      }
    }
  ],
  "connections": [
    {
      "source_step_id": "trigger-1",
      "target_step_id": "validate-1",
      "connection_type": "default",
      "animated": true
    },
    {
      "source_step_id": "validate-1",
      "target_step_id": "create-account-1",
      "source_handle": "success",
      "connection_type": "conditional",
      "label": "Valid Data",
      "animated": true
    },
    {
      "source_step_id": "create-account-1",
      "target_step_id": "send-email-1",
      "connection_type": "default"
    }
  ],
  "tags": ["onboarding", "customer"]
}
```

## API Usage

### Creating a Workflow with UI Metadata

```python
from workflow_core_sdk.schemas.workflows import (
    WorkflowConfig,
    StepBase,
    UIPosition,
    StepConnection,
    ToolOverride
)

workflow = WorkflowConfig(
    name="My Visual Workflow",
    steps=[
        StepBase(
            step_id="step-1",
            step_type="tool",
            name="First Step",
            position=UIPosition(x=100, y=100),
            config={"tool_name": "my_tool"},
            tool_override=ToolOverride(
                title="Custom Tool Title",
                description="Custom description for this workflow"
            )
        ),
        StepBase(
            step_id="step-2",
            step_type="tool",
            name="Second Step",
            position=UIPosition(x=300, y=100),
            dependencies=["step-1"],
            config={"tool_name": "another_tool"}
        )
    ],
    connections=[
        StepConnection(
            source_step_id="step-1",
            target_step_id="step-2",
            connection_type="default",
            animated=True
        )
    ]
)
```

### REST API

**Create Workflow:**
```bash
POST /api/workflows
Content-Type: application/json

{
  "name": "My Workflow",
  "steps": [
    {
      "step_id": "step-1",
      "step_type": "tool",
      "position": {"x": 100, "y": 100},
      "config": {"tool_name": "my_tool"}
    }
  ],
  "connections": [
    {
      "source_step_id": "step-1",
      "target_step_id": "step-2"
    }
  ]
}
```

## Frontend Integration

### TypeScript Interfaces

```typescript
interface UIPosition {
  x: number;
  y: number;
}

interface StepConnection {
  source_step_id: string;
  target_step_id: string;
  source_handle?: string;
  target_handle?: string;
  connection_type?: string;
  label?: string;
  animated?: boolean;
}

interface ToolOverride {
  title?: string;
  description?: string;
  parameter_overrides?: Record<string, {
    title?: string;
    description?: string;
    placeholder?: string;
    help_text?: string;
  }>;
}

interface WorkflowStep {
  step_id?: string;
  step_type: string;
  name?: string;
  position?: UIPosition;
  tool_override?: ToolOverride;
  config?: Record<string, any>;
  // ... other fields
}

interface WorkflowConfig {
  name: string;
  steps: WorkflowStep[];
  connections?: StepConnection[];
  // ... other fields
}
```

## Backward Compatibility

All UI metadata fields are **optional**. Existing workflows without this metadata will continue to work:

- Workflows without `position` fields will execute normally
- Workflows without `connections` will execute based on `dependencies`
- Workflows without `tool_override` will use default tool metadata

The UI can handle missing metadata gracefully:
- Auto-layout steps without positions
- Derive connections from dependencies
- Fall back to tool defaults when no overrides exist

## Best Practices

1. **Always set positions** when creating workflows in a visual editor
2. **Keep connections in sync** with dependencies (connections are for UI, dependencies control execution)
3. **Use tool overrides sparingly** - only when the workflow context requires different labels
4. **Store connection metadata** even if it's redundant with dependencies - it preserves the visual layout
5. **Use meaningful connection types** to help users understand workflow logic

## Migration from Old Schema

If you're migrating from the old `workflow_agents` and `workflow_connections` tables:

```python
# Old schema
workflow_agent = {
    "position_x": 100,
    "position_y": 200,
    "agent_id": "agent-123"
}

# New schema
step = {
    "step_id": "step-1",
    "step_type": "agent",
    "position": {"x": 100, "y": 200},
    "config": {"agent_id": "agent-123"}
}
```

```python
# Old schema
connection = {
    "source_agent_id": "agent-1",
    "target_agent_id": "agent-2",
    "connection_type": "default"
}

# New schema
connection = {
    "source_step_id": "step-1",
    "target_step_id": "step-2",
    "connection_type": "default"
}
```

