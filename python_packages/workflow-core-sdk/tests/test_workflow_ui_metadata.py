"""
Tests for workflow UI metadata (positions, connections, tool overrides)
"""

from workflow_core_sdk.schemas.workflows import (
    WorkflowConfig,
    StepBase,
    UIPosition,
    StepConnection,
    ToolOverride,
    TriggerStepConfig,
    TriggerParameters,
)


def test_ui_position_basic():
    """Test basic UIPosition creation"""
    position = UIPosition(x=100.5, y=200.75)
    assert position.x == 100.5
    assert position.y == 200.75


def test_step_with_position():
    """Test step with position metadata"""
    step = StepBase(
        step_id="step-1",
        step_type="tool",
        name="My Tool Step",
        position=UIPosition(x=250, y=150),
        config={"tool_name": "my_tool"}
    )
    
    assert step.position is not None
    assert step.position.x == 250
    assert step.position.y == 150


def test_step_without_position():
    """Test step without position (backward compatibility)"""
    step = StepBase(
        step_id="step-1",
        step_type="tool",
        name="My Tool Step",
        config={"tool_name": "my_tool"}
    )
    
    assert step.position is None


def test_step_connection_basic():
    """Test basic step connection"""
    connection = StepConnection(
        source_step_id="step-1",
        target_step_id="step-2"
    )
    
    assert connection.source_step_id == "step-1"
    assert connection.target_step_id == "step-2"
    assert connection.connection_type == "default"
    assert connection.animated is False


def test_step_connection_with_handles():
    """Test step connection with handles and custom type"""
    connection = StepConnection(
        source_step_id="step-1",
        target_step_id="step-2",
        source_handle="success",
        target_handle="input",
        connection_type="conditional",
        label="On Success",
        animated=True
    )
    
    assert connection.source_handle == "success"
    assert connection.target_handle == "input"
    assert connection.connection_type == "conditional"
    assert connection.label == "On Success"
    assert connection.animated is True


def test_tool_override_basic():
    """Test basic tool override"""
    override = ToolOverride(
        title="Custom Tool Title",
        description="Custom tool description"
    )
    
    assert override.title == "Custom Tool Title"
    assert override.description == "Custom tool description"
    assert override.parameter_overrides == {}


def test_tool_override_with_parameters():
    """Test tool override with parameter overrides"""
    override = ToolOverride(
        title="Send Customer Email",
        description="Send email to customer",
        parameter_overrides={
            "recipient": {
                "title": "Customer Email",
                "description": "Email address of the customer"
            },
            "subject": {
                "title": "Email Subject",
                "description": "Subject line for the email"
            }
        }
    )
    
    assert override.title == "Send Customer Email"
    assert "recipient" in override.parameter_overrides
    assert override.parameter_overrides["recipient"]["title"] == "Customer Email"


def test_step_with_tool_override():
    """Test step with tool override"""
    step = StepBase(
        step_id="email-step",
        step_type="tool",
        name="Send Email",
        config={"tool_name": "send_email"},
        tool_override=ToolOverride(
            title="Welcome Email",
            description="Send welcome email to new user"
        )
    )
    
    assert step.tool_override is not None
    assert step.tool_override.title == "Welcome Email"


