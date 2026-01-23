#!/bin/bash
# =============================================================================
# Destroy PR Database
# Drops the database for a closed PR environment
# =============================================================================

set -euo pipefail

# Usage: ./destroy-pr-database.sh <PR_NUMBER>

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
    exit 1
fi

DATABASE_NAME="pr_${PR_NUMBER}"

echo "Dropping database: ${DATABASE_NAME}"

# Terminate existing connections
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_ADMIN_DATABASE" \
    -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '${DATABASE_NAME}';" || true

# Drop the database
PGPASSWORD="$DB_PASSWORD" psql \
    -h "$DB_HOST" \
    -p "$DB_PORT" \
    -U "$DB_USER" \
    -d "$DB_ADMIN_DATABASE" \
    -c "DROP DATABASE IF EXISTS ${DATABASE_NAME};"

echo "✅ Database pr_${PR_NUMBER} dropped"
