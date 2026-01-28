#!/usr/bin/env python3
"""
Full Schema Migration: Agent Studio → SDK Schema

Migrates data from old agent-studio schema to new workflow-core-sdk schema.

This script:
1. Creates a new database with SDK schema
2. Migrates all data from old schema to new schema
3. Preserves all important data (stores extra fields in JSON)
4. Validates the migration

Usage:
    python scripts/migrate_to_sdk_schema.py --source agent_studio --target agent_studio_sdk
    python scripts/migrate_to_sdk_schema.py --source agent_studio --target agent_studio_sdk --dry-run
"""

import argparse
import os
import sys
import json
from pathlib import Path
from typing import List
import uuid

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "agent-studio"))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session


class SchemaMigrator:
    """Migrates data from agent-studio schema to SDK schema"""

    def __init__(
        self,
        source_db: str,
        target_db: str,
        host: str = "localhost",
        port: int = 5433,
        user: str = "elevaite",
        password: str = "elevaite",
        target_host: str = None,
        target_port: int = None,
        target_user: str = None,
        target_password: str = None,
        dry_run: bool = False,
        skip_schema_creation: bool = False,
    ):
        self.source_db = source_db
        self.target_db = target_db
        self.host = host
        self.port = port
        self.user = user
        self.password = password

        # Target connection parameters (default to source if not specified)
        self.target_host = target_host or host
        self.target_port = target_port or port
        self.target_user = target_user or user
        self.target_password = target_password or password

        self.dry_run = dry_run
        self.skip_schema_creation = skip_schema_creation

        # Connection strings
        self.source_url = f"postgresql://{user}:{password}@{host}:{port}/{source_db}"
        self.target_url = (
            f"postgresql://{self.target_user}:{self.target_password}@{self.target_host}:{self.target_port}/{target_db}"
        )

        # Statistics
        self.stats = {
            "agents_migrated": 0,
            "prompts_migrated": 0,
            "workflows_migrated": 0,
            "workflow_steps_migrated": 0,
            "workflow_connections_migrated": 0,
            "tools_migrated": 0,
            "agent_tool_bindings_migrated": 0,
            "errors": [],
        }

    def connect_source(self) -> Session:
        """Connect to source database"""
        engine = create_engine(self.source_url)
        return Session(engine)

    def connect_target(self) -> Session:
        """Connect to target database"""
        engine = create_engine(self.target_url)
        return Session(engine)

    def create_target_database(self) -> bool:
        """Create target database with SDK schema"""
        if self.skip_schema_creation:
            print("⏭️  Skipping database/schema creation (assuming already created via Alembic)")
            return True

        print(f"📦 Creating target database: {self.target_db}")

        if self.dry_run:
            print(f"   [DRY RUN] Would create database: {self.target_db}")
            return True

        try:
            # Connect to postgres database to create new database (use target connection)
            admin_url = f"postgresql://{self.target_user}:{self.target_password}@{self.target_host}:{self.target_port}/postgres"
            admin_engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

            with admin_engine.connect() as conn:
                # Check if database exists
                result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{self.target_db}'"))
                if result.fetchone():
                    print(f"   ⚠️  Database already exists: {self.target_db}")
                    response = input("   Drop and recreate? (yes/no): ")
                    if response.lower() != "yes":
                        print("   ❌ Aborted")
                        return False

                    # Terminate connections
                    conn.execute(
                        text(f"""
                        SELECT pg_terminate_backend(pg_stat_activity.pid)
                        FROM pg_stat_activity
                        WHERE pg_stat_activity.datname = '{self.target_db}'
                        AND pid <> pg_backend_pid();
                    """)
                    )

                    # Drop database
                    conn.execute(text(f"DROP DATABASE {self.target_db}"))
                    print("   🗑️  Dropped existing database")

                # Create database
                conn.execute(text(f"CREATE DATABASE {self.target_db}"))
                print(f"   ✅ Database created: {self.target_db}")

            # Create SDK schema using SQLModel
            print("   📋 Creating SDK schema...")

            # Temporarily set environment variable for SDK database connection
            original_db_url = os.environ.get("SQLALCHEMY_DATABASE_URL")
            os.environ["SQLALCHEMY_DATABASE_URL"] = self.target_url

            try:
                # Import SDK database module (this will use the new env var)
                import sys

                # Remove cached modules to force reload with new env var
                modules_to_reload = [m for m in sys.modules.keys() if m.startswith("workflow_core_sdk")]
                for module in modules_to_reload:
                    del sys.modules[module]

                # Import and create tables
                from workflow_core_sdk.db.database import create_db_and_tables

                create_db_and_tables()
                print("   ✅ SDK schema created successfully")
                return True

            except Exception as e:
                print(f"   ❌ Failed to create SDK schema: {e}")
                import traceback

                traceback.print_exc()
                return False

            finally:
                # Restore original environment variable
                if original_db_url:
                    os.environ["SQLALCHEMY_DATABASE_URL"] = original_db_url
                else:
                    os.environ.pop("SQLALCHEMY_DATABASE_URL", None)

        except Exception as e:
            print(f"   ❌ Error creating target database: {e}")
            return False

    def migrate_prompts(self, source_session: Session, target_session: Session) -> bool:
        """Migrate prompts from old schema to new schema"""
        print("\n📝 Migrating prompts...")

        try:
            # Read from old schema
            result = source_session.execute(
                text("""
                SELECT
                    pid,
                    prompt_label,
                    prompt,
                    unique_label,
                    app_name,
                    ai_model_provider,
                    ai_model_name,
                    tags,
                    hyper_parameters,
                    variables,
                    created_time
                FROM prompts
            """)
            )

            prompts = result.fetchall()
            print(f"   Found {len(prompts)} prompts to migrate")

            if self.dry_run:
                print(f"   [DRY RUN] Would migrate {len(prompts)} prompts")
                return True

            # Insert into new schema
            for prompt in prompts:
                target_session.execute(
                    text("""
                    INSERT INTO prompt (
                        id,
                        prompt_label,
                        prompt,
                        unique_label,
                        app_name,
                        ai_model_provider,
                        ai_model_name,
                        tags,
                        hyper_parameters,
                        variables,
                        organization_id,
                        created_by,
                        created_time,
                        updated_time
                    ) VALUES (
                        :id,
                        :prompt_label,
                        :prompt,
                        :unique_label,
                        :app_name,
                        :ai_model_provider,
                        :ai_model_name,
                        :tags,
                        :hyper_parameters,
                        :variables,
                        NULL,
                        NULL,
                        :created_time,
                        :created_time
                    )
                """),
                    {
                        "id": prompt[0],  # pid
                        "prompt_label": prompt[1],
                        "prompt": prompt[2],
                        "unique_label": prompt[3],
                        "app_name": prompt[4],
                        "ai_model_provider": prompt[5],
                        "ai_model_name": prompt[6],
                        "tags": json.dumps(prompt[7]) if prompt[7] else "[]",
                        "hyper_parameters": json.dumps(prompt[8]) if prompt[8] else "{}",
                        "variables": json.dumps(prompt[9]) if prompt[9] else "{}",
                        "created_time": prompt[10],
                    },
                )
                self.stats["prompts_migrated"] += 1

            target_session.commit()
            print(f"   ✅ Migrated {self.stats['prompts_migrated']} prompts")
            return True

        except Exception as e:
            print(f"   ❌ Error migrating prompts: {e}")
            self.stats["errors"].append(f"Prompts: {e}")
            target_session.rollback()
            return False

    def migrate_agents(self, source_session: Session, target_session: Session) -> bool:
        """Migrate agents from old schema to new schema"""
        print("\n🤖 Migrating agents...")

        try:
            # Read from old schema
            result = source_session.execute(
                text("""
                SELECT
                    agent_id,
                    name,
                    description,
                    system_prompt_id,
                    agent_type,
                    functions,
                    routing_options,
                    short_term_memory,
                    long_term_memory,
                    reasoning,
                    input_type,
                    output_type,
                    response_type,
                    max_retries,
                    timeout,
                    deployed,
                    status,
                    priority,
                    parent_agent_id,
                    persona,
                    available_for_deployment,
                    deployment_code,
                    failure_strategies,
                    session_id,
                    last_active,
                    collaboration_mode
                FROM agents
            """)
            )

            agents = result.fetchall()
            print(f"   Found {len(agents)} agents to migrate")

            if self.dry_run:
                print(f"   [DRY RUN] Would migrate {len(agents)} agents")
                return True

            # Insert into new schema
            for agent in agents:
                # Map agent_type to provider_type (best effort)
                agent_type = agent[4] or "router"
                provider_type = "openai_textgen"  # Default

                # Build provider_config from old fields
                provider_config = {
                    "model_name": "gpt-4",  # Default
                    "temperature": 0.7,
                    "max_tokens": 2000,
                }

                # Store all extra fields in provider_config for preservation
                extra_fields = {
                    "agent_type": agent_type,
                    "functions": agent[5],
                    "routing_options": agent[6],
                    "short_term_memory": agent[7],
                    "long_term_memory": agent[8],
                    "reasoning": agent[9],
                    "input_type": agent[10],
                    "output_type": agent[11],
                    "response_type": agent[12],
                    "max_retries": agent[13],
                    "timeout": agent[14],
                    "deployed": agent[15],
                    "priority": agent[17],
                    "parent_agent_id": str(agent[18]) if agent[18] else None,
                    "persona": agent[19],
                    "available_for_deployment": agent[20],
                    "deployment_code": agent[21],
                    "failure_strategies": agent[22],
                    "session_id": agent[23],
                    "last_active": agent[24].isoformat() if agent[24] else None,
                    "collaboration_mode": agent[25],
                }
                provider_config["legacy_fields"] = extra_fields

                target_session.execute(
                    text("""
                    INSERT INTO agent (
                        id,
                        name,
                        description,
                        system_prompt_id,
                        provider_type,
                        provider_config,
                        tags,
                        status,
                        organization_id,
                        created_by,
                        created_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :name,
                        :description,
                        :system_prompt_id,
                        :provider_type,
                        :provider_config,
                        :tags,
                        :status,
                        NULL,
                        NULL,
                        NOW(),
                        NOW()
                    )
                """),
                    {
                        "id": agent[0],  # agent_id
                        "name": agent[1],
                        "description": agent[2],
                        "system_prompt_id": agent[3],
                        "provider_type": provider_type,
                        "provider_config": json.dumps(provider_config),
                        "tags": "[]",
                        "status": agent[16] or "active",  # status
                    },
                )
                self.stats["agents_migrated"] += 1

            target_session.commit()
            print(f"   ✅ Migrated {self.stats['agents_migrated']} agents")
            return True

        except Exception as e:
            print(f"   ❌ Error migrating agents: {e}")
            self.stats["errors"].append(f"Agents: {e}")
            target_session.rollback()
            return False

    def migrate_workflows(self, source_session: Session, target_session: Session) -> bool:
        """Migrate workflows from old schema to new schema with UI metadata"""
        print("\n🔄 Migrating workflows with UI metadata...")

        try:
            # Read from old schema
            result = source_session.execute(
                text("""
                SELECT
                    workflow_id,
                    name,
                    description,
                    version,
                    configuration,
                    created_by,
                    created_at,
                    updated_at,
                    is_active,
                    is_deployed,
                    deployed_at,
                    tags,
                    is_editable
                FROM workflows
            """)
            )

            workflows = result.fetchall()
            print(f"   Found {len(workflows)} workflows to migrate")

            if self.dry_run:
                print(f"   [DRY RUN] Would migrate {len(workflows)} workflows")
                return True

            # Insert into new schema
            for workflow in workflows:
                workflow_id = workflow[0]

                # Determine status from old flags
                is_active = workflow[8]
                is_deployed = workflow[9]
                if is_deployed:
                    status = "active"
                elif is_active:
                    status = "active"
                else:
                    status = "inactive"

                # Parse configuration
                config = workflow[4] if workflow[4] else {}

                # Migrate workflow_agents to steps with positions
                agents_result = source_session.execute(
                    text("""
                    SELECT
                        id,
                        agent_id,
                        position_x,
                        position_y,
                        node_id,
                        agent_config
                    FROM workflow_agents
                    WHERE workflow_id = :workflow_id
                    ORDER BY id
                """),
                    {"workflow_id": workflow_id},
                )

                agents = agents_result.fetchall()

                # Migrate workflow_connections
                connections_result = source_session.execute(
                    text("""
                    SELECT
                        source_agent_id,
                        target_agent_id,
                        connection_type,
                        source_handle,
                        target_handle
                    FROM workflow_connections
                    WHERE workflow_id = :workflow_id
                """),
                    {"workflow_id": workflow_id},
                )

                connections = connections_result.fetchall()

                # Build agent_id to node_id mapping
                agent_to_node = {}
                for agent in agents:
                    agent_to_node[str(agent[1])] = agent[4]  # agent_id -> node_id

                # Convert agents to steps with UI metadata
                steps = []
                for agent in agents:
                    agent_id = agent[1]
                    position_x = agent[2]
                    position_y = agent[3]
                    node_id = agent[4]
                    agent_config = agent[5] if agent[5] else {}

                    step = {
                        "step_id": node_id,
                        "step_type": "agent_execution",
                        "name": f"Agent {agent_id}",
                        "config": {"agent_id": str(agent_id), **agent_config, "stream": True, "visible_to_user": True},
                        "dependencies": [],  # Will be populated from connections
                        "input_mapping": {},
                    }

                    # Add position if available
                    if position_x is not None and position_y is not None:
                        step["position"] = {"x": float(position_x), "y": float(position_y)}

                    steps.append(step)

                # Convert connections to new format
                new_connections = []
                for conn in connections:
                    source_agent_id = str(conn[0])
                    target_agent_id = str(conn[1])
                    connection_type = conn[2] if conn[2] else "default"
                    source_handle = conn[3]
                    target_handle = conn[4]

                    # Map agent IDs to node IDs
                    if source_agent_id in agent_to_node and target_agent_id in agent_to_node:
                        new_conn = {
                            "source_step_id": agent_to_node[source_agent_id],
                            "target_step_id": agent_to_node[target_agent_id],
                            "connection_type": connection_type,
                        }

                        if source_handle:
                            new_conn["source_handle"] = source_handle
                        if target_handle:
                            new_conn["target_handle"] = target_handle

                        new_connections.append(new_conn)

                        # Add to dependencies
                        target_node_id = agent_to_node[target_agent_id]
                        source_node_id = agent_to_node[source_agent_id]
                        for step in steps:
                            if step["step_id"] == target_node_id:
                                if source_node_id not in step["dependencies"]:
                                    step["dependencies"].append(source_node_id)

                # Update configuration with steps and connections
                if steps:
                    if isinstance(config, dict):
                        config["steps"] = steps
                        config["connections"] = new_connections
                    else:
                        config = {"steps": steps, "connections": new_connections}
                    print(
                        f"   📍 Migrated {len(steps)} steps and {len(new_connections)} connections for workflow '{workflow[1]}'"
                    )
                    self.stats["workflow_steps_migrated"] += len(steps)
                    self.stats["workflow_connections_migrated"] += len(new_connections)

                # Store extra fields in global_config
                global_config = {
                    "legacy_fields": {
                        "is_deployed": is_deployed,
                        "deployed_at": workflow[10].isoformat() if workflow[10] else None,
                        "is_editable": workflow[12],
                    }
                }

                target_session.execute(
                    text("""
                    INSERT INTO workflow (
                        id,
                        name,
                        description,
                        version,
                        execution_pattern,
                        configuration,
                        global_config,
                        tags,
                        timeout_seconds,
                        status,
                        created_by,
                        created_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :name,
                        :description,
                        :version,
                        CAST(:execution_pattern AS executionpattern),
                        :configuration,
                        :global_config,
                        :tags,
                        NULL,
                        CAST(:status AS workflowstatus),
                        :created_by,
                        :created_at,
                        :updated_at
                    )
                """),
                    {
                        "id": workflow_id,
                        "name": workflow[1],
                        "description": workflow[2],
                        "version": workflow[3],
                        "execution_pattern": "SEQUENTIAL",  # Uppercase for enum
                        "configuration": json.dumps(config),
                        "global_config": json.dumps(global_config),
                        "tags": json.dumps(workflow[11]) if workflow[11] else "[]",
                        "status": status.upper() if status else "ACTIVE",  # Uppercase for enum
                        "created_by": workflow[5],
                        "created_at": workflow[6],
                        "updated_at": workflow[7],
                    },
                )
                self.stats["workflows_migrated"] += 1

            target_session.commit()
            print(f"   ✅ Migrated {self.stats['workflows_migrated']} workflows with UI metadata")
            return True

        except Exception as e:
            print(f"   ❌ Error migrating workflows: {e}")
            import traceback

            traceback.print_exc()
            self.stats["errors"].append(f"Workflows: {e}")
            target_session.rollback()
            return False

    def migrate_tools(self, source_session: Session, target_session: Session) -> bool:
        """Migrate tools from old schema to new schema"""
        print("\n🔧 Migrating tools...")

        try:
            # Read from old schema
            result = source_session.execute(
                text("""
                SELECT
                    tool_id,
                    name,
                    display_name,
                    description,
                    version,
                    tool_type,
                    execution_type,
                    parameters_schema,
                    return_schema,
                    module_path,
                    function_name,
                    api_endpoint,
                    http_method,
                    headers,
                    auth_required,
                    tags,
                    is_active,
                    is_available,
                    category_id,
                    mcp_server_id,
                    remote_name,
                    documentation,
                    examples,
                    usage_count,
                    last_used
                FROM tools
            """)
            )

            tools = result.fetchall()
            print(f"   Found {len(tools)} tools to migrate")

            if self.dry_run:
                print(f"   [DRY RUN] Would migrate {len(tools)} tools")
                return True

            # Insert into new schema
            for tool in tools:
                target_session.execute(
                    text("""
                    INSERT INTO tool (
                        id,
                        name,
                        display_name,
                        description,
                        version,
                        tool_type,
                        execution_type,
                        parameters_schema,
                        return_schema,
                        module_path,
                        function_name,
                        mcp_server_id,
                        remote_name,
                        api_endpoint,
                        http_method,
                        headers,
                        auth_required,
                        category_id,
                        tags,
                        documentation,
                        examples,
                        is_active,
                        is_available,
                        last_used,
                        usage_count,
                        created_at,
                        updated_at
                    ) VALUES (
                        :id,
                        :name,
                        :display_name,
                        :description,
                        :version,
                        :tool_type,
                        :execution_type,
                        :parameters_schema,
                        :return_schema,
                        :module_path,
                        :function_name,
                        :mcp_server_id,
                        :remote_name,
                        :api_endpoint,
                        :http_method,
                        :headers,
                        :auth_required,
                        :category_id,
                        :tags,
                        :documentation,
                        :examples,
                        :is_active,
                        :is_available,
                        :last_used,
                        :usage_count,
                        NOW(),
                        NOW()
                    )
                """),
                    {
                        "id": tool[0],  # tool_id
                        "name": tool[1],
                        "display_name": tool[2],
                        "description": tool[3],
                        "version": tool[4],
                        "tool_type": tool[5],
                        "execution_type": tool[6],
                        "parameters_schema": json.dumps(tool[7]) if tool[7] else "{}",
                        "return_schema": json.dumps(tool[8]) if tool[8] else "{}",
                        "module_path": tool[9],
                        "function_name": tool[10],
                        "api_endpoint": tool[11],
                        "http_method": tool[12],
                        "headers": json.dumps(tool[13]) if tool[13] else "{}",
                        "auth_required": tool[14],
                        "tags": json.dumps(tool[15]) if tool[15] else "[]",
                        "is_active": tool[16],
                        "is_available": tool[17],
                        "category_id": tool[18],
                        "mcp_server_id": tool[19],
                        "remote_name": tool[20],
                        "documentation": tool[21],
                        "examples": json.dumps(tool[22]) if tool[22] else "{}",
                        "usage_count": tool[23],
                        "last_used": tool[24],
                    },
                )
                self.stats["tools_migrated"] += 1

            target_session.commit()
            print(f"   ✅ Migrated {self.stats['tools_migrated']} tools")
            return True

        except Exception as e:
            print(f"   ❌ Error migrating tools: {e}")
            self.stats["errors"].append(f"Tools: {e}")
            target_session.rollback()

    def migrate_agent_tool_bindings(self, source_session: Session, target_session: Session) -> bool:
        """Migrate agent→tool assignments into AgentToolBinding"""
        print("\n🧩 Migrating agent tool bindings...")
        try:
            # Build tool name → id map from source tools
            tools_res = source_session.execute(
                text(
                    """
                    SELECT tool_id, name, remote_name, function_name
                    FROM tools
                    """
                )
            )
            tool_rows = tools_res.fetchall()
            name_to_id = {}
            alt_to_id = {}
            for t in tool_rows:
                tid, name, remote_name, function_name = t[0], t[1], t[2], t[3]
                if name:
                    name_to_id[str(name)] = tid
                if remote_name:
                    alt_to_id[str(remote_name)] = tid
                if function_name:
                    alt_to_id[str(function_name)] = tid

            # Fetch agents with functions (OpenAI-style tool specs)
            agents_res = source_session.execute(
                text(
                    """
                    SELECT agent_id, functions
                    FROM agents
                    """
                )
            )
            agents = agents_res.fetchall()
            created = 0

            for agent_row in agents:
                agent_id = agent_row[0]
                functions = agent_row[1]
                if not functions:
                    continue

                funcs = functions
                if isinstance(funcs, str):
                    try:
                        funcs = json.loads(funcs)
                    except Exception:
                        continue
                if not isinstance(funcs, list):
                    continue

                # Extract function names
                names: List[str] = []
                for f in funcs:
                    fn = None
                    if isinstance(f, dict):
                        func_obj = f.get("function") if isinstance(f.get("function"), dict) else None
                        if func_obj and "name" in func_obj:
                            fn = func_obj["name"]
                        elif "name" in f:
                            fn = f["name"]
                    elif isinstance(f, str):
                        fn = f
                    if fn:
                        names.append(str(fn))

                # Deduplicate while preserving order
                names = list(dict.fromkeys(names))

                for fn in names:
                    # Try resolve by source tool maps first
                    tool_id = name_to_id.get(fn) or alt_to_id.get(fn)

                    # If not found, try resolve in TARGET DB (case-insensitive by name, or by function_name/remote_name)
                    if not tool_id:
                        row = target_session.execute(
                            text(
                                """
                                SELECT id FROM tool
                                WHERE LOWER(name) = LOWER(:fn)
                                   OR LOWER(COALESCE(function_name, '')) = LOWER(:fn)
                                   OR LOWER(COALESCE(remote_name, '')) = LOWER(:fn)
                                LIMIT 1
                                """
                            ),
                            {"fn": fn},
                        ).fetchone()
                        if row:
                            tool_id = row[0]

                    # If still not found, create a minimal DB tool from the function spec on the agent
                    if not tool_id:
                        # Find this function object to extract description/parameters
                        func_def = None
                        for f in funcs:
                            # normalize to dict with function key
                            if isinstance(f, dict):
                                if isinstance(f.get("function"), dict) and f.get("function", {}).get("name") == fn:
                                    func_def = f.get("function")
                                    break
                                if f.get("name") == fn:
                                    func_def = f
                                    break
                        description = ""
                        parameters = {}
                        if isinstance(func_def, dict):
                            description = func_def.get("description") or ""
                            params = func_def.get("parameters")
                            if isinstance(params, dict):
                                parameters = params
                        # Insert tool record
                        new_tool_id = uuid.uuid4()
                        target_session.execute(
                            text(
                                """
                                INSERT INTO tool (
                                    id, name, display_name, description, version, tool_type, execution_type,
                                    parameters_schema, return_schema, module_path, function_name, mcp_server_id,
                                    remote_name, api_endpoint, http_method, headers, auth_required, category_id, tags,
                                    documentation, examples, is_active, is_available, last_used, usage_count, created_at, updated_at
                                ) VALUES (
                                    :id, :name, :display_name, :description, '1.0.0', 'local', 'function',
                                    :parameters_schema, NULL, NULL, :function_name, NULL,
                                    NULL, NULL, NULL, NULL, FALSE, NULL, NULL,
                                    NULL, NULL, TRUE, TRUE, NULL, 0, NOW(), NOW()
                                )
                                """
                            ),
                            {
                                "id": new_tool_id,
                                "name": fn,
                                "display_name": fn,
                                "description": description,
                                "parameters_schema": json.dumps(parameters or {"type": "object", "properties": {}}),
                                "function_name": fn,
                            },
                        )
                        tool_id = new_tool_id

                    # Skip if binding already exists (idempotent)
                    exists = target_session.execute(
                        text(
                            """
                            SELECT 1 FROM agenttoolbinding
                            WHERE agent_id = :agent_id AND tool_id = :tool_id
                            LIMIT 1
                            """
                        ),
                        {"agent_id": agent_id, "tool_id": tool_id},
                    ).fetchone()
                    if exists:
                        continue

                    target_session.execute(
                        text(
                            """
                            INSERT INTO agenttoolbinding (
                                id, agent_id, tool_id, override_parameters, is_active, organization_id, created_by
                            ) VALUES (
                                :id, :agent_id, :tool_id, :override_parameters, :is_active, NULL, NULL
                            )
                            """
                        ),
                        {
                            "id": uuid.uuid4(),
                            "agent_id": agent_id,
                            "tool_id": tool_id,
                            "override_parameters": json.dumps({}),
                            "is_active": True,
                        },
                    )
                    created += 1

            target_session.commit()
            self.stats["agent_tool_bindings_migrated"] += created
            print(f"   ✅ Migrated {created} agent tool bindings")
            return True

        except Exception as e:
            print(f"   ❌ Error migrating agent tool bindings: {e}")
            self.stats["errors"].append(f"AgentToolBindings: {e}")
            target_session.rollback()
            return False

            return False

    def validate_migration(self, source_session: Session, target_session: Session) -> bool:
        """Validate that migration was successful"""
        print("\n🔍 Validating migration...")

        try:
            # Count records in source
            source_counts = {}
            for table in ["agents", "prompts", "workflows", "tools"]:
                result = source_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                source_counts[table] = result.fetchone()[0]

            # Count records in target (singular table names)
            target_counts = {}
            for table in ["agent", "prompt", "workflow", "tool"]:
                result = target_session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                target_counts[table] = result.fetchone()[0]

            # Compare
            all_match = True
            print("\n   Source → Target:")
            print(f"   {'Table':<15} {'Source':<10} {'Target':<10} {'Status':<10}")
            print(f"   {'-' * 50}")

            for old_table, new_table in [
                ("agents", "agent"),
                ("prompts", "prompt"),
                ("workflows", "workflow"),
                ("tools", "tool"),
            ]:
                source_count = source_counts[old_table]
                target_count = target_counts[new_table]
                match = "✅" if source_count == target_count else "❌"
                all_match = all_match and (source_count == target_count)
                print(f"   {old_table:<15} {source_count:<10} {target_count:<10} {match}")

            if all_match:
                print("\n   ✅ All record counts match!")
                return True
            else:
                print("\n   ⚠️  Some record counts don't match")
                return False

        except Exception as e:
            print(f"   ❌ Error validating migration: {e}")
            return False

    def run(self) -> bool:
        """Run the complete migration process"""
        print("=" * 70)
        print("SCHEMA MIGRATION: AGENT STUDIO → SDK")
        print("=" * 70)
        print()
        print(f"Source: {self.source_db}")
        print(f"Target: {self.target_db}")
        print(f"Dry Run: {self.dry_run}")
        print()

        # Step 1: Create target database
        if not self.create_target_database():
            return False

        # Step 2: Connect to both databases
        print("\n🔌 Connecting to databases...")
        try:
            source_session = self.connect_source()
            target_session = self.connect_target()
            print("   ✅ Connected to both databases")

            # Step 2.5: Ensure local tools are registered in target DB (so bindings can resolve)
            if not self.dry_run:
                try:
                    # Point SDK to the target DB for a SQLModel session
                    original_db_url = os.environ.get("SQLALCHEMY_DATABASE_URL")
                    os.environ["SQLALCHEMY_DATABASE_URL"] = self.target_url
                    # Reload SDK DB to pick up the new URL and get a SQLModel session
                    from importlib import reload
                    import workflow_core_sdk.db.database as sdk_db

                    reload(sdk_db)
                    from workflow_core_sdk.tools.registry import tool_registry
                    from workflow_core_sdk.db.database import get_db_session

                    sqlmodel_session = get_db_session()
                    try:
                        sync_result = tool_registry.sync_local_to_db(sqlmodel_session)
                        print(
                            f"   🔧 Synced local tools to target DB: created={sync_result.get('created', 0)}, updated={sync_result.get('updated', 0)}"
                        )
                    finally:
                        try:
                            sqlmodel_session.close()
                        except Exception:
                            pass
                    # Restore original DB URL if it existed
                    if original_db_url is not None:
                        os.environ["SQLALCHEMY_DATABASE_URL"] = original_db_url
                except Exception as e:
                    print(f"   ⚠️  Failed to sync local tools to target DB (continuing): {e}")

        except Exception as e:
            print(f"   ❌ Failed to connect: {e}")
            return False

        # Step 3: Migrate data
        success = True
        success = success and self.migrate_prompts(source_session, target_session)
        success = success and self.migrate_agents(source_session, target_session)
        success = success and self.migrate_tools(source_session, target_session)
        success = success and self.migrate_agent_tool_bindings(source_session, target_session)
        success = success and self.migrate_workflows(source_session, target_session)

        # Step 4: Validate
        if success and not self.dry_run:
            self.validate_migration(source_session, target_session)

        # Step 5: Print summary
        print("\n" + "=" * 70)
        print("MIGRATION SUMMARY")
        print("=" * 70)
        print(f"Prompts migrated:              {self.stats['prompts_migrated']}")
        print(f"Agents migrated:               {self.stats['agents_migrated']}")
        print(f"Tools migrated:                {self.stats['tools_migrated']}")
        print(f"Agent tool bindings migrated:  {self.stats['agent_tool_bindings_migrated']}")
        print(f"Workflows migrated:            {self.stats['workflows_migrated']}")
        print(f"  - Workflow steps migrated:   {self.stats['workflow_steps_migrated']}")
        print(f"  - Workflow connections:      {self.stats['workflow_connections_migrated']}")

        if self.stats["errors"]:
            print("\n⚠️  Errors encountered:")
            for error in self.stats["errors"]:
                print(f"   - {error}")

        if success:
            print("\n✅ Migration completed successfully!")
            if not self.dry_run:
                print("\n📍 UI Metadata Migration:")
                print("   - Step positions preserved from workflow_agents table")
                print("   - Connections preserved from workflow_connections table")
                print("\nTo use the new database:")
                print(f"  export SQLALCHEMY_DATABASE_URL='{self.target_url}'")
        else:
            print("\n❌ Migration failed")

        print("=" * 70)

        # Close connections
        source_session.close()
        target_session.close()

        return success


