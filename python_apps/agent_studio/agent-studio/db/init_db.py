import os
import sys
import uuid
from datetime import datetime

# Add the parent directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from .database import Base, engine, SessionLocal
from . import models, crud, schemas
from prompts import (
    web_agent_system_prompt,
    api_agent_system_prompt,
    data_agent_system_prompt,
    command_agent_system_prompt,
    toshiba_agent_system_prompt,
)


def init_db():
    """
    Initialize the database by creating all tables and adding initial data.
    """
    # Create tables
    Base.metadata.create_all(bind=engine)

    # Create a database session
    db = SessionLocal()

    try:
        # Check if we already have prompts in the database
        existing_prompts = db.query(models.Prompt).first()
        if existing_prompts:
            print("Database already initialized with data.")
            return

        # Add initial prompts
        prompts = [
            web_agent_system_prompt,
            api_agent_system_prompt,
            data_agent_system_prompt,
            command_agent_system_prompt,
            toshiba_agent_system_prompt,
        ]

        for prompt_obj in prompts:
            existing = (
                db.query(models.Prompt)
                .filter(
                    models.Prompt.app_name == prompt_obj.appName,
                    models.Prompt.prompt_label == prompt_obj.prompt_label,
                    models.Prompt.version == prompt_obj.version,
                )
                .first()
            )

            if existing:
                print(f"Prompt {prompt_obj.prompt_label} v{prompt_obj.version} already exists.")
                continue

            try:
                prompt = schemas.PromptCreate(
                    prompt_label=prompt_obj.prompt_label,
                    prompt=prompt_obj.prompt,
                    sha_hash=prompt_obj.sha_hash,
                    unique_label=prompt_obj.uniqueLabel,
                    app_name=prompt_obj.appName,
                    version=prompt_obj.version,
                    ai_model_provider=prompt_obj.modelProvider,
                    ai_model_name=prompt_obj.modelName,
                    tags=prompt_obj.tags,
                    hyper_parameters=prompt_obj.hyper_parameters,
                    variables=prompt_obj.variables,
                )
                crud.create_prompt(db, prompt)
                print(f"Added prompt: {prompt_obj.prompt_label} v{prompt_obj.version}")
            except Exception as e:
                print(f"Error adding prompt {prompt_obj.prompt_label}: {e}")

        print("Database initialized with initial data.")

    finally:
        db.close()


if __name__ == "__main__":
    init_db()
