# Migration Guide: Old Workflow Schema to New Schema with UI Metadata

## Overview

This guide helps you migrate from the old Agent Studio workflow schema (with separate `workflow_agents` and `workflow_connections` tables) to the new unified workflow schema with UI metadata support.

## Old Schema (Agent Studio)

### Database Tables

**workflow_agents:**
```sql
CREATE TABLE workflow_agents (
    id UUID PRIMARY KEY,
    workflow_id UUID,
    agent_id UUID,
    position_x FLOAT,
    position_y FLOAT,
    order_index INTEGER,
    ...
);
```

**workflow_connections:**
```sql
CREATE TABLE workflow_connections (
    id UUID PRIMARY KEY,
    workflow_id UUID,
    source_agent_id UUID,
    target_agent_id UUID,
    connection_type VARCHAR,
    ...
);
```

## New Schema (Workflow Core SDK)

### Single Configuration JSON

All workflow data is now stored in the `workflows.configuration` JSON field:

```json
{
  "name": "My Workflow",
  "steps": [
    {
      "step_id": "step-1",
      "step_type": "agent",
      "position": {"x": 100, "y": 200},
      "config": {"agent_id": "agent-123"}
    }
  ],
  "connections": [
    {
      "source_step_id": "step-1",
      "target_step_id": "step-2",
      "connection_type": "default"
    }
  ]
}
```

## Migration Steps

### Step 1: Extract Old Data

```python
from sqlalchemy import select
from old_db.models import WorkflowAgent, WorkflowConnection

# Get all agents for a workflow
old_agents = session.exec(
    select(WorkflowAgent).where(WorkflowAgent.workflow_id == workflow_id)
).all()

# Get all connections for a workflow
old_connections = session.exec(
    select(WorkflowConnection).where(WorkflowConnection.workflow_id == workflow_id)
).all()
```

### Step 2: Convert to New Schema

```python
from workflow_core_sdk.schemas.workflows import (
    WorkflowConfig,
    StepBase,
    UIPosition,
    StepConnection
)

# Convert agents to steps
steps = []
for old_agent in old_agents:
    step = StepBase(
        step_id=f"step-{old_agent.id}",  # Generate new step ID
        step_type="agent",
        name=old_agent.name,
        position=UIPosition(
            x=old_agent.position_x,
            y=old_agent.position_y
        ),
        config={
            "agent_id": str(old_agent.agent_id),
            # ... other agent config
        }
    )
    steps.append(step)

# Convert connections
connections = []
for old_conn in old_connections:
    connection = StepConnection(
        source_step_id=f"step-{old_conn.source_agent_id}",
        target_step_id=f"step-{old_conn.target_agent_id}",
        connection_type=old_conn.connection_type or "default"
    )
    connections.append(connection)

# Create new workflow config
new_workflow = WorkflowConfig(
    name=old_workflow.name,
    description=old_workflow.description,
    steps=steps,
    connections=connections
)
```

### Step 3: Save to Database

```python
from workflow_core_sdk.db.models import Workflow

# Create new workflow record
workflow = Workflow(
    name=new_workflow.name,
    description=new_workflow.description,
    configuration=new_workflow.model_dump(),  # Store as JSON
    user_id=user_id,
    editable=True
)

session.add(workflow)
session.commit()
```

## Complete Migration Script

