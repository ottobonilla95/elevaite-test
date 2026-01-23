#!/bin/bash
# Smart dev startup with clear status feedback

set -e

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "                    🚀 ELEVAITE LOCAL DEVELOPMENT"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Start infrastructure first
echo "📦 Starting infrastructure (PostgreSQL, Qdrant, RabbitMQ, MinIO)..."
docker-compose -f docker-compose.dev.yaml up -d postgres qdrant rabbitmq minio

# Wait for infra
echo "⏳ Waiting for infrastructure..."
until nc -z localhost 5433 2>/dev/null; do sleep 1; done
echo "  ✅ PostgreSQL ready"
until nc -z localhost 6333 2>/dev/null; do sleep 1; done
echo "  ✅ Qdrant ready"
until nc -z localhost 5672 2>/dev/null; do sleep 1; done
echo "  ✅ RabbitMQ ready"
until nc -z localhost 9000 2>/dev/null; do sleep 1; done
echo "  ✅ MinIO ready"

echo ""
echo "🔧 Starting backend services..."
docker-compose -f docker-compose.dev.yaml up -d auth-api workflow-engine ingestion

# Check backend health with timeout
check_backend() {
    local name=$1
    local port=$2
    local max_wait=60
    local waited=0
    
    echo -n "  ⏳ $name..."
    while [ $waited -lt $max_wait ]; do
        if nc -z localhost "$port" 2>/dev/null; then
            echo -e "\r  ✅ $name ready (port $port)      "
            return 0
        fi
        # Check if container died
        if ! docker ps | grep -q "elevaite-${name,,}" 2>/dev/null; then
            echo -e "\r  ❌ $name FAILED! Container exited.      "
            echo ""
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            echo "  💥 $name CRASH LOGS:"
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            docker-compose -f docker-compose.dev.yaml logs --tail=20 "${name,,}" 2>/dev/null || true
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            return 1
        fi
        sleep 2
        waited=$((waited + 2))
    done
    echo -e "\r  ❌ $name TIMEOUT after ${max_wait}s      "
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
npx turbo run dev --filter=auth --filter=elevaite &
FRONTEND_PID=$!

# Wait for frontends
sleep 5
echo -n "  ⏳ Waiting for frontends..."
max_wait=60
waited=0
while [ $waited -lt $max_wait ]; do
    if nc -z localhost 3000 2>/dev/null && nc -z localhost 3001 2>/dev/null; then
        break
    fi
    sleep 2
    waited=$((waited + 2))
done

if nc -z localhost 3000 2>/dev/null; then
    echo ""
    echo "  ✅ Auth App ready (port 3000)"
else
    echo ""
    echo "  ⏳ Auth App still starting..."
fi

if nc -z localhost 3001 2>/dev/null; then
    echo "  ✅ Elevaite App ready (port 3001)"
else
    echo "  ⏳ Elevaite App still starting..."
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🎉 ELEVAITE IS RUNNING!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  📋 Quick Links:"
echo "     Auth App:        http://localhost:3000"
echo "     Elevaite App:    http://localhost:3001"
echo "     Auth API Docs:   http://localhost:8004/docs"
echo "     Workflow Docs:   http://localhost:8006/docs"
echo "     Qdrant UI:       http://localhost:6333/dashboard"
echo "     RabbitMQ UI:     http://localhost:15672  (elevaite/elevaite)"
echo "     MinIO Console:   http://localhost:9001   (minioadmin/minioadmin)"
echo ""
echo "  💡 Commands:"
echo "     npm run dev:logs   - View all logs"
echo "     npm run dev:down   - Stop everything"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Keep frontend running in foreground
wait $FRONTEND_PID
