#!/bin/bash

# ============================================================================
# Live Database Migration - Example Configuration
# ============================================================================
# This is an example showing how to configure the migration script.
# 
# TO USE THIS:
# 1. Copy this file: cp migrate_live_db.example.sh migrate_live_db.sh
# 2. Edit migrate_live_db.sh with your actual connection details
# 3. Run: ./migrate_live_db.sh
# ============================================================================

set -e  # Exit on error

# ============================================================================
# CONFIGURATION - Edit these values for your database
# ============================================================================

# Set to "true" to use the values below, or "false" to be prompted interactively
USE_CONFIG_VALUES=true

# Database connection details
DB_HOST="localhost"              # Your database host
DB_PORT="5433"                   # Your database port
DB_USER="elevaite_admin"         # Your database user
DB_PASSWORD="your_password_here" # Your database password
SOURCE_DB="agent_studio"         # Source database name (old schema)
TARGET_DB="agent_studio_sdk"     # Target database name (new schema)

# Migration mode: "dry-run" or "execute"
# ALWAYS start with "dry-run" to preview what will be migrated!
MIGRATION_MODE="dry-run"

# ============================================================================
# EXAMPLE CONFIGURATIONS
# ============================================================================

# Example 1: Local Development Database
# USE_CONFIG_VALUES=true
# DB_HOST="localhost"
# DB_PORT="5433"
# DB_USER="elevaite"
# DB_PASSWORD="elevaite"
# SOURCE_DB="agent_studio"
# TARGET_DB="agent_studio_sdk"
# MIGRATION_MODE="dry-run"

# Example 2: Remote Production Database (Dry-Run)
# USE_CONFIG_VALUES=true
# DB_HOST="db.yourcompany.com"
# DB_PORT="5432"
# DB_USER="admin"
# DB_PASSWORD="secure_password_123"
# SOURCE_DB="agent_studio_prod"
# TARGET_DB="agent_studio_sdk_prod"
# MIGRATION_MODE="dry-run"

# Example 3: Execute Migration (After dry-run looks good)
# USE_CONFIG_VALUES=true
# DB_HOST="localhost"
# DB_PORT="5433"
# DB_USER="elevaite_admin"
# DB_PASSWORD="your_password"
# SOURCE_DB="agent_studio"
# TARGET_DB="agent_studio_sdk"
# MIGRATION_MODE="execute"

# ============================================================================
# END CONFIGURATION
# ============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values for interactive mode
DEFAULT_HOST="localhost"
DEFAULT_PORT="5433"
DEFAULT_USER="elevaite_admin"
DEFAULT_SOURCE_DB="agent_studio"
DEFAULT_TARGET_DB="agent_studio_sdk"

echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   Agent Studio → SDK Schema Migration Helper             ║${NC}"
echo -e "${BLUE}║   With UI Metadata Support (Positions & Connections)      ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Function to prompt for input with default
prompt_with_default() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"
    
    read -p "$(echo -e ${YELLOW}${prompt}${NC} [${default}]: )" input
    eval $var_name="${input:-$default}"
}

# Function to prompt for password
prompt_password() {
    local prompt="$1"
    local var_name="$2"
    
    read -s -p "$(echo -e ${YELLOW}${prompt}${NC}: )" password
    echo ""
    eval $var_name="$password"
}

# Check if using config values or interactive mode
if [ "$USE_CONFIG_VALUES" = "true" ]; then
    echo -e "${GREEN}Using configuration values from script${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo -e "${BLUE}Connection Details:${NC}"
    echo -e "${BLUE}  Host:        $DB_HOST${NC}"
    echo -e "${BLUE}  Port:        $DB_PORT${NC}"
    echo -e "${BLUE}  User:        $DB_USER${NC}"
    echo -e "${BLUE}  Source DB:   $SOURCE_DB${NC}"
    echo -e "${BLUE}  Target DB:   $TARGET_DB${NC}"
    echo -e "${BLUE}  Mode:        $MIGRATION_MODE${NC}"
    echo ""
else
    # Gather connection details
    echo -e "${GREEN}Step 1: Database Connection Details${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    prompt_with_default "Database Host" "$DEFAULT_HOST" "DB_HOST"
    prompt_with_default "Database Port" "$DEFAULT_PORT" "DB_PORT"
    prompt_with_default "Database User" "$DEFAULT_USER" "DB_USER"
    prompt_password "Database Password" "DB_PASSWORD"
    prompt_with_default "Source Database Name" "$DEFAULT_SOURCE_DB" "SOURCE_DB"
    prompt_with_default "Target Database Name" "$DEFAULT_TARGET_DB" "TARGET_DB"
fi

echo ""
echo -e "${GREEN}Step 2: Test Connection${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test source database connection
echo -e "${BLUE}Testing connection to source database...${NC}"
export PGPASSWORD="$DB_PASSWORD"

if psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$SOURCE_DB" -c "SELECT 1;" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Successfully connected to source database: $SOURCE_DB${NC}"
    
    # Get workflow count
    WORKFLOW_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$SOURCE_DB" -t -c "SELECT COUNT(*) FROM workflows;" 2>/dev/null | xargs)
    AGENT_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$SOURCE_DB" -t -c "SELECT COUNT(*) FROM workflow_agents;" 2>/dev/null | xargs)
    CONNECTION_COUNT=$(psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$SOURCE_DB" -t -c "SELECT COUNT(*) FROM workflow_connections;" 2>/dev/null | xargs)
    
    echo -e "${BLUE}   Found:${NC}"
    echo -e "${BLUE}   - $WORKFLOW_COUNT workflows${NC}"
    echo -e "${BLUE}   - $AGENT_COUNT workflow agents (with positions)${NC}"
    echo -e "${BLUE}   - $CONNECTION_COUNT workflow connections${NC}"
else
    echo -e "${RED}❌ Failed to connect to source database: $SOURCE_DB${NC}"
    echo -e "${RED}   Please check your connection details and try again.${NC}"
    exit 1
fi

echo ""

# Determine migration mode
if [ "$USE_CONFIG_VALUES" = "true" ]; then
    # Use configured mode
    DRY_RUN_FLAG=""
    if [ "$MIGRATION_MODE" = "dry-run" ]; then
        DRY_RUN_FLAG="--dry-run"
        echo -e "${BLUE}Running in DRY-RUN mode (no changes will be made)${NC}"
    else
        echo -e "${YELLOW}Running in EXECUTE mode (will migrate data)${NC}"
    fi
else
    # Ask user for mode
    echo -e "${GREEN}Step 3: Migration Mode${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Choose migration mode:"
    echo "  1) Dry-run (preview what will be migrated, no changes)"
    echo "  2) Execute migration (actually migrate the data)"
    echo ""

    read -p "$(echo -e ${YELLOW}Enter choice [1-2]${NC}: )" MODE_CHOICE

    DRY_RUN_FLAG=""
    if [ "$MODE_CHOICE" = "1" ]; then
        DRY_RUN_FLAG="--dry-run"
        echo -e "${BLUE}Running in DRY-RUN mode (no changes will be made)${NC}"
    elif [ "$MODE_CHOICE" = "2" ]; then
        echo -e "${YELLOW}⚠️  WARNING: This will migrate data to the target database!${NC}"
        read -p "$(echo -e ${YELLOW}Are you sure you want to proceed? [y/N]${NC}: )" CONFIRM
        if [ "$CONFIRM" != "y" ] && [ "$CONFIRM" != "Y" ]; then
            echo -e "${RED}Migration cancelled.${NC}"
            exit 0
        fi
    else
        echo -e "${RED}Invalid choice. Exiting.${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}Step 4: Running Migration${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Build migration command
MIGRATION_CMD="python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
  --source $SOURCE_DB \
  --target $TARGET_DB \
  --host $DB_HOST \
  --port $DB_PORT \
  --user $DB_USER \
  --password $DB_PASSWORD \
  $DRY_RUN_FLAG"

echo -e "${BLUE}Executing migration...${NC}"
echo ""

# Run migration
if eval $MIGRATION_CMD; then
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║   ✅ Migration Completed Successfully!                     ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
    
    if [ -z "$DRY_RUN_FLAG" ]; then
        echo ""
        echo -e "${BLUE}Next Steps:${NC}"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "1. Update your application to use the new database:"
        echo ""
        echo -e "${YELLOW}   export SQLALCHEMY_DATABASE_URL='postgresql://$DB_USER:****@$DB_HOST:$DB_PORT/$TARGET_DB'${NC}"
        echo ""
        echo "2. Verify the migration:"
        echo ""
        echo -e "${YELLOW}   psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $TARGET_DB -c 'SELECT COUNT(*) FROM workflow;'${NC}"
        echo ""
        echo "3. Test your workflows in the new database"
        echo ""
        echo "4. Keep the old database as backup until you're confident"
        echo ""
    else
        echo ""
        echo -e "${BLUE}This was a DRY-RUN. No changes were made.${NC}"
        echo ""
        echo "To execute the actual migration:"
        echo "  1. Edit the script and set MIGRATION_MODE=\"execute\""
        echo "  2. Run the script again: ./migrate_live_db.sh"
        echo ""
    fi
else
    echo ""
    echo -e "${RED}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${RED}║   ❌ Migration Failed                                      ║${NC}"
    echo -e "${RED}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
    echo -e "${RED}Please check the error messages above and try again.${NC}"
    exit 1
fi

# Clean up password from environment
unset PGPASSWORD

