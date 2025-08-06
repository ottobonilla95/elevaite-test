#!/usr/bin/env python3
"""
One-time script to register a test hybrid workflow in the database.

This creates a persistent hybrid workflow that can be used for testing
all three endpoints (sync, async, streaming) without recreating it each time.
"""

import sys
import os
import uuid
from datetime import datetime

# Add the parent directory to the path so we can import from the agent-studio
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db.database import SessionLocal
from db import crud, models
from sqlalchemy.orm import Session


def create_test_hybrid_workflow(db: Session):
    """Create a test hybrid workflow with conditional routing."""
    
    # Define the hybrid workflow configuration
    hybrid_config = {
        "workflow_type": "hybrid",
        "agents": [
            {
                "agent_id": "tokenizer_agent",
                "agent_type": "DeterministicWorkflowAgent",
                "name": "Document Tokenizer",
                "config": {
                    "workflow_type": "deterministic",
                    "workflow_name": "Document Processing Pipeline",
                    "execution_pattern": "sequential",
                    "steps": [
                        {
                            "step_id": "file_input",
                            "step_type": "data_input",
                            "step_name": "File Input Processing",
                            "config": {
                                "input_validation": ["file_required"],
                                "supported_formats": ["pdf", "txt", "docx"]
                            }
                        },
                        {
                            "step_id": "text_extraction",
                            "step_type": "data_processing", 
                            "step_name": "Text Extraction",
                            "config": {
                                "chunk_size": 1000,
                                "overlap": 200
                            }
                        },
                        {
                            "step_id": "vector_storage",
                            "step_type": "data_output",
                            "step_name": "Vector Database Storage",
                            "config": {
                                "vector_db": "qdrant",
                                "collection": "documents"
                            }
                        }
                    ]
                }
            },
            {
                "agent_id": "router_agent",
                "agent_type": "CommandAgent",
                "name": "Query Router",
                "config": {
                    "system_prompt": "You are a query routing agent that can access processed documents.",
                    "tools": ["document_search", "general_knowledge"]
                }
            }
        ],
        "connections": [
            {
                "source_agent_id": "tokenizer_agent",
                "target_agent_id": "router_agent",
                "connection_type": "conditional"
            }
        ],
        "execution_logic": {
            "routing_rules": [
                {
                    "condition": "input.has_file",
                    "action": "execute_tokenizer_then_router",
                    "flow": ["tokenizer_agent", "router_agent"],
                    "description": "If input contains a file, process it through tokenizer first"
                },
                {
                    "condition": "!input.has_file",
                    "action": "execute_router_directly", 
                    "flow": ["router_agent"],
                    "description": "If no file, route directly to query agent"
                }
            ],
            "default_action": "execute_router_directly"
        }
    }
    
    # Create the workflow
    workflow_data = {
        "name": "Test Hybrid Document Processing Workflow",
        "description": "Test workflow for hybrid deterministic + AI agent execution with conditional routing",
        "version": "1.0.0",
        "configuration": hybrid_config,
        "created_by": "test_system",
        "is_deployed": False
    }
    
    # Check if workflow already exists
    existing = crud.workflows.get_workflow_by_name(
        db, workflow_data["name"], workflow_data["version"]
    )
    
    if existing:
        print(f"✅ Hybrid workflow already exists: {existing.workflow_id}")
        return existing.workflow_id
    
    # Create new workflow
    workflow = crud.workflows.create_workflow(db, workflow_data)
    print(f"✅ Created hybrid workflow: {workflow.workflow_id}")
    print(f"   Name: {workflow.name}")
    print(f"   Description: {workflow.description}")
    print(f"   Agents: {len(hybrid_config['agents'])}")
    print(f"   Routing Rules: {len(hybrid_config['execution_logic']['routing_rules'])}")
    
    return workflow.workflow_id


def create_test_deterministic_workflow(db: Session):
    """Create a test pure deterministic workflow."""
    
    deterministic_config = {
        "workflow_type": "deterministic",
        "workflow_name": "Test Audit Workflow",
        "description": "Simple deterministic workflow for testing",
        "execution_pattern": "sequential",
        "steps": [
            {
                "step_id": "audit_input",
                "step_type": "data_input",
                "step_name": "Audit Input Request",
                "config": {
                    "validation_rules": ["required_fields"],
                    "audit_level": "detailed"
                }
            },
            {
                "step_id": "validate_request",
                "step_type": "validation",
                "step_name": "Validate Request",
                "config": {
                    "validation_schema": "standard",
                    "strict_mode": True
                }
            },
            {
                "step_id": "process_data",
                "step_type": "data_processing",
                "step_name": "Process Request Data",
                "config": {
                    "processing_mode": "standard",
                    "output_format": "json"
                }
            },
            {
                "step_id": "audit_output",
                "step_type": "data_output",
                "step_name": "Generate Audit Output",
                "config": {
                    "output_destination": "audit_log",
                    "include_metadata": True
                }
            }
        ]
    }
    
    workflow_data = {
        "name": "Test Pure Deterministic Workflow",
        "description": "Test workflow for pure deterministic execution",
        "version": "1.0.0", 
        "configuration": deterministic_config,
        "created_by": "test_system",
        "is_deployed": False
    }
    
    # Check if workflow already exists
    existing = crud.workflows.get_workflow_by_name(
        db, workflow_data["name"], workflow_data["version"]
    )
    
    if existing:
        print(f"✅ Deterministic workflow already exists: {existing.workflow_id}")
        return existing.workflow_id
    
    # Create new workflow
    workflow = crud.workflows.create_workflow(db, workflow_data)
    print(f"✅ Created deterministic workflow: {workflow.workflow_id}")
    print(f"   Name: {workflow.name}")
    print(f"   Steps: {len(deterministic_config['steps'])}")
    
    return workflow.workflow_id


def main():
    """Register test workflows in the database."""
    print("🔧 Registering test workflows in database...")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        # Create hybrid workflow
        print("\n📋 Creating Hybrid Workflow...")
        hybrid_id = create_test_hybrid_workflow(db)
        
        # Create deterministic workflow  
        print("\n📋 Creating Deterministic Workflow...")
        deterministic_id = create_test_deterministic_workflow(db)
        
        # Commit changes
        db.commit()
        
        print("\n🎉 Test workflows registered successfully!")
        print("=" * 60)
        print(f"Hybrid Workflow ID: {hybrid_id}")
        print(f"Deterministic Workflow ID: {deterministic_id}")
        print("\nThese workflows can now be used for testing all endpoints:")
        print("- POST /api/workflows/{id}/execute (sync)")
        print("- POST /api/workflows/{id}/execute/async (async)")
        print("- POST /api/workflows/{id}/stream (streaming)")
        
    except Exception as e:
        print(f"❌ Error registering workflows: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()
