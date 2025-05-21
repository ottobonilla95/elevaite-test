import os
import sys
import uuid
import sqlalchemy
import argparse
import requests

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from db.database import SessionLocal, engine
from db import models, schemas, crud

AGENT_CODES = {
    "WebAgent": "w",
    "DataAgent": "d",
    "APIAgent": "a",
    "CommandAgent": "r",
    "HelloWorldAgent": "h",
}

DEFAULT_PROMPTS = [
    {
        "prompt_label": "Web Agent Prompt",
        "prompt": "You are a web agent that can search the web for information.",
        "unique_label": "WebAgentPrompt",
        "app_name": "agent_studio",
        "version": "1.0",
        "ai_model_provider": "OpenAI",
        "ai_model_name": "GPT-4o-mini",
        "tags": ["web", "search"],
        "hyper_parameters": {"temperature": "0.7"},
        "variables": {"search_engine": "google"},
    },
    {
        "prompt_label": "Data Agent Prompt",
        "prompt": "You are a data agent that can query databases and analyze data.",
        "unique_label": "DataAgentPrompt",
        "app_name": "agent_studio",
        "version": "1.0",
        "ai_model_provider": "OpenAI",
        "ai_model_name": "GPT-4o-mini",
        "tags": ["data", "database"],
        "hyper_parameters": {"temperature": "0.7"},
        "variables": {},
    },
    {
        "prompt_label": "API Agent Prompt",
        "prompt": "You are an API agent that can make API calls to external services.",
        "unique_label": "APIAgentPrompt",
        "app_name": "agent_studio",
        "version": "1.0",
        "ai_model_provider": "OpenAI",
        "ai_model_name": "GPT-4o-mini",
        "tags": ["api", "integration"],
        "hyper_parameters": {"temperature": "0.7"},
        "variables": {},
    },
    {
        "prompt_label": "Command Agent Prompt",
        "prompt": "You are a command agent that can coordinate other agents.",
        "unique_label": "CommandAgentPrompt",
        "app_name": "agent_studio",
        "version": "1.0",
        "ai_model_provider": "OpenAI",
        "ai_model_name": "GPT-4o-mini",
        "tags": ["command", "coordination"],
        "hyper_parameters": {"temperature": "0.7"},
        "variables": {},
    },
    {
        "prompt_label": "Hello World Agent Prompt",
        "prompt": "You are a simple Hello World agent. Your only job is to greet users and respond with a friendly hello world message.",
        "unique_label": "HelloWorldAgentPrompt",
        "app_name": "agent_studio",
        "version": "1.0",
        "ai_model_provider": "OpenAI",
        "ai_model_name": "GPT-4o-mini",
        "tags": ["hello", "demo"],
        "hyper_parameters": {"temperature": "0.7"},
        "variables": {"greeting": "Hello, World!"},
    },
]

