"""
Integration tests for workflow UI metadata with database operations
"""

import pytest
from sqlmodel import Session, create_engine, SQLModel
from sqlalchemy.pool import StaticPool
from workflow_core_sdk.db.models import Workflow
from workflow_core_sdk.schemas.workflows import (
    WorkflowConfig,
    StepBase,
    TriggerStepConfig,
    TriggerParameters,
    UIPosition,
    StepConnection,
    ToolOverride,
)


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_create_workflow_with_ui_metadata(session: Session):
    """Test creating a workflow with UI metadata and saving to database"""
    
    # Create workflow config with UI metadata
    config = WorkflowConfig(
        name="Test Workflow with UI",
        description="Testing UI metadata storage",
        steps=[
            TriggerStepConfig(
                step_id="trigger-1",
                parameters=TriggerParameters(kind="webhook"),
                position=UIPosition(x=100, y=200)
            ),
            StepBase(
                step_id="step-1",
                step_type="tool",
                name="Process Data",
                position=UIPosition(x=300, y=200),
                dependencies=["trigger-1"],
                config={"tool_name": "process_data"},
                tool_override=ToolOverride(
                    title="Data Processor",
                    description="Process incoming data"
                )
            ),
            StepBase(
                step_id="step-2",
                step_type="tool",
                name="Send Result",
                position=UIPosition(x=500, y=200),
                dependencies=["step-1"],
                config={"tool_name": "send_result"}
            )
        ],
        connections=[
            StepConnection(
                source_step_id="trigger-1",
                target_step_id="step-1",
                animated=True
            ),
            StepConnection(
                source_step_id="step-1",
                target_step_id="step-2",
                connection_type="default"
            )
        ],
        tags=["test", "ui-metadata"]
    )
    
    # Create workflow in database
    workflow = Workflow(
        name=config.name,
        description=config.description,
        configuration=config.model_dump(),
        user_id="test-user-123",
        editable=True
    )
    
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    
    # Verify workflow was saved
    assert workflow.id is not None
    assert workflow.name == "Test Workflow with UI"
    
    # Verify configuration was saved correctly
    saved_config = WorkflowConfig(**workflow.configuration)
    assert saved_config.name == config.name
    assert len(saved_config.steps) == 3
    assert len(saved_config.connections) == 2
    
    # Verify positions were saved
    assert saved_config.steps[0].position.x == 100
    assert saved_config.steps[0].position.y == 200
    assert saved_config.steps[1].position.x == 300
    assert saved_config.steps[2].position.x == 500
    
    # Verify tool override was saved
    assert saved_config.steps[1].tool_override is not None
    assert saved_config.steps[1].tool_override.title == "Data Processor"
    
    # Verify connections were saved
    assert saved_config.connections[0].source_step_id == "trigger-1"
    assert saved_config.connections[0].target_step_id == "step-1"
    assert saved_config.connections[0].animated is True


def test_retrieve_and_update_workflow_ui_metadata(session: Session):
    """Test retrieving and updating workflow UI metadata"""
    
    # Create initial workflow
    initial_config = WorkflowConfig(
        name="Updatable Workflow",
        steps=[
            StepBase(
                step_id="step-1",
                step_type="tool",
                name="Initial Step",
                position=UIPosition(x=100, y=100),
                config={"tool_name": "tool1"}
            )
        ],
        connections=[]
    )
    
    workflow = Workflow(
        name=initial_config.name,
        configuration=initial_config.model_dump(),
        user_id="test-user-123"
    )
    
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    
    workflow_id = workflow.id
    
    # Retrieve workflow
    retrieved = session.get(Workflow, workflow_id)
    assert retrieved is not None
    
    # Parse configuration
    config = WorkflowConfig(**retrieved.configuration)
    
    # Update position
    config.steps[0].position = UIPosition(x=200, y=150)
    
    # Add a new step
    config.steps.append(
        StepBase(
            step_id="step-2",
            step_type="tool",
            name="New Step",
            position=UIPosition(x=400, y=150),
            dependencies=["step-1"],
            config={"tool_name": "tool2"}
        )
    )
    
    # Add connection
    config.connections.append(
        StepConnection(
            source_step_id="step-1",
            target_step_id="step-2",
            connection_type="default"
        )
    )
    
    # Save updated configuration
    retrieved.configuration = config.model_dump()
    session.add(retrieved)
    session.commit()
    session.refresh(retrieved)
    
    # Verify updates
    updated_config = WorkflowConfig(**retrieved.configuration)
    assert len(updated_config.steps) == 2
    assert updated_config.steps[0].position.x == 200
    assert updated_config.steps[0].position.y == 150
    assert len(updated_config.connections) == 1


