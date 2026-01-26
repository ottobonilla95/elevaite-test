#!/bin/bash
# Smart dev startup with clear status feedback

set -e

# Check for SKIP_MIGRATIONS flag
SKIP_MIGRATIONS=${SKIP_MIGRATIONS:-false}

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "                    🚀 ELEVAITE LOCAL DEVELOPMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start infrastructure first
echo "📦 Starting infrastructure (PostgreSQL, Qdrant, RabbitMQ, MinIO)..."
docker-compose -f docker-compose.dev.yaml up -d postgres qdrant rabbitmq minio 2>&1 | grep -v "Found orphan containers" || true

# Wait for infra with live feedback
echo ""
echo "⏳ Waiting for infrastructure to be ready..."
echo ""

# PostgreSQL
echo "  🔄 PostgreSQL starting..."
elapsed=0
max_wait=30
while ! nc -z localhost 5433 2>/dev/null; do
    # Check if container is running
    if ! docker ps --format '{{.Names}}' | grep -q "elevaite-postgres"; then
        echo "  ❌ PostgreSQL container failed to start!"
        echo ""
        echo "  Checking container status..."
        docker ps -a --filter "name=elevaite-postgres" --format "table {{.Names}}\t{{.Status}}"
        echo ""
        echo "  Last 20 lines of logs:"
        docker logs elevaite-postgres 2>&1 | tail -20 | sed 's/^/     │ /'
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "  💡 Common fixes:"
        echo "     1. Port 5433 might be in use: lsof -i :5433"
        echo "     2. Remove old containers: docker-compose -f docker-compose.dev.yaml down -v"
        echo "     3. Check Docker Desktop is running"
        echo "     4. Try: npm run dev:death (nuclear reset)"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        exit 1
    fi

    sleep 1
    elapsed=$((elapsed + 1))

    if [ $elapsed -ge $max_wait ]; then
        echo "  ⚠️  PostgreSQL taking longer than expected (${elapsed}s)..."
        docker logs elevaite-postgres 2>&1 | tail -3 | sed 's/^/     │ /'
    fi
done

# Wait for PostgreSQL to accept connections (not just port open)
echo "  🔄 Waiting for PostgreSQL to accept connections..."
max_wait=10
waited=0
while ! PGPASSWORD=elevaite psql -h localhost -p 5433 -U elevaite -d postgres -c "SELECT 1" >/dev/null 2>&1; do
    sleep 1
    waited=$((waited + 1))
    if [ $waited -ge $max_wait ]; then
        echo "  ❌ PostgreSQL not accepting connections after ${max_wait}s"
        exit 1
    fi
done
echo "  ✅ PostgreSQL ready"

# Qdrant
echo "  🔄 Qdrant starting..."
until nc -z localhost 6333 2>/dev/null; do sleep 1; done
echo "  ✅ Qdrant ready"

# RabbitMQ
echo "  🔄 RabbitMQ starting..."
until nc -z localhost 5672 2>/dev/null; do sleep 1; done
echo "  ✅ RabbitMQ ready"

# MinIO
echo "  🔄 MinIO starting..."
until nc -z localhost 9000 2>/dev/null; do sleep 1; done
echo "  ✅ MinIO ready"

echo ""
echo "✅ All infrastructure services ready!"

echo ""

# Run migrations unless explicitly skipped
if [ "$SKIP_MIGRATIONS" = "true" ]; then
    echo "⏭️  Skipping database migrations (SKIP_MIGRATIONS=true)"
    echo ""
else
    echo "🗄️  Running database migrations..."
    echo "     (This may take 10-30 seconds on first run while installing dependencies...)"
    echo ""

    # Run migrations with live output (don't capture, just run)
    if bash scripts/migrate.sh all; then
        echo ""
        echo "  ✅ Database migrations completed"
        echo "  💡 Tip: Skip migrations next time with: SKIP_MIGRATIONS=true npm run dev"
        echo ""
    else
        echo ""
        echo "  ❌ Migration failed!"
        exit 1
    fi
fi

echo "🔧 Starting backend services (auth-api, workflow-engine, ingestion)..."
echo ""
docker-compose -f docker-compose.dev.yaml up -d auth-api workflow-engine ingestion 2>&1 | grep -v "Found orphan containers" || true
echo ""

# Check backend health with timeout and live logs
check_backend() {
    local name=$1
    local port=$2
    local max_wait=60
    local waited=0
    local container_name="elevaite-$(echo $name | tr '[:upper:]' '[:lower:]')"

    echo "  🔄 $name starting..."

    while [ $waited -lt $max_wait ]; do
        # Check if ready
        if nc -z localhost "$port" 2>/dev/null; then
            echo -e "  ✅ $name ready (port $port)"
            return 0
        fi

        # Check if container died
        if ! docker ps | grep -q "$container_name" 2>/dev/null; then
            echo -e "  ❌ $name FAILED! Container exited."
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "  💥 $name CRASH LOGS:"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            docker-compose -f docker-compose.dev.yaml logs --tail=30 "$(echo $name | tr '[:upper:]' '[:lower:]')" 2>/dev/null || true
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            return 1
        fi

        # Show last log line (helpful for debugging)
        if [ $((waited % 4)) -eq 0 ]; then
            log=$(docker logs "$container_name" 2>&1 | tail -1 | cut -c1-100)
            if [ -n "$log" ]; then
                echo "     └─ $(echo $log | tr -d '\n' | tr -d '\r')"
            fi
        fi

        sleep 2
        waited=$((waited + 2))
    done

    echo -e "  ❌ $name TIMEOUT after ${max_wait}s"
    echo "     Last logs:"
    docker logs "$container_name" 2>&1 | tail -10 | sed 's/^/     │ /'
    return 1
}

