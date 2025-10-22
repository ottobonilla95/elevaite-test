"""
Example: Workflow UI Metadata

This example demonstrates how to create workflows with UI metadata including:
- Step positions (x, y coordinates for canvas)
- Step connections (visual edges between steps)
- Tool overrides (workflow-specific tool customization)
"""

import json
from workflow_core_sdk.schemas.workflows import (
    WorkflowConfig,
    StepBase,
    TriggerStepConfig,
    TriggerParameters,
    UIPosition,
    StepConnection,
    ToolOverride,
)


def example_1_basic_positions():
    """Example 1: Basic workflow with step positions"""
    print("\n" + "="*80)
    print("EXAMPLE 1: Basic Workflow with Step Positions")
    print("="*80 + "\n")
    
    workflow = WorkflowConfig(
        name="Simple Positioned Workflow",
        description="A workflow with steps positioned on a canvas",
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
                position=UIPosition(x=350, y=200),
                dependencies=["trigger-1"],
                config={"tool_name": "process_data"}
            ),
            StepBase(
                step_id="step-2",
                step_type="tool",
                name="Send Result",
                position=UIPosition(x=600, y=200),
                dependencies=["step-1"],
                config={"tool_name": "send_result"}
            )
        ]
    )
    
    print("Workflow created with positioned steps:")
    for step in workflow.steps:
        if step.position:
            print(f"  - {step.name or step.step_id}: ({step.position.x}, {step.position.y})")
    
    return workflow


def example_2_with_connections():
    """Example 2: Workflow with visual connections"""
    print("\n" + "="*80)
    print("EXAMPLE 2: Workflow with Visual Connections")
    print("="*80 + "\n")
    
    workflow = WorkflowConfig(
        name="Connected Workflow",
        description="A workflow with explicit visual connections",
        steps=[
            TriggerStepConfig(
                step_id="trigger-1",
                parameters=TriggerParameters(kind="webhook"),
                position=UIPosition(x=100, y=200)
            ),
            StepBase(
                step_id="validate-1",
                step_type="tool",
                name="Validate Input",
                position=UIPosition(x=300, y=200),
                dependencies=["trigger-1"],
                config={"tool_name": "validate"}
            ),
            StepBase(
                step_id="process-success",
                step_type="tool",
                name="Process Valid Data",
                position=UIPosition(x=500, y=150),
                dependencies=["validate-1"],
                config={"tool_name": "process"}
            ),
            StepBase(
                step_id="handle-error",
                step_type="tool",
                name="Handle Invalid Data",
                position=UIPosition(x=500, y=250),
                dependencies=["validate-1"],
                config={"tool_name": "handle_error"}
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
                target_step_id="process-success",
                source_handle="success",
                target_handle="input",
                connection_type="conditional",
                label="Valid",
                animated=True
            ),
            StepConnection(
                source_step_id="validate-1",
                target_step_id="handle-error",
                source_handle="error",
                target_handle="input",
                connection_type="error",
                label="Invalid",
                animated=False
            )
        ]
    )
    
    print("Workflow connections:")
    for conn in workflow.connections:
        label = f" ({conn.label})" if conn.label else ""
        print(f"  - {conn.source_step_id} → {conn.target_step_id}{label} [{conn.connection_type}]")
    
    return workflow


def example_3_tool_overrides():
    """Example 3: Workflow with tool overrides"""
    print("\n" + "="*80)
    print("EXAMPLE 3: Workflow with Tool Overrides")
    print("="*80 + "\n")
    
    workflow = WorkflowConfig(
        name="Customer Onboarding",
        description="Onboard new customers with customized tool labels",
        steps=[
            TriggerStepConfig(
                step_id="trigger-1",
                parameters=TriggerParameters(kind="webhook"),
                position=UIPosition(x=100, y=200)
            ),
            StepBase(
                step_id="validate-customer",
                step_type="tool",
                name="Validate Customer",
                position=UIPosition(x=300, y=200),
                dependencies=["trigger-1"],
                config={"tool_name": "validate_data"},
                tool_override=ToolOverride(
                    title="Customer Data Validation",
                    description="Validate customer registration information including email, phone, and address",
                    parameter_overrides={
                        "data": {
                            "title": "Customer Information",
                            "description": "Customer registration data to validate"
                        },
                        "schema": {
                            "title": "Validation Rules",
                            "description": "Schema defining required customer fields"
                        }
                    }
                )
            ),
            StepBase(
                step_id="create-account",
                step_type="tool",
                name="Create Account",
                position=UIPosition(x=500, y=200),
                dependencies=["validate-customer"],
                config={"tool_name": "create_user_account"},
                tool_override=ToolOverride(
                    title="Customer Account Creation",
                    description="Create a new customer account in the system"
                )
            ),
            StepBase(
                step_id="send-welcome",
                step_type="tool",
                name="Send Welcome Email",
                position=UIPosition(x=700, y=200),
                dependencies=["create-account"],
                config={"tool_name": "send_email"},
                tool_override=ToolOverride(
                    title="Welcome Email Notification",
                    description="Send personalized welcome email to new customer",
                    parameter_overrides={
                        "recipient": {
                            "title": "New Customer Email",
                            "description": "Email address of the newly registered customer",
                            "placeholder": "customer@example.com"
                        },
                        "subject": {
                            "title": "Welcome Email Subject",
                            "description": "Subject line for the welcome email"
                        },
                        "body": {
                            "title": "Email Content",
                            "description": "Personalized welcome message content"
                        }
                    }
                )
            )
        ],
        connections=[
            StepConnection(
                source_step_id="trigger-1",
                target_step_id="validate-customer",
                animated=True
            ),
            StepConnection(
                source_step_id="validate-customer",
                target_step_id="create-account",
                source_handle="success",
                connection_type="conditional",
                label="Valid Data"
            ),
            StepConnection(
                source_step_id="create-account",
                target_step_id="send-welcome",
                connection_type="default"
            )
        ],
        tags=["onboarding", "customer", "email"]
    )
    
    print("Tool overrides in workflow:")
    for step in workflow.steps:
        if step.tool_override:
            print(f"\n  Step: {step.name}")
            print(f"    Override Title: {step.tool_override.title}")
            print(f"    Override Description: {step.tool_override.description}")
            if step.tool_override.parameter_overrides:
                print(f"    Parameter Overrides:")
                for param_name, override in step.tool_override.parameter_overrides.items():
                    print(f"      - {param_name}: {override.get('title', 'N/A')}")
    
    return workflow


