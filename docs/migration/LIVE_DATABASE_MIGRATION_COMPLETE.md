# Live Database Migration - Complete Implementation

## Summary

The migration script has been **fully updated** to support migrating your **live Agent Studio database** directly to the new SDK schema with complete UI metadata preservation.

## What Was Completed

### ✅ 1. Enhanced Migration Script
- **File:** `python_apps/agent_studio/scripts/migrate_to_sdk_schema.py`
- **Updated:** `migrate_workflows()` method to migrate UI metadata from live database
- **Supports:** Direct connection to live databases via command-line parameters

### ✅ 2. UI Metadata Migration
- Migrates `workflow_agents` table → step positions
- Migrates `workflow_connections` table → visual connections
- Preserves connection handles and types
- Automatically derives step dependencies

### ✅ 3. Interactive Helper Script
- **File:** `migrate_live_db.sh`
- Interactive prompts for connection details
- Tests connection before migration
- Shows preview of what will be migrated
- Supports dry-run and execute modes

### ✅ 4. Comprehensive Documentation
- **Live Migration Guide:** `python_apps/agent_studio/scripts/LIVE_MIGRATION_GUIDE.md`
- **Quick Reference:** `QUICK_MIGRATION_REFERENCE.md`
- **Implementation Details:** `MIGRATION_UI_METADATA_UPDATE.md`

### ✅ 5. Testing
- **Test Script:** `python_apps/agent_studio/scripts/test_migration_ui_metadata.py`
- All tests passing ✅
- Verified migration logic works correctly

## How to Use

### Quick Start (Recommended)

```bash
# Run the interactive helper script
./migrate_live_db.sh
```

This will guide you through:
1. Entering connection details
2. Testing the connection
3. Previewing what will be migrated
4. Choosing dry-run or execute mode
5. Running the migration

### Manual Command

```bash
# Dry-run first (always recommended)
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --host YOUR_HOST \
  --port 5433 \
  --user YOUR_USER \
  --password YOUR_PASSWORD \
  --dry-run

# Then execute
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --host YOUR_HOST \
  --port 5433 \
  --user YOUR_USER \
  --password YOUR_PASSWORD
```

## Connection Parameters

The script supports these parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--source` | `agent_studio` | Source database name |
| `--target` | `agent_studio_sdk` | Target database name |
| `--host` | `localhost` | Database host |
| `--port` | `5433` | Database port |
| `--user` | `elevaite` | Database user |
| `--password` | `elevaite` | Database password |
| `--dry-run` | (none) | Preview mode |

## What Gets Migrated

### From Live Database Tables

**workflows table:**
- ✅ Workflow metadata (name, description, version)
- ✅ Configuration JSON
- ✅ Status flags (is_active, is_deployed, is_editable)
- ✅ Tags and timestamps

**workflow_agents table:**
- ✅ `position_x`, `position_y` → `step.position.x`, `step.position.y`
- ✅ `node_id` → `step.step_id`
- ✅ `agent_id` → `step.config.agent_id`
- ✅ `agent_config` → merged into `step.config`

**workflow_connections table:**
- ✅ `source_agent_id`, `target_agent_id` → `connection.source_step_id`, `connection.target_step_id`
- ✅ `connection_type` → `connection.connection_type`
- ✅ `source_handle`, `target_handle` → preserved
- ✅ Automatic dependency derivation

**agents table:**
- ✅ All agent metadata and configurations

**prompts table:**
- ✅ All system prompts

**tools table:**
- ✅ All tool definitions and schemas

## Migration Output Example

```
🔄 Migrating workflows with UI metadata...
   Found 15 workflows to migrate
   📍 Migrated 3 steps and 2 connections for workflow 'Media Planning Flow'
   📍 Migrated 2 steps and 1 connections for workflow 'Customer Support'
   📍 Migrated 1 steps and 0 connections for workflow 'RAG Agent'
   ✅ Migrated 15 workflows with UI metadata

======================================================================
MIGRATION SUMMARY
======================================================================
Prompts migrated:              25
Agents migrated:               50
Workflows migrated:            15
  - Workflow steps migrated:   45
  - Workflow connections:      28
Tools migrated:                30

✅ Migration completed successfully!

📍 UI Metadata Migration:
   - Step positions preserved from workflow_agents table
   - Connections preserved from workflow_connections table

