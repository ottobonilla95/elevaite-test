# ✅ Connection String Support Added!

## Summary

The migration script now supports **full PostgreSQL connection strings** instead of individual parameters. You can now paste your complete connection URLs directly into the script!

## What Changed

### 1. Bash Script (`migrate_live_db.sh`)
- Now accepts full PostgreSQL connection URLs
- Parses them using regex to extract components
- Supports passwords with special characters (like `[[`, `~`, etc.)

### 2. Python Script (`migrate_to_sdk_schema.py`)
- Added `--source-url` and `--target-url` parameters
- Uses regex-based parsing to handle special characters in passwords
- Supports separate connection parameters for source and target databases
- Backward compatible with individual parameters

## Your Configuration

Based on your edits, your configuration is:

```bash
USE_CONFIG_VALUES=true

SOURCE_DB_CONNECTION="postgresql://elevaite_admin:1R_6byQw~8[[@10.0.255.130:5432/agent_studio"
TARGET_DB_CONNECTION="postgresql://elevaite:elevaite@localhost:5433/agent_studio_test"

MIGRATION_MODE="dry-run"
```

This will:
- ✅ Connect to **remote source** at `10.0.255.130:5432` as `elevaite_admin`
- ✅ Connect to **local target** at `localhost:5433` as `elevaite`
- ✅ Handle the special characters in your password (`~`, `[[`)
- ✅ Run in dry-run mode (no changes)

## How to Use

### Step 1: Your configuration is already set!

You've already edited `migrate_live_db.sh` with:
- `USE_CONFIG_VALUES=true`
- Your source and target connection strings
- `MIGRATION_MODE="dry-run"`

### Step 2: Run the script

```bash
./migrate_live_db.sh
```

That's it! The script will:
1. Parse your connection strings
2. Connect to the remote source database
3. Connect to the local target database
4. Show you what will be migrated (dry-run mode)

### Step 3: Review the output

The script will show:
- Connection details (parsed from your URLs)
- Number of workflows, agents, connections found
- What would be migrated

### Step 4: Execute the migration

If the dry-run looks good, change:

```bash
MIGRATION_MODE="execute"
```

And run again:

```bash
./migrate_live_db.sh
```

## Connection String Format

```
postgresql://user:password@host:port/database
```

**Examples:**

```bash
# Local database
postgresql://elevaite:elevaite@localhost:5433/agent_studio

# Remote database
postgresql://admin:mypassword@db.example.com:5432/production_db

# With special characters in password
postgresql://user:p@ssw0rd!~#$@host:5432/database

# IP address
postgresql://elevaite_admin:1R_6byQw~8[[@10.0.255.130:5432/agent_studio
```

## Special Character Support

The regex-based parser handles special characters in passwords, including:
- `~` (tilde)
- `[` `]` (brackets)
- `!` `@` `#` `$` `%` `^` `&` `*` (symbols)
- And more!

**Note:** The only character that might cause issues is `@` in the password, since it's used as a delimiter. If your password contains `@`, you'll need to URL-encode it as `%40`.

## Command-Line Usage

You can also use connection strings directly from the command line:

```bash
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --source-url "postgresql://user:pass@host:port/source_db" \
  --target-url "postgresql://user:pass@host:port/target_db" \
  --dry-run
```

## Backward Compatibility

The old parameter-based approach still works:

```bash
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --host localhost \
  --port 5433 \
  --user elevaite \
  --password elevaite \
  --dry-run
```

Or with separate source/target parameters:

```bash
python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --source agent_studio \
  --target agent_studio_sdk \
  --source-host 10.0.255.130 \
  --source-port 5432 \
  --source-user elevaite_admin \
  --source-password "1R_6byQw~8[[" \
  --target-host localhost \
  --target-port 5433 \
  --target-user elevaite \
  --target-password elevaite \
  --dry-run
```

## What Gets Migrated

From your remote source database (`10.0.255.130:5432/agent_studio`):
- ✅ All workflows with metadata
- ✅ Workflow agents with positions (x, y coordinates)
- ✅ Workflow connections (visual edges)
- ✅ All agents
- ✅ All prompts
- ✅ All tools

To your local target database (`localhost:5433/agent_studio_test`):
- ✅ New SDK schema structure
- ✅ All data preserved
- ✅ UI metadata maintained

## Testing Your Setup

Run a dry-run to test:

```bash
./migrate_live_db.sh
```

Expected output:

```
╔════════════════════════════════════════════════════════════╗
║   Agent Studio → SDK Schema Migration Helper             ║
║   With UI Metadata Support (Positions & Connections)      ║
╚════════════════════════════════════════════════════════════╝

Using configuration values from script
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Parsing connection strings...

Connection Details:
  Source: elevaite_admin@10.0.255.130:5432/agent_studio
  Target: elevaite@localhost:5433/agent_studio_test
  Mode:   dry-run

Step 2: Test Connection
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Testing connection to source database...
✅ Successfully connected to source database: agent_studio
   Found:
   - X workflows
   - Y workflow agents (with positions)
   - Z workflow connections

Running in DRY-RUN mode (no changes will be made)

[... migration preview ...]
```

## Troubleshooting

### Connection Refused

If you get "connection refused" for the remote database:
- Check that the remote host is accessible
- Verify firewall rules allow connections
- Ensure PostgreSQL is configured to accept remote connections

### Authentication Failed

If authentication fails:
- Double-check the username and password in your connection string
- Verify the user has permissions on the source database

### Invalid URL Format

If you get "Invalid PostgreSQL URL format":
- Ensure the format is: `postgresql://user:password@host:port/database`
- Check for typos in the connection string

## Files Modified

1. ✅ `migrate_live_db.sh` - Updated to parse and use connection strings
2. ✅ `python_apps/agent_studio/scripts/migrate_to_sdk_schema.py` - Added URL parsing and separate target connection support

## Next Steps

1. **Run the dry-run** (your config is already set):
   ```bash
   ./migrate_live_db.sh
   ```

2. **Review the output** to ensure it looks correct

3. **Execute the migration** by changing `MIGRATION_MODE="execute"` and running again

4. **Verify the migration** in your target database

You're all set! Your connection strings are configured and ready to use! 🎉

