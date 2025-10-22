# Live Database Migration Guide

This guide explains how to migrate your live Agent Studio database to the new SDK schema with UI metadata support.

## Prerequisites

1. **Live database running** with the old Agent Studio schema
2. **Target database created** for the new SDK schema
3. **Backup of your data** (recommended)

## Database Connection Details

Based on your SQL dump, your live database likely uses:
- **Host:** Your production host (or localhost for local dev)
- **Port:** 5433 (default) or your custom port
- **User:** elevaite_admin or elevaite
- **Password:** Your database password
- **Source DB:** agent_studio (or your custom name)
- **Target DB:** agent_studio_sdk (will be created if doesn't exist)

## Migration Steps

### Step 1: Verify Source Database Connection

First, verify you can connect to your live database:

```bash
# Test connection to source database
psql -U elevaite_admin -h YOUR_HOST -p 5433 -d agent_studio -c "SELECT COUNT(*) FROM workflows;"
```

If this works, you're ready to migrate!

### Step 2: Create Target Database (if needed)

The migration script will create the target database if it doesn't exist, but you can create it manually:

```bash
# Create target database
psql -U elevaite_admin -h YOUR_HOST -p 5433 -c "CREATE DATABASE agent_studio_sdk;"
```

### Step 3: Run Dry-Run Migration

**ALWAYS run a dry-run first** to see what will be migrated:

```bash
cd python_apps/agent_studio

# Dry run with default localhost settings
python scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --host localhost \
  --port 5433 \
  --user elevaite_admin \
  --password YOUR_PASSWORD \
  --dry-run
```

**For remote database:**

```bash
python scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --host YOUR_REMOTE_HOST \
  --port 5433 \
  --user elevaite_admin \
  --password YOUR_PASSWORD \
  --dry-run
```

This will show you:
- How many workflows will be migrated
- How many steps and connections per workflow
- What data will be preserved
- Any potential issues

### Step 4: Execute Migration

Once you're satisfied with the dry-run output, execute the migration:

```bash
# Execute migration (remove --dry-run flag)
python scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --host YOUR_HOST \
  --port 5433 \
  --user elevaite_admin \
  --password YOUR_PASSWORD
```

**Note:** Remove the `--dry-run` flag to actually perform the migration.

### Step 5: Verify Migration

After migration, verify the data:

```bash
# Check workflow count in target database
psql -U elevaite_admin -h YOUR_HOST -p 5433 -d agent_studio_sdk -c "SELECT COUNT(*) FROM workflow;"

# Check a sample workflow configuration
psql -U elevaite_admin -h YOUR_HOST -p 5433 -d agent_studio_sdk -c "SELECT name, configuration FROM workflow LIMIT 1;"
```

## Expected Output

### Dry-Run Output

```
🔄 Migrating workflows with UI metadata...
   Found 15 workflows to migrate
   [DRY RUN] Would migrate 15 workflows

======================================================================
MIGRATION SUMMARY
======================================================================
Prompts migrated:              0 (dry run)
Agents migrated:               0 (dry run)
Workflows migrated:            0 (dry run)
  - Workflow steps migrated:   0 (dry run)
  - Workflow connections:      0 (dry run)
Tools migrated:                0 (dry run)
======================================================================
```

### Actual Migration Output

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
  export SQLALCHEMY_DATABASE_URL='postgresql://elevaite_admin:PASSWORD@HOST:5433/agent_studio_sdk'
======================================================================
```

## Common Connection Scenarios

### Scenario 1: Local Development Database

```bash
python scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --host localhost \
  --port 5433 \
  --user elevaite \
  --password elevaite
```

### Scenario 2: Remote Production Database

```bash
python scripts/migrate_to_sdk_schema.py \
  --source agent_studio_prod \
  --target agent_studio_sdk_prod \
  --host db.yourcompany.com \
  --port 5432 \
  --user elevaite_admin \
  --password YOUR_SECURE_PASSWORD
```

### Scenario 3: Using Environment Variables

You can also set environment variables instead of command-line arguments:

```bash
export DB_HOST=localhost
export DB_PORT=5433
export DB_USER=elevaite_admin
export DB_PASSWORD=your_password

python scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk
```

## What Gets Migrated

### From `workflows` table:
- ✅ Workflow metadata (name, description, version, tags)
- ✅ Existing configuration JSON
- ✅ Status flags (is_active, is_deployed, is_editable)
- ✅ Timestamps (created_at, updated_at, deployed_at)

### From `workflow_agents` table:
- ✅ Agent positions (position_x, position_y) → `step.position.x/y`
- ✅ Node IDs → `step.step_id`
- ✅ Agent IDs → `step.config.agent_id`
- ✅ Agent configurations → merged into `step.config`

### From `workflow_connections` table:
- ✅ Source/target agent IDs → `connection.source_step_id/target_step_id`
- ✅ Connection types → `connection.connection_type`
- ✅ Connection handles → `connection.source_handle/target_handle`
- ✅ Automatic dependency derivation

### From `agents` table:
- ✅ All agent metadata and configurations

### From `prompts` table:
- ✅ All system prompts

### From `tools` table:
- ✅ All tool definitions and schemas

## Troubleshooting

### Connection Refused

```
Error: connection refused
```

**Solution:** Check that:
1. Database is running
2. Host and port are correct
3. Firewall allows connections
4. User has connection permissions

### Authentication Failed

```
Error: authentication failed for user "elevaite_admin"
```

**Solution:** Verify:
1. Username is correct
2. Password is correct
3. User exists in the database
4. User has necessary permissions

### Database Does Not Exist

```
Error: database "agent_studio" does not exist
```

**Solution:** 
1. Verify the source database name
2. Check available databases: `psql -U elevaite_admin -h HOST -p PORT -l`

### Missing Tables

```
Error: relation "workflow_agents" does not exist
```

**Solution:** 
1. Verify you're connecting to the correct source database
2. Check that the old schema tables exist
3. The dump file you have might be data-only (no schema)

## Post-Migration

After successful migration:

1. **Update your application configuration** to use the new database:
   ```bash
   export SQLALCHEMY_DATABASE_URL='postgresql://user:pass@host:port/agent_studio_sdk'
   ```

2. **Test the new database** with your application

3. **Verify UI metadata** is preserved:
   - Check that workflow steps have positions
   - Check that connections are preserved
   - Test the visual workflow editor

4. **Keep the old database** as backup until you're confident everything works

## Rollback

If you need to rollback:

1. Simply switch back to the old database URL
2. The old database remains unchanged
3. You can delete the target database and try again

## Support

If you encounter issues:

1. Check the error messages in the migration output
2. Verify database connection parameters
3. Check database logs for detailed error information
4. Review the migration script logs

## Security Notes

- **Never commit passwords** to version control
- Use environment variables for sensitive data
- Consider using `.pgpass` file for password management
- Ensure secure connections (SSL) for production databases