BACKEND_FAILED=0
check_backend "auth-api" 8004 || BACKEND_FAILED=1
check_backend "workflow-engine" 8006 || BACKEND_FAILED=1
check_backend "ingestion" 8001 || BACKEND_FAILED=1

if [ $BACKEND_FAILED -eq 1 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ⚠️  SOME BACKEND SERVICES FAILED - Fix issues and try again"
    echo "  Run: npm run dev:logs    to see full logs"
    echo "  Run: npm run dev:down    to stop everything"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    exit 1
fi

echo ""
echo "🖥️  Starting frontend apps..."

# Build UI package CSS first (required by apps)
echo "  📦 Building UI package..."
npm run --prefix packages/ui build > /dev/null 2>&1 || echo "  ⚠️  UI build warning (may be ok)"

echo "     (Starting... will show logs below)"
echo ""

# Start frontend in background initially to check ports
# Use npm run dev:frontend which loads env vars from root .env
wait-on tcp:8004 tcp:8006 tcp:8001 && dotenv -e .env -- npx turbo run dev --filter=auth --filter=elevaite > /tmp/elevaite-frontend.log 2>&1 &
FRONTEND_PID=$!

# Wait for frontends with progress
max_wait=90
waited=0
auth_ready=false
elevaite_ready=false

while [ $waited -lt $max_wait ]; do
    # Check auth app (port 3005)
    if ! $auth_ready && nc -z localhost 3005 2>/dev/null; then
        echo "  ✅ Auth App ready (port 3005)"
        auth_ready=true
    fi

    # Check elevaite app (port 3001)
    if ! $elevaite_ready && nc -z localhost 3001 2>/dev/null; then
        echo "  ✅ Elevaite App ready (port 3001)"
        elevaite_ready=true
    fi

    # Both ready? Break
    if $auth_ready && $elevaite_ready; then
        break
    fi

    # Show progress every 10 seconds
    if [ $((waited % 10)) -eq 0 ] && [ $waited -gt 0 ]; then
        if ! $auth_ready; then
            echo "  🔄 Auth App still starting... (${waited}s)"
        fi
        if ! $elevaite_ready; then
            echo "  🔄 Elevaite App still starting... (${waited}s)"
        fi
    fi

    sleep 2
    waited=$((waited + 2))
done

# Final status
if ! $auth_ready; then
    echo "  ⏳ Auth App still starting... (check logs: tail -f /tmp/elevaite-frontend.log)"
fi
if ! $elevaite_ready; then
    echo "  ⏳ Elevaite App still starting... (check logs: tail -f /tmp/elevaite-frontend.log)"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎉 ELEVAITE IS RUNNING!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📋 Quick Links:"
echo "     Auth App:         http://localhost:3005"
echo "     Elevaite App:     http://localhost:3001"
echo "     Auth API Docs:    http://localhost:8004/docs"
echo "     Workflow Docs:    http://localhost:8006/docs"
echo "     Ingestion Docs:   http://localhost:8001/docs"
echo ""
echo "  🔧 Admin Tools:"
echo "     Qdrant UI:        http://localhost:6333/dashboard"
echo "     RabbitMQ UI:      http://localhost:15672  (elevaite/elevaite)"
echo "     MinIO Console:    http://localhost:9001   (minioadmin/minioadmin)"
echo ""
echo "  💡 Useful Commands:"
echo "     npm run dev:logs        - View all container logs"
echo "     npm run dev:down        - Stop everything"
echo "     npm run migrate:status  - Check migration status"
echo "     tail -f /tmp/elevaite-frontend.log  - View frontend logs"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📺 Showing frontend logs (Ctrl+C to stop)..."
echo ""

# Cleanup on Ctrl+C - stop EVERYTHING and wait
cleanup() {
    echo ""
    echo ""
    echo "  🛑 Stopping all services..."
    echo ""
    kill $FRONTEND_PID 2>/dev/null
    wait $FRONTEND_PID 2>/dev/null
    echo "  ✅ Frontend stopped"
    echo "  🛑 Stopping Docker containers..."
    docker-compose -f docker-compose.dev.yaml down
    echo ""
    echo "  ✅ All services stopped"
    exit 0
}
trap cleanup INT TERM

# Show frontend logs in foreground (keeps terminal blocked)
tail -f /tmp/elevaite-frontend.log
