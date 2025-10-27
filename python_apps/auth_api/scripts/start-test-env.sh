#!/bin/bash
# Start test environment for Auth API integration tests

set -e

echo "🚀 Starting Auth API Test Environment"
echo "======================================"

# Change to auth_api directory
cd "$(dirname "$0")/.."

# Start Docker services
echo ""
echo "📦 Starting Docker services (PostgreSQL + MailHog + OPA)..."
docker-compose -f docker-compose.test.yaml up -d

# Wait for services to be healthy
echo ""
echo "⏳ Waiting for services to be ready..."
sleep 5

# Check PostgreSQL
echo "  ✓ Checking PostgreSQL..."
until docker exec auth-api-postgres-test pg_isready -U auth_user -d auth_db > /dev/null 2>&1; do
  echo "    Waiting for PostgreSQL..."
  sleep 2
done
echo "  ✅ PostgreSQL is ready"

# Check MailHog
echo "  ✓ Checking MailHog..."
until curl -s http://localhost:8025 > /dev/null 2>&1; do
  echo "    Waiting for MailHog..."
  sleep 2
done
echo "  ✅ MailHog is ready"

# Check OPA
echo "  ✓ Checking OPA..."
until curl -s http://localhost:8181/health > /dev/null 2>&1; do
  echo "    Waiting for OPA..."
  sleep 2
done
echo "  ✅ OPA is ready"

# Run migrations
echo ""
echo "🔄 Running database migrations..."
export $(cat .env.test | grep -v '^#' | xargs)
alembic upgrade head

echo ""
echo "✅ Test environment is ready!"
echo ""
echo "📧 MailHog Web UI: http://localhost:8025"
echo "   (All emails sent by Auth API will appear here)"
echo ""
echo "🔐 OPA (Open Policy Agent): http://localhost:8181"
echo "   Health: http://localhost:8181/health"
echo "   Policies: /policies/rbac.rego"
echo ""
echo "🗄️  PostgreSQL: localhost:5434"
echo "   Database: auth_db"
echo "   User: auth_user"
echo "   Password: auth_password"
echo ""
echo "🚀 To start Auth API with test config:"
echo "   export \$(cat .env.test | grep -v '^#' | xargs)"
echo "   python -m app.main"
echo ""
echo "🧪 To run integration tests:"
echo "   cd ../../python_packages/rbac-sdk"
echo "   pytest tests/integration/ -v"
echo ""

