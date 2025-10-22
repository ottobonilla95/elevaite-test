#!/bin/bash
# Database migration helper script for workflow-core-sdk

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if alembic is installed
if ! command -v alembic &> /dev/null; then
    echo -e "${RED}Error: alembic is not installed${NC}"
    echo "Install it with: pip install alembic"
    exit 1
fi

# Function to print usage
usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  upgrade       - Apply all pending migrations"
    echo "  downgrade     - Rollback one migration"
    echo "  current       - Show current migration version"
    echo "  history       - Show migration history"
    echo "  create <msg>  - Create a new migration"
    echo "  help          - Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  SQLALCHEMY_DATABASE_URL - Database connection string"
    echo "                            Default: postgresql://elevaite:elevaite@localhost:5433/agent_studio_2"
    exit 1
}

# Get command
COMMAND=${1:-help}

case "$COMMAND" in
    upgrade)
        echo -e "${GREEN}Applying migrations...${NC}"
        alembic upgrade head
        echo -e "${GREEN}✅ Migrations applied successfully${NC}"
        ;;
    
    downgrade)
        echo -e "${YELLOW}Rolling back one migration...${NC}"
        alembic downgrade -1
        echo -e "${GREEN}✅ Rollback complete${NC}"
        ;;
    
    current)
        echo -e "${GREEN}Current migration version:${NC}"
        alembic current
        ;;
    
    history)
        echo -e "${GREEN}Migration history:${NC}"
        alembic history --verbose
        ;;
    
    create)
        if [ -z "$2" ]; then
            echo -e "${RED}Error: Migration message required${NC}"
            echo "Usage: $0 create <message>"
            exit 1
        fi
        echo -e "${GREEN}Creating new migration: $2${NC}"
        alembic revision --autogenerate -m "$2"
        echo -e "${GREEN}✅ Migration created${NC}"
        echo -e "${YELLOW}⚠️  Remember to review the generated migration file!${NC}"
        ;;
    
    help|--help|-h)
        usage
        ;;
    
    *)
        echo -e "${RED}Error: Unknown command '$COMMAND'${NC}"
        echo ""
        usage
        ;;
esac

