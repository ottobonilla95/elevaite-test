#!/bin/bash
# =============================================================================
# Create PR Database
# Creates a new database for a PR environment on the shared dev PostgreSQL
# =============================================================================

set -euo pipefail

# Usage: ./create-pr-database.sh <PR_NUMBER>

PR_NUMBER="${1:-}"

if [[ -z "$PR_NUMBER" ]]; then
    echo "Usage: $0 <PR_NUMBER>"
    echo "Example: $0 123"
    exit 1
fi

# Database connection (from environment or Terraform outputs)
DB_HOST="${DB_HOST:-}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-elevaite}"
DB_PASSWORD="${DB_PASSWORD:-}"
DB_ADMIN_DATABASE="${DB_ADMIN_DATABASE:-elevaite_dev}"

if [[ -z "$DB_HOST" || -z "$DB_PASSWORD" ]]; then
    echo "Error: DB_HOST and DB_PASSWORD must be set"
    echo "Set these from Terraform outputs or environment variables"
    exit 1
fi

DATABASE_NAME="pr_${PR_NUMBER}"

echo "Creating database: ${DATABASE_NAME}"

# Create the database
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_ADMIN_DATABASE" \
    -c "CREATE DATABASE ${DATABASE_NAME};" || {
        echo "Database may already exist, continuing..."
    }

echo "Running migrations for PR ${PR_NUMBER}..."

# Set DATABASE_URL for migrations
export DATABASE_URL="postgresql://${DB_USER}:${DB_PASSWORD}@${DB_HOST}:${DB_PORT}/${DATABASE_NAME}?sslmode=require"

# Run Alembic migrations
cd "$(dirname "$0")/../../python_apps/workflow-engine-poc"
uv run alembic upgrade head

echo "✅ Database pr_${PR_NUMBER} created and migrated"
echo ""
echo "Connection string:"
echo "  postgresql://${DB_USER}@${DB_HOST}:${DB_PORT}/${DATABASE_NAME}?sslmode=require"
