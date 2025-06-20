import os
import sys

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

def init_tool_categories(db):
    categories = [
        {
            "name": "Search & Retrieval",
            "description": "Tools for searching and retrieving information",
            "icon": "🔍",
            "color": "#3B82F6",
        },
        {
            "name": "Data Processing",
            "description": "Tools for processing and manipulating data",
            "icon": "⚙️",
            "color": "#10B981",
        },
        {
            "name": "Web & API",
            "description": "Tools for web scraping and API interactions",
            "icon": "🌐",
            "color": "#8B5CF6",
        },
        {"name": "Utilities", "description": "General utility tools", "icon": "🛠️", "color": "#F59E0B"},
        {
            "name": "Customer Service",
            "description": "Tools for customer service operations",
            "icon": "👥",
            "color": "#EF4444",
        },
    ]

    created_categories = {}

    for cat_data in categories:
        existing = crud.get_tool_category_by_name(db, cat_data["name"])
        if existing:
            print(f"✓ Category '{cat_data['name']}' already exists")
            created_categories[cat_data["name"]] = existing
        else:
            category = crud.create_tool_category(db, schemas.ToolCategoryCreate(**cat_data))
            created_categories[cat_data["name"]] = category
            print(f"✓ Created category: {cat_data['name']}")

    return created_categories

def init_tools(db, categories):
    try:
        from agents.tools import tool_store, tool_schemas
    except ImportError:
        print("⚠ Could not import tool_store and tool_schemas, skipping tool initialization")
        return

    tool_categories = {
        "web_search": "Search & Retrieval",
        "query_retriever2": "Search & Retrieval",
        "url_to_markdown": "Web & API",
        "weather_forecast": "Web & API",
        "get_customer_order": "Customer Service",
        "get_customer_location": "Customer Service",
        "add_customer": "Customer Service",
        "add_numbers": "Utilities",
        "print_to_console": "Utilities",
    }

    migrated_count = 0

    for tool_name, tool_function in tool_store.items():
        try:
            existing = crud.get_tool_by_name(db, tool_name)
            if existing:
                print(f"✓ Tool '{tool_name}' already exists")
                continue

            if tool_name not in tool_schemas:
                print(f"⚠ No schema found for tool '{tool_name}', skipping")
                continue

            schema = tool_schemas[tool_name]
            function_info = schema.get("function", {})

            category_name = tool_categories.get(tool_name, "Utilities")
            category_id = categories.get(category_name, {}).category_id if category_name in categories else None

            tool_create = schemas.ToolCreate(
                name=tool_name,
                display_name=function_info.get("name", tool_name).replace("_", " ").title(),
                description=function_info.get("description", f"Tool: {tool_name}"),
                version="1.0.0",
                tool_type="local",
                execution_type="function",
                parameters_schema=function_info.get("parameters", {}),
                module_path=getattr(tool_function, "__module__", "agents.tools"),
                function_name=getattr(tool_function, "__name__", tool_name),
                category_id=category_id,
                tags=[],
                requires_auth=False,
                timeout_seconds=30,
                retry_count=3,
                created_by="init_script",
            )

            tool = crud.create_tool(db, tool_create)
            migrated_count += 1
            print(f"✓ Added tool: {tool_name} -> {tool.tool_id}")

        except Exception as e:
            print(f"✗ Error adding tool '{tool_name}': {e}")
            continue

    print(f"✓ Successfully added {migrated_count} tools")

def init_agents(db):
    try:
        from services.demo_service import DemoInitializationService
    except ImportError:
        print("⚠ Could not import DemoInitializationService, skipping agent initialization")
        return

    demo_service = DemoInitializationService(db)
    success, message, details = demo_service.initialize_agents()

    if success:
        print(f"✓ {message}")
        if details.get("added_agents"):
            for agent in details["added_agents"]:
                print(f"  - Added: {agent}")
        if details.get("updated_agents"):
            for agent in details["updated_agents"]:
                print(f"  - Updated: {agent}")
    else:
        print(f"✗ {message}")

def init_db():
    
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()

    try:
        existing_prompts = db.query(models.Prompt).first()
        if existing_prompts:
            print("Database already initialized with prompts.")
        else:
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
                    created_prompt = crud.create_prompt_safe(db, prompt)
                    if created_prompt:
                        print(f"Added prompt: {prompt_obj.prompt_label} v{prompt_obj.version}")
                    else:
                        print(f"Prompt {prompt_obj.prompt_label} v{prompt_obj.version} already exists.")
                except Exception as e:
                    print(f"Error adding prompt {prompt_obj.prompt_label}: {e}")

            print("Database initialized with prompts.")

        print("\nInitializing tool categories...")
        categories = init_tool_categories(db)

        print("\nInitializing tools...")
        init_tools(db, categories)

        print("\nInitializing agents...")
        init_agents(db)

        print("\nDatabase initialization completed.")

    finally:
        db.close()

if __name__ == "__main__":
    init_db()
