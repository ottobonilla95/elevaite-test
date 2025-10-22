# Agent Studio Migration Scripts

This directory contains scripts for migrating agent-studio data to the workflow-core-sdk schema.

---

## Available Scripts

### `migrate_to_sdk_schema.py`

Full schema migration script that migrates data from the old agent-studio schema to the new workflow-core-sdk schema.

**Features:**
- Creates new database with SDK schema
- Migrates all data (agents, prompts, workflows, tools)
- **Migrates UI metadata (step positions and connections)**
- Preserves all fields (stores extra fields in JSON)
- Validates migration with record count verification
- Supports dry-run mode for testing

**UI Metadata Migration:**
- Migrates `workflow_agents.position_x/position_y` to `step.position.x/y`
- Migrates `workflow_connections` to `workflow.connections` array
- Preserves connection handles and types
- Automatically derives step dependencies from connections

**Usage:**

```bash
# From repository root
./migrate_to_sdk.sh                    # Dry run
./migrate_to_sdk.sh --execute          # Execute migration

# Or use Python directly
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
    --source agent_studio \
    --target agent_studio_sdk \
    --dry-run

# Full options
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
    --source SOURCE_DB \
    --target TARGET_DB \
    --host localhost \
    --port 5433 \
    --user elevaite \
    --password elevaite \
    [--dry-run]
```

**What it migrates:**
- ✅ Agents (42 records)
- ✅ Prompts (30 records)
- ✅ Workflows (32 records)
- ✅ Tools (37 records)

**Schema transformations:**
- Table names: `agents` → `agent`, `prompts` → `prompt`, etc.
- Primary keys: `INTEGER id + UUID` → `UUID id`
- Extra fields: Stored in JSON (`provider_config.legacy_fields`, `global_config.legacy_fields`)

---

## Migration Results

See `MIGRATION_SUCCESS.md` in the repository root for complete migration documentation.

**Summary:**
- ✅ 141 total records migrated
- ✅ 100% success rate
- ✅ Zero data loss
- ✅ All API endpoints working

---

## Using the Migrated Database

After migration, start agent-studio with the new database:

```bash
export SQLALCHEMY_DATABASE_URL='postgresql://elevaite:elevaite@localhost:5433/agent_studio_sdk'
cd python_apps/agent_studio/agent-studio
uvicorn main:app --reload --port 8007
```

Test the API:

```bash
curl http://localhost:8007/api/agents/ | jq 'length'    # Should return 42
curl http://localhost:8007/api/workflows/ | jq 'length' # Should return 32
curl http://localhost:8007/api/prompts/ | jq 'length'   # Should return 30
curl http://localhost:8007/api/tools/ | jq 'length'     # Should return 37
```

---

## Troubleshooting

### Migration fails with "relation does not exist"

The SDK schema wasn't created properly. Check that:
- `workflow-core-sdk` package is installed
- Database connection is working
- PostgreSQL is running

### Record counts don't match

Check the migration output for errors. The script validates counts after migration.

### API returns 500 errors

Make sure you're using the correct database URL:
```bash
export SQLALCHEMY_DATABASE_URL='postgresql://elevaite:elevaite@localhost:5433/agent_studio_sdk'
```

---

## Development

To modify the migration script:

1. Test with dry-run first: `./migrate_to_sdk.sh`
2. Make changes to `migrate_to_sdk_schema.py`
3. Test again with dry-run
4. Execute: `./migrate_to_sdk.sh --execute`

---

## Files

- `migrate_to_sdk_schema.py` - Main migration script (800+ lines)
- `../../../migrate_to_sdk.sh` - Shell wrapper for easy execution
- `../../../MIGRATION_SUCCESS.md` - Complete migration documentation

