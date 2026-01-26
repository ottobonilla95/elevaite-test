#!/bin/bash

# Database Migration Status Script for ElevAIte Platform
# Shows current migration status for all services

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Suppress uv warnings for cleaner output
export UV_NO_PROGRESS=1

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
print_header() {
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}$1${NC}"
}

# Function to check migration status for a service
check_status() {
    local service=$1
    local service_path=$2
    local schema_prefix=$3

    cd "$service_path"

    # Check if alembic.ini exists
    if [ ! -f "alembic.ini" ]; then
        print_error "alembic.ini not found in $service_path"
        cd - > /dev/null
        return 1
    fi

    # If schema prefix is provided, this is a multi-tenant service
    if [ -n "$schema_prefix" ]; then
        # Get list of tenants from environment or use defaults
        TENANTS=${TENANTS:-"default toshiba iopex"}

        for tenant in $TENANTS; do
            schema="${schema_prefix}_${tenant}"
            echo ""
            print_info "Schema: $schema"

            # Get current revision
            ALEMBIC_SCHEMA=$schema uv run alembic current 2>/dev/null || print_error "Failed to get current revision"

            # Show history
            echo ""
            print_info "Recent migrations:"
            ALEMBIC_SCHEMA=$schema uv run alembic history --verbose 2>/dev/null | head -n 20 || print_error "Failed to get history"
        done
    else
        # Single schema migration
        echo ""
        print_info "Current revision:"
        uv run alembic current 2>/dev/null || print_error "Failed to get current revision"

        echo ""
        print_info "Recent migrations:"
        uv run alembic history --verbose 2>/dev/null | head -n 20 || print_error "Failed to get history"
    fi

    cd - > /dev/null
}

# Main script
ROOT_DIR=$(pwd)

echo ""
print_header "ElevAIte Migration Status"
echo ""

# Auth API
print_header "AUTH-API (Multi-tenant)"
export SQLALCHEMY_DATABASE_URL="postgresql://elevaite:elevaite@localhost:5433/auth"
check_status "auth-api" "$ROOT_DIR/python_apps/auth_api" "auth"
echo ""

# Workflow Engine
print_header "WORKFLOW-ENGINE (Multi-tenant)"
export DATABASE_URI="postgresql://elevaite:elevaite@localhost:5433/workflow_engine"
export SQLALCHEMY_DATABASE_URL="postgresql://elevaite:elevaite@localhost:5433/workflow_engine"
check_status "workflow-engine" "$ROOT_DIR/python_apps/workflow-engine-poc" "workflow"
echo ""

# Ingestion Service
print_header "INGESTION-SERVICE (Single schema)"
export DATABASE_URL="postgresql://elevaite:elevaite@localhost:5433/elevaite_ingestion"
check_status "ingestion-service" "$ROOT_DIR/python_apps/ingestion-service" ""
echo ""

print_success "Status check completed!"
echo ""
