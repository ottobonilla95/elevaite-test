#!/usr/bin/env python3
"""
Registration script for ToshibaAgent in the database
This script registers the ToshibaAgent with its prompt and configuration
"""

import os
import sys
import uuid
from datetime import datetime

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from db.database import SessionLocal
from db import crud, schemas, models
from prompts import toshiba_agent_system_prompt
from db.fixtures.default_data import AGENT_CODES


def register_toshiba_agent():
    """
    Register ToshibaAgent in the database with its prompt and configuration
    """
    db = SessionLocal()
    
    try:
        print("=== Registering ToshibaAgent ===")
        
        # Step 1: Check if ToshibaAgent prompt already exists
        existing_prompt = (
            db.query(models.Prompt)
            .filter(
                models.Prompt.app_name == toshiba_agent_system_prompt.appName,
                models.Prompt.prompt_label == toshiba_agent_system_prompt.prompt_label,
                models.Prompt.version == toshiba_agent_system_prompt.version,
            )
            .first()
        )
        
        if existing_prompt:
            print(f"✓ ToshibaAgent prompt already exists: {existing_prompt.pid}")
            prompt_id = existing_prompt.pid
        else:
            # Create ToshibaAgent prompt
            print("Creating ToshibaAgent prompt...")
            prompt_data = schemas.PromptCreate(
                prompt_label=toshiba_agent_system_prompt.prompt_label,
                prompt=toshiba_agent_system_prompt.prompt,
                sha_hash=toshiba_agent_system_prompt.sha_hash,
                unique_label=toshiba_agent_system_prompt.uniqueLabel,
                app_name=toshiba_agent_system_prompt.appName,
                version=toshiba_agent_system_prompt.version,
                ai_model_provider=toshiba_agent_system_prompt.modelProvider,
                ai_model_name=toshiba_agent_system_prompt.modelName,
                tags=toshiba_agent_system_prompt.tags,
                hyper_parameters=toshiba_agent_system_prompt.hyper_parameters,
                variables=toshiba_agent_system_prompt.variables,
            )
            
            db_prompt = crud.create_prompt(db, prompt_data)
            prompt_id = db_prompt.pid
            print(f"✓ Created ToshibaAgent prompt: {prompt_id}")
        
        # Step 2: Check if ToshibaAgent already exists
        existing_agent = crud.get_agent_by_name(db, "ToshibaAgent")
        
        if existing_agent:
            print(f"✓ ToshibaAgent already exists: {existing_agent.agent_id}")
            print("Updating existing agent configuration...")
            
            # Update the existing agent
            agent_update = schemas.AgentUpdate(
                agent_type="toshiba",
                description="Specialized agent for Toshiba parts, assemblies, and technical information",
                system_prompt_id=prompt_id,
                persona="Toshiba Expert",
                functions=[],  # Will be populated with actual tool schemas
                routing_options={
                    "ask": "If you think you need to ask more information or context from the user to answer the question.",
                    "continue": "If you think you have the answer, you can stop here.",
                    "give_up": "If you think you can't answer the query, you can give up and let the user know."
                },
                short_term_memory=True,
                long_term_memory=False,
                reasoning=False,
                input_type=["text", "voice"],
                output_type=["text", "voice"],
                response_type="json",
                max_retries=3,
                timeout=None,
                deployed=False,
                status="active",
                priority=None,
                failure_strategies=["retry", "escalate"],
                collaboration_mode="single",
                available_for_deployment=True,
                deployment_code=AGENT_CODES.get("ToshibaAgent", "t")
            )
            
            updated_agent = crud.update_agent(db, existing_agent.agent_id, agent_update)
            if updated_agent:
                print(f"✓ Updated ToshibaAgent: {updated_agent.agent_id}")
                agent_id = updated_agent.agent_id
            else:
                print("✗ Failed to update ToshibaAgent")
                return False
        else:
            # Create new ToshibaAgent
            print("Creating new ToshibaAgent...")
            agent_data = schemas.AgentCreate(
                name="ToshibaAgent",
                agent_type="toshiba",
                description="Specialized agent for Toshiba parts, assemblies, and technical information",
                parent_agent_id=None,
                system_prompt_id=prompt_id,
                persona="Toshiba Expert",
                functions=[],  # Will be populated with actual tool schemas
                routing_options={
                    "ask": "If you think you need to ask more information or context from the user to answer the question.",
                    "continue": "If you think you have the answer, you can stop here.",
                    "give_up": "If you think you can't answer the query, you can give up and let the user know."
                },
                short_term_memory=True,
                long_term_memory=False,
                reasoning=False,
                input_type=["text", "voice"],
                output_type=["text", "voice"],
                response_type="json",
                max_retries=3,
                timeout=None,
                deployed=False,
                status="active",
                priority=None,
                failure_strategies=["retry", "escalate"],
                collaboration_mode="single",
                available_for_deployment=True,
                deployment_code=AGENT_CODES.get("ToshibaAgent", "t")
            )
            
            db_agent = crud.create_agent(db, agent_data)
            agent_id = db_agent.agent_id
            print(f"✓ Created ToshibaAgent: {agent_id}")
        
        # Step 3: Verify registration
        print("\n=== Verification ===")
        registered_agent = crud.get_agent_by_name(db, "ToshibaAgent")
        if registered_agent:
            print(f"✓ ToshibaAgent successfully registered")
            print(f"  - Agent ID: {registered_agent.agent_id}")
            print(f"  - Agent Type: {registered_agent.agent_type}")
            print(f"  - Description: {registered_agent.description}")
            print(f"  - Deployment Code: {registered_agent.deployment_code}")
            print(f"  - Available for Deployment: {registered_agent.available_for_deployment}")
            print(f"  - Status: {registered_agent.status}")
            
            # Check prompt association
            if registered_agent.system_prompt:
                print(f"  - System Prompt: {registered_agent.system_prompt.prompt_label}")
            else:
                print("  - ⚠️  No system prompt associated")
            
            return True
        else:
            print("✗ Failed to verify ToshibaAgent registration")
            return False
            
    except Exception as e:
        print(f"✗ Error registering ToshibaAgent: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def check_toshiba_agent_status():
    """Check if ToshibaAgent is already registered"""
    db = SessionLocal()
    
    try:
        agent = crud.get_agent_by_name(db, "ToshibaAgent")
        if agent:
            print(f"ToshibaAgent is registered with ID: {agent.agent_id}")
            print(f"Status: {agent.status}")
            print(f"Available for deployment: {agent.available_for_deployment}")
            return True
        else:
            print("ToshibaAgent is not registered")
            return False
    finally:
        db.close()


def main():
    """Main function"""
    print("ToshibaAgent Registration Tool")
    print("=" * 40)
    
    # Check current status
    print("Checking current status...")
    is_registered = check_toshiba_agent_status()
    
    if not is_registered:
        print("\nRegistering ToshibaAgent...")
        success = register_toshiba_agent()
        if success:
            print("\n🎉 ToshibaAgent registration completed successfully!")
        else:
            print("\n❌ ToshibaAgent registration failed!")
            sys.exit(1)
    else:
        print("\nToshibaAgent is already registered.")
        response = input("Do you want to update the configuration? (y/N): ")
        if response.lower() in ['y', 'yes']:
            success = register_toshiba_agent()
            if success:
                print("\n🎉 ToshibaAgent configuration updated successfully!")
            else:
                print("\n❌ ToshibaAgent update failed!")
                sys.exit(1)
        else:
            print("No changes made.")
    
    print("\n=== Next Steps ===")
    print("1. ToshibaAgent is now available for use in workflows")
    print("2. Create single-agent workflows using agent_type: 'ToshibaAgent'")
    print("3. Deploy workflows with ToshibaAgent for direct execution")
    print("4. Test the agent using the test_toshiba_single_agent.py script")


if __name__ == "__main__":
    main()
