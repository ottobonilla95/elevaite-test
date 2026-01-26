#!/bin/bash

# Database Migration Script for ElevAIte Platform
# Runs Alembic migrations for all services or specific service

set -e

# Suppress uv warnings for cleaner output
export UV_NO_PROGRESS=1

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Load environment variables safely
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

# Set default database URLs for local development if not set
export DATABASE_URI=${DATABASE_URI:-"postgresql://elevaite:elevaite@localhost:5433/auth"}
export DATABASE_URL=${DATABASE_URL:-"postgresql://elevaite:elevaite@localhost:5433/elevaite_ingestion"}
export SQLALCHEMY_DATABASE_URL=${SQLALCHEMY_DATABASE_URL:-"postgresql://elevaite:elevaite@localhost:5433/workflow_engine"}

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Function to run migrations for a service
run_migration() {
    local service=$1
    local service_path=$2
    local schema_prefix=$3

    print_info "Running migrations for $service..."

    cd "$service_path"

    # Check if alembic.ini exists
    if [ ! -f "alembic.ini" ]; then
        print_error "alembic.ini not found in $service_path"
        return 1
    fi

    # If schema prefix is provided, this is a multi-tenant service
    if [ -n "$schema_prefix" ]; then
        # Get list of tenants from environment or use defaults
        TENANTS=${TENANTS:-"default toshiba iopex"}

        for tenant in $TENANTS; do
            schema="${schema_prefix}_${tenant}"
            print_info "Migrating schema: $schema"

            # Determine database name based on schema prefix
            if [ "$schema_prefix" = "auth" ]; then
                db_name="auth"
            elif [ "$schema_prefix" = "workflow" ]; then
                db_name="workflow_engine"
            else
                db_name="postgres"
            fi

            # Create schema if it doesn't exist
            echo "Creating schema $schema in database $db_name..." >&2
            if PGPASSWORD=elevaite psql -h localhost -p 5433 -U elevaite -d "$db_name" -c "CREATE SCHEMA IF NOT EXISTS $schema" 2>&1 | grep -q "CREATE SCHEMA\|already exists"; then
                echo "Schema $schema ready" >&2
            else
                print_error "Failed to create schema $schema"
                return 1
            fi

            # Run migration with schema override
            # Export vars for the command
            export ALEMBIC_SCHEMA=$schema

            if uv run alembic upgrade head >/dev/null 2>&1; then
                print_success "$schema migration completed"
            else
                print_error "Migration failed for $schema"
                uv run alembic upgrade head 2>&1 | tail -10 >&2
                return 1
            fi
        done
    else
        # Single schema migration
        if uv run alembic upgrade head 2>&1 >/dev/null; then
            print_success "$service migration completed"
        else
            print_error "Migration failed for $service"
            return 1
        fi
    fi

    cd - > /dev/null
}

# Main script
SERVICE=${1:-"all"}
ROOT_DIR=$(pwd)

case $SERVICE in
    "auth"|"auth-api")
        print_info "Migrating auth-api (multi-tenant)..."
        export SQLALCHEMY_DATABASE_URL="postgresql://elevaite:elevaite@localhost:5433/auth"
        run_migration "auth-api" "$ROOT_DIR/python_apps/auth_api" "auth"
        ;;

    "workflow"|"workflow-engine"|"workflow-engine-poc")
        print_info "Migrating workflow-engine (multi-tenant)..."
        # Set DATABASE_URI for workflow-engine (needed by workflow_core_sdk imports)
        export DATABASE_URI="postgresql://elevaite:elevaite@localhost:5433/workflow_engine"
        export SQLALCHEMY_DATABASE_URL="postgresql://elevaite:elevaite@localhost:5433/workflow_engine"
        run_migration "workflow-engine" "$ROOT_DIR/python_apps/workflow-engine-poc" "workflow"
        ;;

    "ingestion"|"ingestion-service")
        print_info "Migrating ingestion-service (single schema)..."
        export DATABASE_URL="postgresql://elevaite:elevaite@localhost:5433/elevaite_ingestion"
        run_migration "ingestion-service" "$ROOT_DIR/python_apps/ingestion-service" ""
        ;;

    "all")
        print_info "Running migrations for all services..."
        echo ""

        # Auth API
        export SQLALCHEMY_DATABASE_URL="postgresql://elevaite:elevaite@localhost:5433/auth"
        run_migration "auth-api" "$ROOT_DIR/python_apps/auth_api" "auth"
        echo ""

        # Workflow Engine
        export DATABASE_URI="postgresql://elevaite:elevaite@localhost:5433/workflow_engine"
        export SQLALCHEMY_DATABASE_URL="postgresql://elevaite:elevaite@localhost:5433/workflow_engine"
        run_migration "workflow-engine" "$ROOT_DIR/python_apps/workflow-engine-poc" "workflow"
        echo ""

        # Ingestion Service
        export DATABASE_URL="postgresql://elevaite:elevaite@localhost:5433/elevaite_ingestion"
        run_migration "ingestion-service" "$ROOT_DIR/python_apps/ingestion-service" ""
        echo ""

        print_success "All migrations completed successfully!"
        ;;

    *)
        print_error "Unknown service: $SERVICE"
        echo ""
        echo "Usage: $0 [service]"
        echo ""
        echo "Services:"
        echo "  auth              Run auth-api migrations"
        echo "  workflow          Run workflow-engine migrations"
        echo "  ingestion         Run ingestion-service migrations"
        echo "  all               Run all migrations (default)"
        echo ""
        echo "Environment variables:"
        echo "  TENANTS           Space-separated list of tenant names (default: 'default toshiba iopex')"
        echo ""
        exit 1
        ;;
esac
