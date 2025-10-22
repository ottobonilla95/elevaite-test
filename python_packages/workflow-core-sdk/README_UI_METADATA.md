# Workflow UI Metadata Feature

## Quick Start

The workflow schema now supports UI metadata for visual workflow editors:

```python
from workflow_core_sdk.schemas.workflows import (
    WorkflowConfig,
    StepBase,
    UIPosition,
    StepConnection,
    ToolOverride
)

# Create a workflow with UI metadata
workflow = WorkflowConfig(
    name="My Visual Workflow",
    steps=[
        StepBase(
            step_id="step-1",
            step_type="tool",
            name="Send Email",
            position=UIPosition(x=100, y=200),  # Canvas position
            config={"tool_name": "send_email"},
            tool_override=ToolOverride(  # Workflow-specific customization
                title="Welcome Email",
                description="Send welcome email to new user"
            )
        )
    ],
    connections=[  # Visual edges
        StepConnection(
            source_step_id="step-1",
            target_step_id="step-2",
            animated=True
        )
    ]
)
```

## Features

### 1. Step Positions 📍

Store x, y coordinates for visual canvas placement:

```python
position=UIPosition(x=250.5, y=150.0)
```

### 2. Step Connections 🔗

Define visual edges between steps:

```python
StepConnection(
    source_step_id="step-1",
    target_step_id="step-2",
    source_handle="success",      # For multi-output steps
    connection_type="conditional", # default, conditional, error, etc.
    label="On Success",
    animated=True
)
```

### 3. Tool Overrides 🎨

Customize tool labels per workflow:

```python
tool_override=ToolOverride(
    title="Customer Email Notification",
    description="Send email to customer about order",
    parameter_overrides={
        "recipient": {
            "title": "Customer Email",
            "description": "Email of the customer to notify"
        }
    }
)
```

## Documentation

- **[Complete Usage Guide](docs/WORKFLOW_UI_METADATA.md)** - Detailed documentation with examples
- **[Migration Guide](docs/MIGRATION_OLD_TO_NEW_SCHEMA.md)** - Migrate from old schema
- **[Implementation Summary](../../WORKFLOW_UI_METADATA_IMPLEMENTATION.md)** - Technical details

## Examples

Run the examples to see the features in action:

```bash
cd python_packages/workflow-core-sdk
python examples/workflow_ui_metadata_example.py
```

This will show:
1. Basic workflow with step positions
2. Workflow with visual connections
3. Workflow with tool overrides
4. Complete workflow with all features

## Testing

All features are fully tested:

```bash
cd python_packages/workflow-core-sdk
pytest tests/test_workflow_ui_metadata.py -v          # Schema tests (12 tests)
pytest tests/test_workflow_ui_integration.py -v       # Integration tests (4 tests)
```

**Status**: ✅ 16/16 tests passing

## API Usage

### Create Workflow with UI Metadata

```bash
POST /api/workflows
Content-Type: application/json

{
  "name": "My Workflow",
  "steps": [
    {
      "step_id": "step-1",
      "step_type": "tool",
      "position": {"x": 100, "y": 200},
      "config": {"tool_name": "my_tool"},
      "tool_override": {
        "title": "Custom Title",
        "description": "Custom description"
      }
    }
  ],
  "connections": [
    {
      "source_step_id": "step-1",
      "target_step_id": "step-2",
      "animated": true
    }
  ]
}
```

### Retrieve Workflow

```bash
GET /api/workflows/{workflow_id}
```

Response includes all UI metadata in the `configuration` field.

## Frontend Integration

### TypeScript Types

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
  parameter_overrides?: Record<string, any>;
}
```

### React Flow Example

```typescript
import ReactFlow from 'reactflow';

// Convert workflow to React Flow format
const nodes = workflow.steps.map(step => ({
  id: step.step_id,
  position: step.position || { x: 0, y: 0 },
  data: {
    label: step.tool_override?.title || step.name,
    description: step.tool_override?.description
  }
}));

const edges = workflow.connections?.map(conn => ({
  id: `${conn.source_step_id}-${conn.target_step_id}`,
  source: conn.source_step_id,
  target: conn.target_step_id,
  animated: conn.animated,
  label: conn.label
})) || [];

<ReactFlow nodes={nodes} edges={edges} />
```

## Backward Compatibility

✅ **Fully backward compatible**

All UI metadata fields are optional:
- Workflows without positions still execute normally
- Workflows without connections use dependencies for execution order
- Workflows without tool overrides use default tool metadata

```python
# This still works!
workflow = WorkflowConfig(
    name="Legacy Workflow",
    steps=[
        StepBase(
            step_id="step-1",
            step_type="tool",
            config={"tool_name": "my_tool"}
            # No position, no tool_override
        )
    ]
    # No connections
)
```

## Schema Structure

```
WorkflowConfig
├── name: string
├── description: string
├── steps: List[StepConfig]
│   └── StepBase
│       ├── step_id: string
│       ├── step_type: string
│       ├── position?: UIPosition
│       │   ├── x: float
│       │   └── y: float
│       └── tool_override?: ToolOverride
│           ├── title?: string
│           ├── description?: string
│           └── parameter_overrides?: Dict
└── connections: List[StepConnection]
    ├── source_step_id: string
    ├── target_step_id: string
    ├── source_handle?: string
    ├── target_handle?: string
    ├── connection_type?: string
    ├── label?: string
    └── animated: bool
```

## Key Benefits

1. **Visual Workflow Editor** - Drag-and-drop positioning with persistent layout
2. **Flexible Tool Customization** - Same tool, different labels per workflow
3. **Clear Workflow Logic** - Visual connections show data flow
4. **Standards-Based** - Uses standard JSON schema, no custom extensions
5. **Backward Compatible** - Existing workflows work unchanged
6. **Type-Safe** - Full Pydantic validation and TypeScript types

## Files Modified

### Core Schema
- `workflow_core_sdk/schemas/workflows.py` - Added UIPosition, StepConnection, ToolOverride
- `workflow_engine_poc/schemas/workflows.py` - Kept in sync with SDK

### Tests
- `tests/test_workflow_ui_metadata.py` - Schema validation tests
- `tests/test_workflow_ui_integration.py` - Database integration tests

### Documentation
- `docs/WORKFLOW_UI_METADATA.md` - Complete usage guide
- `docs/MIGRATION_OLD_TO_NEW_SCHEMA.md` - Migration from old schema
- `README_UI_METADATA.md` - This file

### Examples
- `examples/workflow_ui_metadata_example.py` - Working examples

## Next Steps

### For Backend Developers
1. ✅ Schema updated with UI metadata support
2. ✅ Tests passing (16/16)
3. ✅ Documentation complete
4. 🔄 Deploy to staging/production

### For Frontend Developers
1. Update workflow editor to save/load positions
2. Implement connection visualization
3. Add tool override UI in step configuration
4. Handle graceful degradation for missing metadata

## Support

For questions or issues:
- Check the [complete documentation](docs/WORKFLOW_UI_METADATA.md)
- Review the [examples](examples/workflow_ui_metadata_example.py)
- Run the tests to verify your setup

## License

Same as the parent project.

