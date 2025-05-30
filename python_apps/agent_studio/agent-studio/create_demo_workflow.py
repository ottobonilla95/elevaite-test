#!/usr/bin/env python3
"""
Script to create a demo workflow in the database for testing the frontend workflow management feature.
"""

import sys
import os
from datetime import datetime
from sqlalchemy.orm import Session

# Add the current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from db.database import get_db, engine
from db import models, crud, schemas

def create_demo_workflow():
    """Create a demo workflow with sample agents and connections."""
    
    # Get database session
    db = next(get_db())
    
    try:
        print("Creating demo workflow...")
        
        # First, let's check if we have any agents in the database
        agents = crud.get_available_agents(db)
        print(f"Found {len(agents)} available agents in database")
        
        if len(agents) < 2:
            print("Not enough agents in database. Creating sample agents first...")
            
            # Create sample agents if they don't exist
            sample_agents = [
                {
                    "name": "Router Agent",
                    "agent_type": "router",
                    "description": "Routes user queries to appropriate specialized agents",
                    "functions": [{"name": "route_query", "description": "Route user query"}],
                    "routing_options": {"default": "web_search"},
                    "available_for_deployment": True,
                    "deployment_code": "R"
                },
                {
                    "name": "Web Search Agent", 
                    "agent_type": "web_search",
                    "description": "Searches the web for information",
                    "functions": [{"name": "web_search", "description": "Search the web"}],
                    "routing_options": {},
                    "available_for_deployment": True,
                    "deployment_code": "W"
                },
                {
                    "name": "Data Analysis Agent",
                    "agent_type": "data", 
                    "description": "Analyzes and processes data",
                    "functions": [{"name": "analyze_data", "description": "Analyze data"}],
                    "routing_options": {},
                    "available_for_deployment": True,
                    "deployment_code": "D"
                }
            ]
            
            # Create system prompts for the agents
            for i, agent_data in enumerate(sample_agents):
                # Create system prompt
                prompt_data = schemas.PromptCreate(
                    prompt_label=f"{agent_data['name']} System Prompt",
                    prompt=f"You are a {agent_data['name'].lower()}. {agent_data['description']}",
                    app_name="command_agent",
                    version="1.0",
                    ai_model_provider="openai",
                    ai_model_name="gpt-4",
                    tags=[agent_data['agent_type']]
                )
                
                system_prompt = crud.create_prompt(db, prompt_data)
                print(f"Created system prompt: {system_prompt.prompt_label}")
                
                # Create agent
                agent_create_data = schemas.AgentCreate(
                    name=agent_data['name'],
                    agent_type=agent_data['agent_type'],
                    description=agent_data['description'],
                    system_prompt_id=system_prompt.pid,
                    functions=agent_data['functions'],
                    routing_options=agent_data['routing_options'],
                    available_for_deployment=agent_data['available_for_deployment'],
                    deployment_code=agent_data['deployment_code']
                )
                
                agent = crud.create_agent(db, agent_create_data)
                print(f"Created agent: {agent.name}")
        
        # Get available agents again
        agents = crud.get_available_agents(db)
        print(f"Now have {len(agents)} available agents")
        
        # Create demo workflow
        workflow_data = schemas.WorkflowCreate(
            name="Customer Support Demo Workflow",
            description="A demo workflow that handles customer inquiries using web search and data analysis",
            version="1.0",
            created_by="demo_script",
            is_active=True,
            tags=["demo", "customer_support"],
            configuration={
                "demo": True,
                "created_by_script": True,
                "purpose": "testing_frontend"
            }
        )
        
        workflow = crud.create_workflow(db, workflow_data)
        print(f"Created workflow: {workflow.name} (ID: {workflow.workflow_id})")
        
        # Add agents to workflow with positions
        workflow_agents = []
        agent_positions = [
            {"x": 100, "y": 100},  # Router Agent
            {"x": 300, "y": 50},   # Web Search Agent  
            {"x": 300, "y": 150}   # Data Analysis Agent
        ]
        
        for i, agent in enumerate(agents[:3]):  # Use first 3 agents
            if i < len(agent_positions):
                workflow_agent_data = schemas.WorkflowAgentCreate(
                    workflow_id=workflow.workflow_id,
                    agent_id=agent.agent_id,
                    position_x=agent_positions[i]["x"],
                    position_y=agent_positions[i]["y"],
                    node_id=f"node-{agent.agent_id}",
                    agent_config={"demo": True}
                )
                
                workflow_agent = crud.create_workflow_agent(db, workflow_agent_data)
                workflow_agents.append(workflow_agent)
                print(f"Added agent {agent.name} to workflow at position ({agent_positions[i]['x']}, {agent_positions[i]['y']})")
        
        # Create connections between agents
        if len(workflow_agents) >= 2:
            # Router -> Web Search
            connection1_data = schemas.WorkflowConnectionCreate(
                workflow_id=workflow.workflow_id,
                source_agent_id=workflow_agents[0].agent_id,  # Router
                target_agent_id=workflow_agents[1].agent_id,  # Web Search
                connection_type="default",
                priority=1
            )
            
            connection1 = crud.create_workflow_connection(db, connection1_data)
            print(f"Created connection: {agents[0].name} -> {agents[1].name}")
            
            if len(workflow_agents) >= 3:
                # Router -> Data Analysis
                connection2_data = schemas.WorkflowConnectionCreate(
                    workflow_id=workflow.workflow_id,
                    source_agent_id=workflow_agents[0].agent_id,  # Router
                    target_agent_id=workflow_agents[2].agent_id,  # Data Analysis
                    connection_type="conditional",
                    priority=2,
                    conditions={"query_type": "data_analysis"}
                )
                
                connection2 = crud.create_workflow_connection(db, connection2_data)
                print(f"Created connection: {agents[0].name} -> {agents[2].name}")
        
        # Create a deployment for the workflow
        deployment_data = schemas.WorkflowDeploymentCreate(
            workflow_id=workflow.workflow_id,
            environment="demo",
            deployment_name="customer-support-demo",
            deployed_by="demo_script",
            runtime_config={"demo_mode": True}
        )
        
        deployment = crud.create_workflow_deployment(db, deployment_data)
        print(f"Created deployment: {deployment.deployment_name} (ID: {deployment.deployment_id})")
        
        print("\n✅ Demo workflow created successfully!")
        print(f"Workflow ID: {workflow.workflow_id}")
        print(f"Workflow Name: {workflow.name}")
        print(f"Agents: {len(workflow_agents)}")
        print(f"Connections: {2 if len(workflow_agents) >= 3 else 1 if len(workflow_agents) >= 2 else 0}")
        print(f"Deployment: {deployment.deployment_name}")
        
        return workflow
        
    except Exception as e:
        print(f"Error creating demo workflow: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def create_second_demo_workflow():
    """Create a second demo workflow for more testing."""
    
    db = next(get_db())
    
    try:
        print("\nCreating second demo workflow...")
        
        # Get available agents
        agents = crud.get_available_agents(db)
        
        # Create second workflow
        workflow_data = schemas.WorkflowCreate(
            name="Data Processing Pipeline",
            description="A workflow for processing and analyzing large datasets",
            version="1.0", 
            created_by="demo_script",
            is_active=True,
            tags=["demo", "data_processing", "analytics"],
            configuration={
                "demo": True,
                "pipeline_type": "data_processing"
            }
        )
        
        workflow = crud.create_workflow(db, workflow_data)
        print(f"Created workflow: {workflow.name} (ID: {workflow.workflow_id})")
        
        # Add agents with different positions
        if len(agents) >= 2:
            positions = [
                {"x": 150, "y": 200},  # First agent
                {"x": 400, "y": 200}   # Second agent
            ]
            
            for i, agent in enumerate(agents[:2]):
                workflow_agent_data = schemas.WorkflowAgentCreate(
                    workflow_id=workflow.workflow_id,
                    agent_id=agent.agent_id,
                    position_x=positions[i]["x"],
                    position_y=positions[i]["y"],
                    node_id=f"node-{agent.agent_id}-v2",
                    agent_config={"demo": True, "version": 2}
                )
                
                crud.create_workflow_agent(db, workflow_agent_data)
                print(f"Added agent {agent.name} to workflow")
        
        print(f"✅ Second demo workflow created: {workflow.name}")
        return workflow
        
    except Exception as e:
        print(f"Error creating second demo workflow: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Creating demo workflows for testing...")
    
    try:
        # Create the database tables if they don't exist
        models.Base.metadata.create_all(bind=engine)
        print("Database tables ensured to exist")
        
        # Create demo workflows
        workflow1 = create_demo_workflow()
        workflow2 = create_second_demo_workflow()
        
        print(f"\n🎉 Successfully created {2} demo workflows!")
        print("\nYou can now test the frontend workflow management features:")
        print("1. Open the frontend and go to the Workflows tab")
        print("2. You should see the demo workflows listed")
        print("3. Try loading, editing, and saving workflows")
        
    except Exception as e:
        print(f"❌ Failed to create demo workflows: {e}")
        sys.exit(1)