def example_4_complete_workflow():
    """Example 4: Complete workflow with all metadata"""
    print("\n" + "="*80)
    print("EXAMPLE 4: Complete Workflow with All Metadata")
    print("="*80 + "\n")
    
    workflow = WorkflowConfig(
        name="Order Processing Pipeline",
        description="Complete order processing with validation, payment, and fulfillment",
        version="2.0.0",
        steps=[
            TriggerStepConfig(
                step_id="order-trigger",
                parameters=TriggerParameters(kind="webhook"),
                position=UIPosition(x=50, y=300)
            ),
            StepBase(
                step_id="validate-order",
                step_type="tool",
                name="Validate Order",
                position=UIPosition(x=250, y=300),
                dependencies=["order-trigger"],
                config={"tool_name": "validate_order"},
                tool_override=ToolOverride(
                    title="Order Validation",
                    description="Validate order items, quantities, and customer information"
                )
            ),
            StepBase(
                step_id="check-inventory",
                step_type="tool",
                name="Check Inventory",
                position=UIPosition(x=450, y=250),
                dependencies=["validate-order"],
                config={"tool_name": "check_stock"}
            ),
            StepBase(
                step_id="process-payment",
                step_type="tool",
                name="Process Payment",
                position=UIPosition(x=450, y=350),
                dependencies=["validate-order"],
                config={"tool_name": "charge_payment"}
            ),
            StepBase(
                step_id="fulfill-order",
                step_type="tool",
                name="Fulfill Order",
                position=UIPosition(x=650, y=300),
                dependencies=["check-inventory", "process-payment"],
                config={"tool_name": "create_shipment"}
            ),
            StepBase(
                step_id="send-confirmation",
                step_type="tool",
                name="Send Confirmation",
                position=UIPosition(x=850, y=300),
                dependencies=["fulfill-order"],
                config={"tool_name": "send_email"},
                tool_override=ToolOverride(
                    title="Order Confirmation Email",
                    description="Send order confirmation with tracking information"
                )
            )
        ],
        connections=[
            StepConnection(source_step_id="order-trigger", target_step_id="validate-order", animated=True),
            StepConnection(source_step_id="validate-order", target_step_id="check-inventory", 
                         source_handle="success", connection_type="conditional", label="Valid Order"),
            StepConnection(source_step_id="validate-order", target_step_id="process-payment",
                         source_handle="success", connection_type="conditional", label="Valid Order"),
            StepConnection(source_step_id="check-inventory", target_step_id="fulfill-order",
                         source_handle="available", connection_type="conditional", label="In Stock"),
            StepConnection(source_step_id="process-payment", target_step_id="fulfill-order",
                         source_handle="success", connection_type="conditional", label="Payment OK"),
            StepConnection(source_step_id="fulfill-order", target_step_id="send-confirmation")
        ],
        tags=["orders", "ecommerce", "payment"],
        timeout_seconds=300
    )
    
    print(f"Workflow: {workflow.name}")
    print(f"Steps: {len(workflow.steps)}")
    print(f"Connections: {len(workflow.connections)}")
    print(f"Tags: {', '.join(workflow.tags)}")
    
    return workflow


def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("WORKFLOW UI METADATA EXAMPLES")
    print("="*80)
    
    # Run examples
    workflow1 = example_1_basic_positions()
    workflow2 = example_2_with_connections()
    workflow3 = example_3_tool_overrides()
    workflow4 = example_4_complete_workflow()
    
    # Show JSON output for one workflow
    print("\n" + "="*80)
    print("JSON OUTPUT (Example 3)")
    print("="*80 + "\n")
    print(json.dumps(workflow3.model_dump(), indent=2))
    
    print("\n" + "="*80)
    print("All examples completed successfully!")
    print("="*80 + "\n")


if __name__ == "__main__":
    main()