def main():
    parser = argparse.ArgumentParser(
        description="Migrate data from agent-studio schema to SDK schema",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "--source",
        default="agent_studio",
        help="Source database name (default: agent_studio)",
    )

    parser.add_argument(
        "--target",
        default="agent_studio_sdk",
        help="Target database name (default: agent_studio_sdk)",
    )

    # Connection string arguments (preferred)
    parser.add_argument(
        "--source-url",
        help="Source database connection URL (postgresql://user:pass@host:port/db)",
    )

    parser.add_argument(
        "--target-url",
        help="Target database connection URL (postgresql://user:pass@host:port/db)",
    )

    # Legacy individual parameter arguments (for backward compatibility)
    parser.add_argument(
        "--host",
        default="localhost",
        help="PostgreSQL host for both databases (default: localhost)",
    )

    parser.add_argument(
        "--port",
        type=int,
        default=5433,
        help="PostgreSQL port (default: 5433)",
    )

    parser.add_argument(
        "--user",
        default="elevaite",
        help="PostgreSQL user (default: elevaite)",
    )

    parser.add_argument(
        "--password",
        default="elevaite",
        help="PostgreSQL password for both databases (default: elevaite)",
    )

    # Separate source/target parameters
    parser.add_argument(
        "--source-host",
        help="Source database host (overrides --host)",
    )

    parser.add_argument(
        "--source-port",
        type=int,
        help="Source database port (overrides --port)",
    )

    parser.add_argument(
        "--source-user",
        help="Source database user (overrides --user)",
    )

    parser.add_argument(
        "--source-password",
        help="Source database password (overrides --password)",
    )

    parser.add_argument(
        "--target-host",
        help="Target database host (overrides --host)",
    )

    parser.add_argument(
        "--target-port",
        type=int,
        help="Target database port (overrides --port)",
    )

    parser.add_argument(
        "--target-user",
        help="Target database user (overrides --user)",
    )

    parser.add_argument(
        "--target-password",
        help="Target database password (overrides --password)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry run without making changes",
    )

    parser.add_argument(
        "--skip-schema-creation",
        action="store_true",
        help="Skip database and schema creation (use when schema already created via Alembic)",
    )

    args = parser.parse_args()

    def parse_db_url(url: str) -> dict:
        """Parse PostgreSQL connection URL using regex to handle special characters in password"""
        import re

        # Pattern: postgresql://user:password@host:port/database
        pattern = r"postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+)"
        match = re.match(pattern, url)

        if not match:
            raise ValueError(f"Invalid PostgreSQL URL format: {url}")

        return {
            "user": match.group(1),
            "password": match.group(2),
            "host": match.group(3),
            "port": int(match.group(4)),
            "db": match.group(5),
        }

    # Parse connection URLs if provided
    source_params = {}
    target_params = {}

    if args.source_url:
        # Parse source URL using regex
        source_params = parse_db_url(args.source_url)
    else:
        # Use individual parameters
        source_params = {
            "host": args.source_host or args.host,
            "port": args.source_port or args.port,
            "user": args.source_user or args.user,
            "password": args.source_password or args.password,
            "db": args.source,
        }

    if args.target_url:
        # Parse target URL using regex
        target_params = parse_db_url(args.target_url)
    else:
        # Use individual parameters
        target_params = {
            "host": args.target_host or args.host,
            "port": args.target_port or args.port,
            "user": args.target_user or args.user,
            "password": args.target_password or args.password,
            "db": args.target,
        }

    migrator = SchemaMigrator(
        source_db=source_params["db"],
        target_db=target_params["db"],
        host=source_params["host"],
        port=source_params["port"],
        user=source_params["user"],
        password=source_params["password"],
        target_host=target_params["host"],
        target_port=target_params["port"],
        target_user=target_params["user"],
        target_password=target_params["password"],
        dry_run=args.dry_run,
        skip_schema_creation=args.skip_schema_creation,
    )

    success = migrator.run()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