def test_workflow_with_connections():
    """Test workflow configuration with connections"""
    workflow = WorkflowConfig(
        name="Test Workflow",
        steps=[
            TriggerStepConfig(
                step_id="trigger-1",
                parameters=TriggerParameters(kind="webhook"),
                position=UIPosition(x=100, y=100)
            ),
            StepBase(
                step_id="step-1",
                step_type="tool",
                name="First Tool",
                position=UIPosition(x=300, y=100),
                dependencies=["trigger-1"],
                config={"tool_name": "tool1"}
            ),
            StepBase(
                step_id="step-2",
                step_type="tool",
                name="Second Tool",
                position=UIPosition(x=500, y=100),
                dependencies=["step-1"],
                config={"tool_name": "tool2"}
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
        ]
    )
    
    assert workflow.name == "Test Workflow"
    assert len(workflow.steps) == 3
    assert len(workflow.connections) == 2
    assert workflow.connections[0].source_step_id == "trigger-1"
    assert workflow.connections[0].target_step_id == "step-1"


def test_workflow_without_connections():
    """Test workflow without connections (backward compatibility)"""
    workflow = WorkflowConfig(
        name="Simple Workflow",
        steps=[
            TriggerStepConfig(
                step_id="trigger-1",
                parameters=TriggerParameters(kind="webhook")
            ),
            StepBase(
                step_id="step-1",
                step_type="tool",
                name="Tool Step",
                dependencies=["trigger-1"],
                config={"tool_name": "my_tool"}
            )
        ]
    )
    
    assert workflow.name == "Simple Workflow"
    assert len(workflow.steps) == 2
    assert len(workflow.connections) == 0  # Empty list by default


def test_complete_workflow_with_all_metadata():
    """Test complete workflow with positions, connections, and tool overrides"""
    workflow = WorkflowConfig(
        name="Customer Onboarding",
        description="Automated customer onboarding workflow",
        version="1.0.0",
        steps=[
            TriggerStepConfig(
                step_id="trigger-1",
                parameters=TriggerParameters(kind="webhook"),
                position=UIPosition(x=100, y=100)
            ),
            StepBase(
                step_id="validate-1",
                step_type="tool",
                name="Validate Data",
                position=UIPosition(x=300, y=100),
                dependencies=["trigger-1"],
                config={"tool_name": "validate_data"},
                tool_override=ToolOverride(
                    title="Customer Data Validation",
                    description="Validate customer information"
                )
            ),
            StepBase(
                step_id="email-1",
                step_type="tool",
                name="Send Email",
                position=UIPosition(x=500, y=100),
                dependencies=["validate-1"],
                config={"tool_name": "send_email"},
                tool_override=ToolOverride(
                    title="Welcome Email",
                    description="Send welcome email to customer",
                    parameter_overrides={
                        "recipient": {
                            "title": "Customer Email",
                            "description": "Email of the new customer"
                        }
                    }
                )
            )
        ],
        connections=[
            StepConnection(
                source_step_id="trigger-1",
                target_step_id="validate-1",
                connection_type="default",
                animated=True
            ),
            StepConnection(
                source_step_id="validate-1",
                target_step_id="email-1",
                source_handle="success",
                connection_type="conditional",
                label="Valid Data",
                animated=True
            )
        ],
        tags=["onboarding", "customer"]
    )
    
    # Validate workflow structure
    assert workflow.name == "Customer Onboarding"
    assert len(workflow.steps) == 3
    assert len(workflow.connections) == 2
    assert len(workflow.tags) == 2
    
    # Validate positions
    assert workflow.steps[0].position.x == 100
    assert workflow.steps[1].position.x == 300
    assert workflow.steps[2].position.x == 500
    
    # Validate tool overrides
    validate_step = workflow.steps[1]
    assert validate_step.tool_override.title == "Customer Data Validation"
    
    email_step = workflow.steps[2]
    assert email_step.tool_override.title == "Welcome Email"
    assert "recipient" in email_step.tool_override.parameter_overrides
    
    # Validate connections
    assert workflow.connections[0].animated is True
    assert workflow.connections[1].source_handle == "success"
    assert workflow.connections[1].label == "Valid Data"


def test_workflow_json_serialization():
    """Test that workflow with UI metadata can be serialized to JSON"""
    workflow = WorkflowConfig(
        name="Test Workflow",
        steps=[
            StepBase(
                step_id="step-1",
                step_type="tool",
                name="My Tool",
                position=UIPosition(x=100, y=200),
                config={"tool_name": "my_tool"},
                tool_override=ToolOverride(
                    title="Custom Title",
                    parameter_overrides={"param1": {"title": "Param 1"}}
                )
            )
        ],
        connections=[
            StepConnection(
                source_step_id="step-1",
                target_step_id="step-2"
            )
        ]
    )
    
    # Serialize to dict
    workflow_dict = workflow.model_dump()
    
    assert workflow_dict["name"] == "Test Workflow"
    assert workflow_dict["steps"][0]["position"]["x"] == 100
    assert workflow_dict["steps"][0]["tool_override"]["title"] == "Custom Title"
    assert len(workflow_dict["connections"]) == 1
    
    # Serialize to JSON string
    workflow_json = workflow.model_dump_json()
    assert isinstance(workflow_json, str)
    assert "Test Workflow" in workflow_json