```python
"""
Migration script: Old workflow schema to new schema with UI metadata
"""

from sqlalchemy import select
from workflow_core_sdk.schemas.workflows import (
    WorkflowConfig,
    StepBase,
    UIPosition,
    StepConnection
)
from workflow_core_sdk.db.models import Workflow as NewWorkflow
# Import your old models
# from old_db.models import Workflow as OldWorkflow, WorkflowAgent, WorkflowConnection


def migrate_workflow(session, old_workflow_id: str, user_id: str):
    """Migrate a single workflow from old schema to new schema"""
    
    # 1. Get old workflow data
    old_workflow = session.exec(
        select(OldWorkflow).where(OldWorkflow.id == old_workflow_id)
    ).first()
    
    if not old_workflow:
        raise ValueError(f"Workflow {old_workflow_id} not found")
    
    # 2. Get agents
    old_agents = session.exec(
        select(WorkflowAgent).where(WorkflowAgent.workflow_id == old_workflow_id)
    ).all()
    
    # 3. Get connections
    old_connections = session.exec(
        select(WorkflowConnection).where(WorkflowConnection.workflow_id == old_workflow_id)
    ).all()
    
    # 4. Create agent_id to step_id mapping
    agent_to_step = {}
    for agent in old_agents:
        step_id = f"step-{agent.id}"
        agent_to_step[str(agent.id)] = step_id
    
    # 5. Convert agents to steps
    steps = []
    for old_agent in old_agents:
        step = StepBase(
            step_id=agent_to_step[str(old_agent.id)],
            step_type="agent",
            name=old_agent.name or f"Agent {old_agent.agent_id}",
            position=UIPosition(
                x=old_agent.position_x or 0,
                y=old_agent.position_y or 0
            ),
            config={
                "agent_id": str(old_agent.agent_id),
                # Add other agent configuration as needed
            },
            # Convert dependencies if they exist
            dependencies=[
                agent_to_step[str(dep_id)]
                for dep_id in (old_agent.dependencies or [])
                if str(dep_id) in agent_to_step
            ]
        )
        steps.append(step)
    
    # 6. Convert connections
    connections = []
    for old_conn in old_connections:
        source_id = str(old_conn.source_agent_id)
        target_id = str(old_conn.target_agent_id)
        
        if source_id in agent_to_step and target_id in agent_to_step:
            connection = StepConnection(
                source_step_id=agent_to_step[source_id],
                target_step_id=agent_to_step[target_id],
                connection_type=old_conn.connection_type or "default",
                label=old_conn.label if hasattr(old_conn, 'label') else None
            )
            connections.append(connection)
    
    # 7. Create new workflow config
    new_config = WorkflowConfig(
        name=old_workflow.name,
        description=old_workflow.description,
        version=old_workflow.version or "1.0.0",
        steps=steps,
        connections=connections,
        tags=old_workflow.tags or [],
        created_by=str(user_id)
    )
    
    # 8. Create new workflow record
    new_workflow = NewWorkflow(
        name=new_config.name,
        description=new_config.description,
        configuration=new_config.model_dump(),
        user_id=user_id,
        editable=old_workflow.editable if hasattr(old_workflow, 'editable') else True
    )
    
    session.add(new_workflow)
    session.commit()
    session.refresh(new_workflow)
    
    return new_workflow


def migrate_all_workflows(session, user_id: str):
    """Migrate all workflows for a user"""
    
    old_workflows = session.exec(
        select(OldWorkflow).where(OldWorkflow.user_id == user_id)
    ).all()
    
    migrated = []
    errors = []
    
    for old_workflow in old_workflows:
        try:
            new_workflow = migrate_workflow(session, str(old_workflow.id), user_id)
            migrated.append({
                'old_id': str(old_workflow.id),
                'new_id': str(new_workflow.id),
                'name': new_workflow.name
            })
            print(f"✅ Migrated: {new_workflow.name}")
        except Exception as e:
            errors.append({
                'old_id': str(old_workflow.id),
                'name': old_workflow.name,
                'error': str(e)
            })
            print(f"❌ Failed: {old_workflow.name} - {e}")
    
    return {
        'migrated': migrated,
        'errors': errors,
        'total': len(old_workflows),
        'success': len(migrated),
        'failed': len(errors)
    }


if __name__ == "__main__":
    # Example usage
    from workflow_core_sdk.db.database import get_db
    
    db = next(get_db())
    try:
        result = migrate_all_workflows(db, user_id="your-user-id")
        print(f"\n📊 Migration Summary:")
        print(f"   Total: {result['total']}")
        print(f"   Success: {result['success']}")
        print(f"   Failed: {result['failed']}")
    finally:
        db.close()
```

## Field Mapping Reference

