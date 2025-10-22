#!/bin/bash

# ============================================================================
# Live Database Migration Helper Script
# ============================================================================
# This script helps you migrate your live Agent Studio database to the new
# SDK schema with UI metadata support (positions & connections).
#
# USAGE:
#
# Option 1 - Interactive Mode (default):
#   ./migrate_live_db.sh
#   (You'll be prompted for connection details and migration mode)
#
# Option 2 - Configuration Mode:
#   1. Edit the configuration section below
#   2. Set USE_CONFIG_VALUES=true
#   3. Fill in your database connection details
#   4. Set MIGRATION_MODE to "dry-run" or "execute"
#   5. Run: ./migrate_live_db.sh
#
# RECOMMENDATION: Always run with MIGRATION_MODE="dry-run" first!
# ============================================================================

set -e  # Exit on error

# ============================================================================
# CONFIGURATION - Edit these values for your database
# ============================================================================

# Set to "true" to use the values below, or "false" to be prompted interactively
USE_CONFIG_VALUES=true

# Database connection strings (only used if USE_CONFIG_VALUES=true)
# Format: postgresql://user:password@host:port/database
SOURCE_DB_CONNECTION=""
TARGET_DB_CONNECTION="postgresql://elevaite:elevaite@localhost:5433/agent_studio"

# Migration mode: "dry-run" or "execute"
# dry-run = preview only, no changes
# execute = actually perform the migration
MIGRATION_MODE="execute"

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

# Function to parse PostgreSQL connection string
parse_connection_string() {
    local conn_string="$1"
    local var_prefix="$2"

    # Extract components using regex
    # Format: postgresql://user:password@host:port/database
    if [[ $conn_string =~ postgresql://([^:]+):([^@]+)@([^:]+):([^/]+)/(.+) ]]; then
        eval "${var_prefix}_USER=\"${BASH_REMATCH[1]}\""
        eval "${var_prefix}_PASSWORD=\"${BASH_REMATCH[2]}\""
        eval "${var_prefix}_HOST=\"${BASH_REMATCH[3]}\""
        eval "${var_prefix}_PORT=\"${BASH_REMATCH[4]}\""
        eval "${var_prefix}_DB=\"${BASH_REMATCH[5]}\""
        return 0
    else
        echo -e "${RED}Error: Invalid connection string format${NC}"
        echo -e "${RED}Expected: postgresql://user:password@host:port/database${NC}"
        return 1
    fi
}

# Check if using config values or interactive mode
if [ "$USE_CONFIG_VALUES" = "true" ]; then
    echo -e "${GREEN}Using configuration values from script${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Parse connection strings
    echo -e "${BLUE}Parsing connection strings...${NC}"

    if ! parse_connection_string "$SOURCE_DB_CONNECTION" "SOURCE"; then
        exit 1
    fi

    if ! parse_connection_string "$TARGET_DB_CONNECTION" "TARGET"; then
        exit 1
    fi

    # Set variables for compatibility with rest of script
    # (psql commands use DB_HOST, DB_PORT, etc. for source connection)
    DB_HOST="$SOURCE_HOST"
    DB_PORT="$SOURCE_PORT"
    DB_USER="$SOURCE_USER"
    DB_PASSWORD="$SOURCE_PASSWORD"
    # SOURCE_DB and TARGET_DB are already set by parse_connection_string

    echo -e "${BLUE}Connection Details:${NC}"
    echo -e "${BLUE}  Source: $SOURCE_USER@$SOURCE_HOST:$SOURCE_PORT/$SOURCE_DB${NC}"
    echo -e "${BLUE}  Target: $TARGET_USER@$TARGET_HOST:$TARGET_PORT/$TARGET_DB${NC}"
    echo -e "${BLUE}  Mode:   $MIGRATION_MODE${NC}"
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

# Check if psql is available
if ! command -v psql &> /dev/null; then
    echo -e "${YELLOW}⚠️  psql not found, skipping connection test${NC}"
    echo -e "${YELLOW}   The migration script will test the connection${NC}"
else
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
if [ "$USE_CONFIG_VALUES" = "true" ]; then
    # Use connection URLs
    MIGRATION_CMD="python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
      --source-url '$SOURCE_DB_CONNECTION' \
      --target-url '$TARGET_DB_CONNECTION' \
      $DRY_RUN_FLAG"
else
    # Use individual parameters
    MIGRATION_CMD="python python_apps/agent_studio/scripts/migrate_to_sdk_schema.py \
      --source $SOURCE_DB \
      --target $TARGET_DB \
      --host $DB_HOST \
      --port $DB_PORT \
      --user $DB_USER \
      --password $DB_PASSWORD \
      $DRY_RUN_FLAG"
fi

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
        echo "To execute the actual migration, run this script again and choose option 2."
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

