#!/usr/bin/env python3
"""
ARCHIVED: Migration script to populate the new tool storage tables with existing tools.

This script migrates tools from the current in-memory tool_store to the new
database-backed tool storage system.

NOTE: This script was used for the initial Phase 1 migration and should not be run again.
It is kept for reference purposes only.
"""

import os
import sys
from datetime import datetime

# Add the current directory to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from db.database import SessionLocal
from db import crud, schemas
from agents.tools import tool_store, tool_schemas


def migrate_tool_categories():
    """Create default tool categories."""
    db = SessionLocal()

    try:
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
            # Check if category already exists
            existing = crud.get_tool_category_by_name(db, cat_data["name"])
            if existing:
                print(f"✓ Category '{cat_data['name']}' already exists")
                created_categories[cat_data["name"]] = existing
            else:
                category = crud.create_tool_category(db, schemas.ToolCategoryCreate(**cat_data))
                created_categories[cat_data["name"]] = category
                print(f"✓ Created category: {cat_data['name']}")

        return created_categories

    except Exception as e:
        print(f"✗ Error creating categories: {e}")
        db.rollback()
        return {}
    finally:
        db.close()


def migrate_existing_tools():
    """Migrate existing tools from tool_store to database."""
    db = SessionLocal()

    try:
        # Get categories
        categories = {cat.name: cat for cat in crud.get_tool_categories(db)}

        # Tool categorization mapping
        tool_categories = {
            "query_retriever": "Search & Retrieval",
            "query_retriever2": "Search & Retrieval",
            "customer_query_retriever": "Search & Retrieval",
            "web_search": "Web & API",
            "url_to_markdown": "Web & API",
            "weather_forecast": "Web & API",
            "add_numbers": "Utilities",
            "print_to_console": "Utilities",
            "get_customer_order": "Customer Service",
            "get_customer_location": "Customer Service",
            "add_customer": "Customer Service",
        }

        migrated_count = 0

        for tool_name, tool_function in tool_store.items():
            try:
                # Check if tool already exists
                existing = crud.get_tool_by_name(db, tool_name)
                if existing:
                    print(f"✓ Tool '{tool_name}' already exists")
                    continue

                # Get tool schema
                if tool_name not in tool_schemas:
                    print(f"⚠ No schema found for tool '{tool_name}', skipping")
                    continue

                schema = tool_schemas[tool_name]
                function_info = schema.get("function", {})

                # Determine category
                category_name = tool_categories.get(tool_name, "Utilities")
                category_id = categories.get(category_name, {}).category_id if category_name in categories else None

                # Create tool
                tool_create = schemas.ToolCreate(
                    name=tool_name,
                    display_name=function_info.get("name", tool_name).replace("_", " ").title(),
                    description=function_info.get("description", f"Tool: {tool_name}"),
                    version="1.0.0",
                    tool_type="local",
                    execution_type="function",
                    parameters_schema=function_info.get("parameters", {}),
                    module_path=tool_function.__module__,
                    function_name=tool_function.__name__,
                    category_id=category_id,
                    tags=[],
                    requires_auth=False,
                    timeout_seconds=30,
                    retry_count=3,
                    created_by="migration_script",
                )

                tool = crud.create_tool(db, tool_create)
                migrated_count += 1
                print(f"✓ Migrated tool: {tool_name} -> {tool.tool_id}")

            except Exception as e:
                print(f"✗ Error migrating tool '{tool_name}': {e}")
                continue

        print(f"\n✓ Successfully migrated {migrated_count} tools")
        return True

    except Exception as e:
        print(f"✗ Error during tool migration: {e}")
        db.rollback()
        return False
    finally:
        db.close()


def verify_migration():
    """Verify the migration was successful."""
    db = SessionLocal()

    try:
        # Count categories
        categories = crud.get_tool_categories(db)
        print(f"\nVerification Results:")
        print(f"- Tool Categories: {len(categories)}")

        for category in categories:
            tools_in_category = crud.get_tools(db, category_id=category.category_id)
            print(f"  - {category.name}: {len(tools_in_category)} tools")

        # Count tools
        all_tools = crud.get_tools(db)
        active_tools = crud.get_available_tools(db)

        print(f"- Total Tools: {len(all_tools)}")
        print(f"- Active Tools: {len(active_tools)}")

        # List tools by type
        local_tools = crud.get_tools(db, tool_type="local")
        print(f"- Local Tools: {len(local_tools)}")

        print(f"\nLocal Tools:")
        for tool in local_tools:
            print(f"  - {tool.name} (v{tool.version})")

        return True

    except Exception as e:
        print(f"✗ Error during verification: {e}")
        return False
    finally:
        db.close()


def main():
    """Run the migration."""
    print("Starting tool storage migration...")
    print("=" * 50)

    # Step 1: Create categories
    print("\n1. Creating tool categories...")
    categories = migrate_tool_categories()
    if not categories:
        print("✗ Failed to create categories, aborting migration")
        return False

    # Step 2: Migrate tools
    print("\n2. Migrating existing tools...")
    if not migrate_existing_tools():
        print("✗ Tool migration failed")
        return False

    # Step 3: Verify migration
    print("\n3. Verifying migration...")
    if not verify_migration():
        print("✗ Migration verification failed")
        return False

    print("\n" + "=" * 50)
    print("✓ Tool storage migration completed successfully!")
    print("\nNext steps:")
    print("- Update agents to use the new tool registry")
    print("- Test tool execution through the new system")
    print("- Implement MCP server integration (Phase 2)")

    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
