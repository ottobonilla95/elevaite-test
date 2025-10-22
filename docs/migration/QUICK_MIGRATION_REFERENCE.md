# Quick Migration Reference

## TL;DR - Migrate Your Live Database

### Option 1: Configuration Mode (Easiest - No Typing!)

**Step 1:** Edit `migrate_live_db.sh` and set your connection details at the top:

```bash
# Set to "true" to use the values below
USE_CONFIG_VALUES=true

# Your database connection details
DB_HOST="localhost"
DB_PORT="5433"
DB_USER="elevaite_admin"
DB_PASSWORD="your_password_here"
SOURCE_DB="agent_studio"
TARGET_DB="agent_studio_sdk"

# Start with dry-run!
MIGRATION_MODE="dry-run"
```

**Step 2:** Run the script:

```bash
./migrate_live_db.sh
```

That's it! No prompts, no typing. It will use your configured values.

### Option 2: Interactive Mode

If you prefer to be prompted for each value:

```bash
./migrate_live_db.sh
```

(Keep `USE_CONFIG_VALUES=false` in the script)

This will:
1. ✅ Prompt you for connection details
2. ✅ Test the connection
3. ✅ Show you what will be migrated
4. ✅ Let you choose dry-run or execute
5. ✅ Migrate with UI metadata support

### Option 3: Direct Python Command

If you prefer to run the Python script directly:

**Dry-run (preview only):**
```bash
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --host YOUR_HOST \
  --port 5433 \
  --user YOUR_USER \
  --password YOUR_PASSWORD \
  --dry-run
```

**Execute migration:**
```bash
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --host YOUR_HOST \
  --port 5433 \
  --user YOUR_USER \
  --password YOUR_PASSWORD
```

## Quick Setup

**Copy the example configuration:**
```bash
cp migrate_live_db.example.sh migrate_live_db.sh
```

**Edit your connection details:**
```bash
nano migrate_live_db.sh  # or use your favorite editor
```

**Run it:**
```bash
./migrate_live_db.sh
```

## What Gets Migrated

| Source | Target | What |
|--------|--------|------|
| `workflows` table | `workflow` table | Workflow metadata |
| `workflow_agents` table | `workflow.configuration.steps[].position` | Step positions (x, y) |
| `workflow_connections` table | `workflow.configuration.connections[]` | Visual connections |
| `agents` table | `agent` table | All agents |
| `prompts` table | `prompt` table | All prompts |
| `tools` table | `tool` table | All tools |

## Connection Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `--source` | `agent_studio` | Source database name |
| `--target` | `agent_studio_sdk` | Target database name |
| `--host` | `localhost` | Database host |
| `--port` | `5433` | Database port |
| `--user` | `elevaite` | Database user |
| `--password` | `elevaite` | Database password |
| `--dry-run` | (none) | Preview mode, no changes |

## Common Scenarios

### Local Development
```bash
./migrate_live_db.sh
# Use defaults: localhost, port 5433, user elevaite
```

### Remote Production
```bash
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --source agent_studio_prod \
  --target agent_studio_sdk_prod \
  --host db.yourcompany.com \
  --port 5432 \
  --user admin \
  --password YOUR_SECURE_PASSWORD
```

### Different Port
```bash
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --port 5432 \
  --dry-run
```

## Verification

After migration, verify:

```bash
# Check workflow count
psql -h HOST -p PORT -U USER -d agent_studio_sdk \
  -c "SELECT COUNT(*) FROM workflow;"

# Check UI metadata
psql -h HOST -p PORT -U USER -d agent_studio_sdk \
  -c "SELECT name, configuration->'steps'->0->'position' as first_step_position FROM workflow LIMIT 1;"

# Check connections
psql -h HOST -p PORT -U USER -d agent_studio_sdk \
  -c "SELECT name, jsonb_array_length(configuration->'connections') as connection_count FROM workflow;"
```

## Troubleshooting

| Error | Solution |
|-------|----------|
| Connection refused | Check host, port, and firewall |
| Authentication failed | Verify username and password |
| Database does not exist | Check database name |
| Table does not exist | Verify you're connecting to the right database |

## Post-Migration

Update your app to use the new database:

```bash
export SQLALCHEMY_DATABASE_URL='postgresql://user:pass@host:port/agent_studio_sdk'
```

Or in your `.env` file:
```
SQLALCHEMY_DATABASE_URL=postgresql://user:pass@host:port/agent_studio_sdk
```

## Rollback

The old database is **not modified**. To rollback:

1. Switch back to old database URL
2. Delete target database if needed: `DROP DATABASE agent_studio_sdk;`
3. Try migration again

## Support Files

- 📖 **Detailed Guide:** `python_apps/agent_studio/scripts/LIVE_MIGRATION_GUIDE.md`
- 🔧 **Migration Script:** `python_apps/agent_studio/scripts/migrate_to_sdk_schema.py`
- 🚀 **Helper Script:** `migrate_live_db.sh`
- 📝 **Implementation Details:** `MIGRATION_UI_METADATA_UPDATE.md`

