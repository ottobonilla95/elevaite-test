"""
Seed the database with default prompts from prompts.py

This script reads the prompts defined in prompts.py and inserts them into the database
using the SDK's PromptsService.
"""

import sys
import os

# Add parent directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from sqlmodel import Session
from db.database import engine
from workflow_core_sdk.services.prompts_service import PromptsService
from workflow_core_sdk.db.models import PromptCreate

# Import prompts from prompts.py
from prompts import (
    web_agent_system_prompt,
    api_agent_system_prompt,
    data_agent_system_prompt,
    command_agent_system_prompt,
    hello_world_agent_system_prompt,
    console_printer_agent_system_prompt,
    toshiba_agent_system_prompt,
    mitie_agent_system_prompt,
)


def seed_prompts():
    """Seed the database with default prompts"""
    
    # List of all prompts to seed
    prompts_to_seed = [
        web_agent_system_prompt,
        api_agent_system_prompt,
        data_agent_system_prompt,
        command_agent_system_prompt,
        hello_world_agent_system_prompt,
        console_printer_agent_system_prompt,
        toshiba_agent_system_prompt,
        mitie_agent_system_prompt,
    ]
    
    print("=" * 60)
    print("Seeding Prompts to Database")
    print("=" * 60)
    
    with Session(engine) as session:
        created_count = 0
        skipped_count = 0
        error_count = 0
        
        for prompt_obj in prompts_to_seed:
            try:
                # Convert PromptObject to PromptCreate (SDK format)
                prompt_create = PromptCreate(
                    prompt_label=prompt_obj.prompt_label,
                    unique_label=prompt_obj.uniqueLabel,
                    prompt=prompt_obj.prompt,
                    app_name=prompt_obj.appName,
                    version=prompt_obj.version,
                    ai_model_provider=prompt_obj.modelProvider,
                    ai_model_name=prompt_obj.modelName,
                    tags=prompt_obj.tags,
                    hyper_parameters=prompt_obj.hyper_parameters,
                    variables=prompt_obj.variables,
                )
                
                # Try to create the prompt
                created_prompt = PromptsService.create_prompt(session, prompt_create)
                
                print(f"✅ Created: {prompt_obj.prompt_label} (unique_label: {prompt_obj.uniqueLabel})")
                created_count += 1
                
            except ValueError as e:
                if "already exists" in str(e):
                    print(f"⏭️  Skipped: {prompt_obj.prompt_label} (already exists)")
                    skipped_count += 1
                else:
                    print(f"❌ Error creating {prompt_obj.prompt_label}: {e}")
                    error_count += 1
            except Exception as e:
                print(f"❌ Error creating {prompt_obj.prompt_label}: {e}")
                error_count += 1
    
    print("\n" + "=" * 60)
    print("Seeding Complete!")
    print("=" * 60)
    print(f"✅ Created: {created_count}")
    print(f"⏭️  Skipped: {skipped_count}")
    print(f"❌ Errors: {error_count}")
    print(f"📊 Total: {len(prompts_to_seed)}")
    print("=" * 60)


if __name__ == "__main__":
    seed_prompts()

