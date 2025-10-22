# Database Migration Tools

This directory contains tools and documentation for migrating data from the old Agent Studio schema to the new workflow-core-sdk schema.

## Migration Scripts

### `migrate_live_db.sh` (Recommended)
Interactive helper script for migrating live databases with UI metadata support.

**Features:**
- Configuration mode: Edit connection strings directly in the script
- Interactive mode: Prompted for connection details
- Supports PostgreSQL connection URLs
- Handles special characters in passwords
- Supports separate source/target database hosts
- Dry-run mode to preview changes before executing

**Usage:**
```bash
# Edit connection details in the script
nano migrate_live_db.sh

# Run migration (will use configured values)
./migrate_live_db.sh
```

See `migrate_live_db.example.sh` for a template with comments.

### `migrate_to_sdk.sh` (Legacy)
Older migration script with simpler interface. Use `migrate_live_db.sh` instead for new migrations.

## Documentation

- **`QUICK_MIGRATION_REFERENCE.md`** - Quick start guide for migration
- **`LIVE_DATABASE_MIGRATION_COMPLETE.md`** - Complete implementation summary
- **`MIGRATION_READY.md`** - Configuration mode guide
- **`CONNECTION_STRING_SUPPORT.md`** - Connection string format and troubleshooting

## What Gets Migrated

The migration preserves all data including:

### Core Data
- ✅ Prompts (all fields)
- ✅ Agents (all fields)
- ✅ Workflows (all fields)
- ✅ Tools (all fields)

### UI Metadata (New!)
- ✅ **Step Positions**: x, y coordinates from `workflow_agents` table
- ✅ **Step Connections**: Visual edges from `workflow_connections` table
- ✅ **Dependencies**: Automatically derived from connections

### Schema Mapping

| Old Schema | New Schema |
|------------|------------|
| `workflow_agents.position_x, position_y` | `workflow.configuration.steps[].position.x, y` |
| `workflow_connections.source_id, target_id` | `workflow.configuration.connections[]` |
| `workflow_agents.agent_id` | `workflow.configuration.steps[].config.agent_id` |

## Migration Process

1. **Backup your data** (always!)
2. **Configure connection strings** in `migrate_live_db.sh`
3. **Run dry-run** to preview changes
4. **Execute migration** after verifying dry-run output
5. **Verify data** in target database

## Troubleshooting

### Connection Issues
- Ensure PostgreSQL client (`psql`) is installed: `sudo apt install postgresql-client`
- Check network connectivity to remote databases
- Verify firewall rules allow PostgreSQL port (5432)
- Confirm credentials are correct

### Migration Issues
- Check that source database has the expected schema
- Ensure target database doesn't already exist (or confirm overwrite)
- Review dry-run output for any warnings

## Related Documentation

- **Python Migration Script**: `python_apps/agent_studio/scripts/migrate_to_sdk_schema.py`
- **Migration Guide**: `python_apps/agent_studio/scripts/LIVE_MIGRATION_GUIDE.md`
- **SDK Documentation**: `python_packages/workflow-core-sdk/docs/`