def test_workflow_without_ui_metadata(session: Session):
    """Test that workflows without UI metadata still work (backward compatibility)"""
    
    # Create workflow without positions or connections
    config = WorkflowConfig(
        name="Legacy Workflow",
        steps=[
            TriggerStepConfig(
                step_id="trigger-1",
                parameters=TriggerParameters(kind="webhook")
                # No position
            ),
            StepBase(
                step_id="step-1",
                step_type="tool",
                name="Tool Step",
                dependencies=["trigger-1"],
                config={"tool_name": "my_tool"}
                # No position, no tool_override
            )
        ]
        # No connections
    )
    
    workflow = Workflow(
        name=config.name,
        configuration=config.model_dump(),
        user_id="test-user-123"
    )
    
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    
    # Verify workflow was saved
    assert workflow.id is not None
    
    # Verify configuration
    saved_config = WorkflowConfig(**workflow.configuration)
    assert len(saved_config.steps) == 2
    assert saved_config.steps[0].position is None
    assert saved_config.steps[1].position is None
    assert saved_config.steps[1].tool_override is None
    assert len(saved_config.connections) == 0


def test_complex_workflow_with_all_features(session: Session):
    """Test a complex workflow with all UI metadata features"""
    
    config = WorkflowConfig(
        name="Complex Order Processing",
        description="Full-featured workflow with all metadata",
        version="2.0.0",
        steps=[
            TriggerStepConfig(
                step_id="order-trigger",
                parameters=TriggerParameters(kind="webhook"),
                position=UIPosition(x=50, y=300)
            ),
            StepBase(
                step_id="validate",
                step_type="tool",
                name="Validate Order",
                position=UIPosition(x=250, y=300),
                dependencies=["order-trigger"],
                config={"tool_name": "validate_order"},
                tool_override=ToolOverride(
                    title="Order Validation",
                    description="Validate order items and customer info",
                    parameter_overrides={
                        "order_data": {
                            "title": "Order Information",
                            "description": "Complete order details"
                        }
                    }
                )
            ),
            StepBase(
                step_id="process-success",
                step_type="tool",
                name="Process Order",
                position=UIPosition(x=450, y=250),
                dependencies=["validate"],
                config={"tool_name": "process_order"}
            ),
            StepBase(
                step_id="handle-error",
                step_type="tool",
                name="Handle Error",
                position=UIPosition(x=450, y=350),
                dependencies=["validate"],
                config={"tool_name": "handle_error"}
            )
        ],
        connections=[
            StepConnection(
                source_step_id="order-trigger",
                target_step_id="validate",
                animated=True
            ),
            StepConnection(
                source_step_id="validate",
                target_step_id="process-success",
                source_handle="success",
                target_handle="input",
                connection_type="conditional",
                label="Valid Order",
                animated=True
            ),
            StepConnection(
                source_step_id="validate",
                target_step_id="handle-error",
                source_handle="error",
                target_handle="input",
                connection_type="error",
                label="Invalid Order"
            )
        ],
        tags=["orders", "validation", "complex"],
        timeout_seconds=300
    )
    
    workflow = Workflow(
        name=config.name,
        description=config.description,
        configuration=config.model_dump(),
        user_id="test-user-123",
        editable=True
    )
    
    session.add(workflow)
    session.commit()
    session.refresh(workflow)
    
    # Comprehensive verification
    saved_config = WorkflowConfig(**workflow.configuration)
    
    # Verify basic info
    assert saved_config.name == "Complex Order Processing"
    assert saved_config.version == "2.0.0"
    assert len(saved_config.tags) == 3
    assert saved_config.timeout_seconds == 300
    
    # Verify steps
    assert len(saved_config.steps) == 4
    
    # Verify positions
    assert saved_config.steps[0].position.x == 50
    assert saved_config.steps[1].position.x == 250
    assert saved_config.steps[2].position.x == 450
    assert saved_config.steps[3].position.x == 450
    
    # Verify tool override
    validate_step = saved_config.steps[1]
    assert validate_step.tool_override is not None
    assert validate_step.tool_override.title == "Order Validation"
    assert "order_data" in validate_step.tool_override.parameter_overrides
    
    # Verify connections
    assert len(saved_config.connections) == 3
    
    # Verify conditional connection
    conditional_conn = saved_config.connections[1]
    assert conditional_conn.source_handle == "success"
    assert conditional_conn.target_handle == "input"
    assert conditional_conn.connection_type == "conditional"
    assert conditional_conn.label == "Valid Order"
    assert conditional_conn.animated is True
    
    # Verify error connection
    error_conn = saved_config.connections[2]
    assert error_conn.connection_type == "error"
    assert error_conn.label == "Invalid Order"