# Default agents
DEFAULT_AGENTS = [
    {
        "name": "WebAgent",
        "prompt_label": "WebAgentPrompt",
        "persona": "Helper",
        "functions": [],
        "routing_options": {
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        "short_term_memory": True,
        "long_term_memory": False,
        "reasoning": False,
        "input_type": ["text", "voice"],
        "output_type": ["text", "voice"],
        "response_type": "json",
        "max_retries": 3,
        "timeout": None,
        "deployed": False,
        "status": "active",
        "priority": None,
        "failure_strategies": ["retry", "escalate"],
        "collaboration_mode": "single",
    },
    {
        "name": "DataAgent",
        "prompt_label": "DataAgentPrompt",
        "persona": "Helper",
        "functions": [],
        "routing_options": {
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        "short_term_memory": True,
        "long_term_memory": False,
        "reasoning": False,
        "input_type": ["text", "voice"],
        "output_type": ["text", "voice"],
        "response_type": "json",
        "max_retries": 3,
        "timeout": None,
        "deployed": False,
        "status": "active",
        "priority": None,
        "failure_strategies": ["retry", "escalate"],
        "collaboration_mode": "single",
    },
    {
        "name": "APIAgent",
        "prompt_label": "APIAgentPrompt",
        "persona": "Helper",
        "functions": [],
        "routing_options": {
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        "short_term_memory": True,
        "long_term_memory": False,
        "reasoning": False,
        "input_type": ["text", "voice"],
        "output_type": ["text", "voice"],
        "response_type": "json",
        "max_retries": 3,
        "timeout": None,
        "deployed": False,
        "status": "active",
        "priority": None,
        "failure_strategies": ["retry", "escalate"],
        "collaboration_mode": "single",
    },
    {
        "name": "CommandAgent",
        "prompt_label": "CommandAgentPrompt",
        "persona": "Coordinator",
        "functions": [],
        "routing_options": {
            "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
            "respond": "If you think you have the answer, you can stop here.",
            "give_up": "If you think you can't answer the query, you can give up and let the user know.",
        },
        "short_term_memory": True,
        "long_term_memory": False,
        "reasoning": True,
        "input_type": ["text", "voice"],
        "output_type": ["text", "voice"],
        "response_type": "json",
        "max_retries": 3,
        "timeout": None,
        "deployed": False,
        "status": "active",
        "priority": None,
        "failure_strategies": ["retry", "escalate"],
        "collaboration_mode": "single",
    },
    {
        "name": "HelloWorldAgent",
        "prompt_label": "HelloWorldAgentPrompt",
        "persona": "Greeter",
        "functions": [],
        "routing_options": {
            "respond": "Respond with a friendly hello world greeting.",
        },
        "short_term_memory": False,
        "long_term_memory": False,
        "reasoning": False,
        "input_type": ["text", "voice"],
        "output_type": ["text", "voice"],
        "response_type": "json",
        "max_retries": 3,
        "timeout": None,
        "deployed": False,
        "status": "active",
        "priority": None,
        "failure_strategies": ["retry"],
        "collaboration_mode": "single",
    },
]


def initialize_prompts():
    db = SessionLocal()
    try:
        inspector = sqlalchemy.inspect(engine)
        if not inspector.has_table("prompts"):
            print("Error: The prompts table does not exist.")
            print("Please run the database migrations first.")
            return

        added_count = 0
        for prompt_data in DEFAULT_PROMPTS:
            existing_prompt = (
                db.query(models.Prompt)
                .filter(models.Prompt.unique_label == prompt_data["unique_label"])
                .first()
            )

            if existing_prompt is None:
                prompt_create = schemas.PromptCreate(
                    prompt_label=prompt_data["prompt_label"],
                    prompt=prompt_data["prompt"],
                    unique_label=prompt_data["unique_label"],
                    app_name=prompt_data["app_name"],
                    version=prompt_data["version"],
                    ai_model_provider=prompt_data["ai_model_provider"],
                    ai_model_name=prompt_data["ai_model_name"],
                    tags=prompt_data["tags"],
                    hyper_parameters=prompt_data["hyper_parameters"],
                    variables=prompt_data["variables"],
                )

                # Add the prompt to the database
                db_prompt = crud.create_prompt(db=db, prompt=prompt_create)
                print(f"Added prompt '{prompt_data['prompt_label']}' to the database")
                added_count += 1
            else:
                print(
                    f"Prompt '{prompt_data['prompt_label']}' already exists in the database"
                )

        # Commit the changes
        if added_count > 0:
            db.commit()
            print(f"Added {added_count} prompts to the database")
        else:
            print("No new prompts were added to the database")

    except Exception as e:
        db.rollback()
        print(f"Error initializing prompts: {e}")

    finally:
        db.close()


def initialize_agents():
    db = SessionLocal()
    try:
        inspector = sqlalchemy.inspect(engine)
        if not inspector.has_table("agents"):
            print("Error: The agents table does not exist.")
            print("Please run the database migrations first.")
            return

        added_count = 0
        for agent_data in DEFAULT_AGENTS:
            existing_agent = (
                db.query(models.Agent)
                .filter(models.Agent.name == agent_data["name"])
                .first()
            )

            if existing_agent is None:
                prompt = (
                    db.query(models.Prompt)
                    .filter(models.Prompt.unique_label == agent_data["prompt_label"])
                    .first()
                )

                if prompt is None:
                    print(
                        f"Error: Prompt '{agent_data['prompt_label']}' not found in the database"
                    )
                    print("Please run initialize_prompts() first")
                    continue

                deployment_code = AGENT_CODES.get(agent_data["name"])

                prompt_id = uuid.UUID(str(prompt.pid))

                agent_create = schemas.AgentCreate(
                    name=agent_data["name"],
                    system_prompt_id=prompt_id,
                    persona=agent_data["persona"],
                    functions=agent_data["functions"],
                    routing_options=agent_data["routing_options"],
                    short_term_memory=agent_data["short_term_memory"],
                    long_term_memory=agent_data["long_term_memory"],
                    reasoning=agent_data["reasoning"],
                    input_type=agent_data["input_type"],
                    output_type=agent_data["output_type"],
                    response_type=agent_data["response_type"],
                    max_retries=agent_data["max_retries"],
                    timeout=agent_data["timeout"],
                    deployed=agent_data["deployed"],
                    status=agent_data["status"],
                    priority=agent_data["priority"],
                    failure_strategies=agent_data["failure_strategies"],
                    collaboration_mode=agent_data["collaboration_mode"],
                    deployment_code=deployment_code,
                    available_for_deployment=True,
                )

                crud.create_agent(db=db, agent=agent_create)

                print(
                    f"Added agent '{agent_data['name']}' to the database with deployment code '{deployment_code}'"
                )
                added_count += 1
            else:
                existing_code = getattr(existing_agent, "deployment_code", None)
                has_code = (
                    existing_code is not None and str(existing_code).strip() != ""
                )

                deployment_code = AGENT_CODES.get(agent_data["name"])

                if not has_code and deployment_code is not None:
                    setattr(
                        existing_agent,
                        "deployment_code",
                        deployment_code,
                    )
                    setattr(existing_agent, "available_for_deployment", True)
                    print(
                        f"Updated agent '{agent_data['name']}' with deployment code '{deployment_code}'"
                    )
                    added_count += 1
                else:
                    print(
                        f"Agent '{agent_data['name']}' already exists in the database"
                    )

        if added_count > 0:
            db.commit()
            print(f"Added or updated {added_count} agents in the database")
        else:
            print("No new agents were added to the database")

    except Exception as e:
        db.rollback()
        print(f"Error initializing agents: {e}")

    finally:
        db.close()


def check_server_health(server_url):
    try:
        health_url = f"{server_url}/hc"
        response = requests.get(health_url, timeout=5)
        if response.status_code == 200:
            return True, None
        return False, f"Server returned status code {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, str(e)


def initialize_all(server_url="http://localhost:8000"):
    server_ok, error_msg = check_server_health(server_url)

    if not server_ok:
        print(f"ERROR: Cannot connect to server at {server_url}")
        print(f"Reason: {error_msg}")

        print(
            "Start the server and rerun the script or use --server-url to specify a different address"
        )
        return

    print("Initializing prompts...")
    initialize_prompts()

    print("\nInitializing agents...")
    initialize_agents()

    print("\nInitialization complete!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Initialize the database with agents and prompts"
    )
    parser.add_argument(
        "--server-url",
        default="http://localhost:8000",
        help="URL of the agent_studio server (default: http://localhost:8000)",
    )

    args = parser.parse_args()

    initialize_all(server_url=args.server_url)