To use the new database:
  export SQLALCHEMY_DATABASE_URL='postgresql://user:pass@host:port/agent_studio_sdk'
======================================================================
```

## Verification

After migration, verify the data:

```bash
# Check workflow count
psql -h HOST -p PORT -U USER -d agent_studio_sdk \
  -c "SELECT COUNT(*) FROM workflow;"

# Check UI metadata is preserved
psql -h HOST -p PORT -U USER -d agent_studio_sdk \
  -c "SELECT name, configuration->'steps'->0->'position' FROM workflow LIMIT 1;"

# Check connections
psql -h HOST -p PORT -U USER -d agent_studio_sdk \
  -c "SELECT name, jsonb_array_length(configuration->'connections') FROM workflow;"
```

## Safety Features

### ✅ Dry-Run Mode
- Preview what will be migrated
- No changes made to any database
- Shows counts and sample data

### ✅ Source Database Unchanged
- Migration only reads from source
- Source database is never modified
- Safe to run multiple times

### ✅ Connection Testing
- Helper script tests connection before migration
- Shows what data exists in source
- Validates credentials

### ✅ Error Handling
- Detailed error messages
- Transaction rollback on failure
- Traceback for debugging

## Post-Migration Steps

1. **Update Application Configuration**
   ```bash
   export SQLALCHEMY_DATABASE_URL='postgresql://user:pass@host:port/agent_studio_sdk'
   ```

2. **Verify Migration**
   - Check workflow counts match
   - Verify UI metadata is preserved
   - Test workflows in new database

3. **Test Application**
   - Run your application with new database
   - Test workflow execution
   - Verify visual workflow editor works

4. **Keep Old Database as Backup**
   - Don't delete old database immediately
   - Keep it until you're confident
   - Easy rollback if needed

## Rollback Procedure

If you need to rollback:

1. **Switch back to old database:**
   ```bash
   export SQLALCHEMY_DATABASE_URL='postgresql://user:pass@host:port/agent_studio'
   ```

2. **Delete target database (optional):**
   ```bash
   psql -h HOST -p PORT -U USER -c "DROP DATABASE agent_studio_sdk;"
   ```

3. **Try migration again with fixes**

## Files Created/Modified

### Modified
1. ✅ `python_apps/agent_studio/scripts/migrate_to_sdk_schema.py`
   - Enhanced `migrate_workflows()` method
   - Added UI metadata migration logic
   - Updated statistics tracking

### Created
1. ✅ `migrate_live_db.sh` - Interactive helper script
2. ✅ `python_apps/agent_studio/scripts/LIVE_MIGRATION_GUIDE.md` - Detailed guide
3. ✅ `QUICK_MIGRATION_REFERENCE.md` - Quick reference
4. ✅ `LIVE_DATABASE_MIGRATION_COMPLETE.md` - This file
5. ✅ `python_apps/agent_studio/scripts/test_migration_ui_metadata.py` - Test script

## Key Features

### 🎯 Direct Live Database Connection
- No need to restore dumps
- Connect directly to running database
- Works with local or remote databases

### 📍 Complete UI Metadata Preservation
- Step positions (x, y coordinates)
- Visual connections between steps
- Connection handles and types
- Automatic dependency derivation

### 🔒 Safe and Reversible
- Dry-run mode for preview
- Source database never modified
- Easy rollback procedure
- Transaction-based migration

### 📊 Comprehensive Reporting
- Detailed progress output
- Statistics for all migrated data
- Error messages with tracebacks
- Validation after migration

## Next Steps

1. **Review the documentation:**
   - Read `QUICK_MIGRATION_REFERENCE.md` for quick start
   - Read `LIVE_MIGRATION_GUIDE.md` for detailed instructions

2. **Run a dry-run:**
   ```bash
   ./migrate_live_db.sh
   # Choose option 1 (dry-run)
   ```

3. **Execute the migration:**
   ```bash
   ./migrate_live_db.sh
   # Choose option 2 (execute)
   ```

4. **Verify and test:**
   - Check the migrated data
   - Test your application
   - Verify UI metadata is preserved

## Success! 🎉

You can now migrate your live Agent Studio database directly to the new SDK schema with complete UI metadata preservation!

All workflow positions and connections will be preserved, ensuring your visual workflow layouts remain intact in the new system.

