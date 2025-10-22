#!/bin/bash
#
# Migrate Agent Studio data to SDK schema
#
# Usage:
#   ./migrate_to_sdk.sh                    # Dry run first
#   ./migrate_to_sdk.sh --execute          # Actually perform migration
#

set -e  # Exit on error

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "🚀 Agent Studio → SDK Schema Migration"
echo ""

# Check if --execute flag is provided
if [ "$1" == "--execute" ]; then
    DRY_RUN=""
    echo "⚠️  EXECUTING MIGRATION (not a dry run)"
    echo ""
    read -p "Are you sure you want to migrate the data? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "❌ Aborted"
        exit 1
    fi
else
    DRY_RUN="--dry-run"
    echo "ℹ️  DRY RUN MODE (use --execute to actually migrate)"
fi

echo ""

# Run the migration script
python3 "${SCRIPT_DIR}/python_apps/agent_studio/scripts/migrate_to_sdk_schema.py" \
    --source agent_studio \
    --target agent_studio_sdk \
    --host localhost \
    --port 5433 \
    --user elevaite \
    --password elevaite \
    $DRY_RUN

echo ""
echo "✅ Done!"
echo ""

if [ "$1" != "--execute" ]; then
    echo "To actually perform the migration, run:"
    echo "  ./migrate_to_sdk.sh --execute"
fi