| Old Schema | New Schema | Notes |
|------------|------------|-------|
| `workflow_agents.position_x` | `step.position.x` | Now in UIPosition object |
| `workflow_agents.position_y` | `step.position.y` | Now in UIPosition object |
| `workflow_agents.agent_id` | `step.config.agent_id` | Stored in config dict |
| `workflow_agents.order_index` | `step.dependencies` | Use dependencies for ordering |
| `workflow_connections.source_agent_id` | `connection.source_step_id` | Now references step_id |
| `workflow_connections.target_agent_id` | `connection.target_step_id` | Now references step_id |
| `workflow_connections.connection_type` | `connection.connection_type` | Same field name |

## Key Differences

### 1. Storage Location
- **Old**: Separate tables (`workflow_agents`, `workflow_connections`)
- **New**: Single JSON field (`workflows.configuration`)

### 2. Step Identification
- **Old**: Used `agent_id` directly
- **New**: Uses `step_id` (can reference agents, tools, or other step types)

### 3. Positioning
- **Old**: Separate `position_x` and `position_y` columns
- **New**: Nested `position` object with `x` and `y` fields

### 4. Dependencies
- **Old**: Implicit from connections or `order_index`
- **New**: Explicit `dependencies` array on each step

### 5. Flexibility
- **Old**: Only supported agents
- **New**: Supports agents, tools, triggers, and custom step types

## Validation After Migration

```python
def validate_migrated_workflow(workflow_id: str):
    """Validate a migrated workflow"""
    
    workflow = session.exec(
        select(NewWorkflow).where(NewWorkflow.id == workflow_id)
    ).first()
    
    config = WorkflowConfig(**workflow.configuration)
    
    # Check all steps have positions
    for step in config.steps:
        assert step.position is not None, f"Step {step.step_id} missing position"
        assert step.position.x >= 0, f"Step {step.step_id} has negative x"
        assert step.position.y >= 0, f"Step {step.step_id} has negative y"
    
    # Check all connections reference valid steps
    step_ids = {step.step_id for step in config.steps}
    for conn in config.connections:
        assert conn.source_step_id in step_ids, f"Invalid source: {conn.source_step_id}"
        assert conn.target_step_id in step_ids, f"Invalid target: {conn.target_step_id}"
    
    print(f"✅ Workflow {workflow.name} validated successfully")
    return True
```

## Rollback Plan

If you need to rollback:

1. Keep old tables until migration is verified
2. Store mapping of old IDs to new IDs
3. Can regenerate old records from new JSON if needed

```python
def rollback_workflow(new_workflow_id: str):
    """Rollback a migrated workflow (for testing)"""
    
    new_workflow = session.exec(
        select(NewWorkflow).where(NewWorkflow.id == new_workflow_id)
    ).first()
    
    # Parse configuration
    config = WorkflowConfig(**new_workflow.configuration)
    
    # Recreate old workflow record
    old_workflow = OldWorkflow(
        name=config.name,
        description=config.description,
        user_id=new_workflow.user_id
    )
    session.add(old_workflow)
    session.flush()
    
    # Recreate agents
    for step in config.steps:
        if step.step_type == "agent":
            old_agent = WorkflowAgent(
                workflow_id=old_workflow.id,
                agent_id=step.config.get("agent_id"),
                position_x=step.position.x if step.position else 0,
                position_y=step.position.y if step.position else 0,
                name=step.name
            )
            session.add(old_agent)
    
    # Recreate connections
    for conn in config.connections:
        old_conn = WorkflowConnection(
            workflow_id=old_workflow.id,
            source_agent_id=conn.source_step_id,
            target_agent_id=conn.target_step_id,
            connection_type=conn.connection_type
        )
        session.add(old_conn)
    
    session.commit()
    return old_workflow
```

## Best Practices

1. **Test on a copy** of your database first
2. **Backup** all workflow data before migration
3. **Validate** each migrated workflow
4. **Keep old tables** until migration is verified in production
5. **Document** any custom fields that need special handling
6. **Run in batches** for large datasets
7. **Log all errors** for troubleshooting

## Support

If you encounter issues during migration:
- Check the validation output for specific errors
- Verify all old workflow data is accessible
- Ensure step IDs are unique within each workflow
- Confirm all connection references are valid

