#!/bin/bash
# Test runner for policy management tests
# This script runs unit, integration, and E2E tests with proper setup

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.dev.yaml"

# Test paths
UNIT_TESTS="tests/unit/test_policy_service.py"
INTEGRATION_TESTS="tests/integration/test_policy_api.py"
E2E_TESTS="tests/e2e/test_policy_management_e2e.py"

# Functions
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Parse arguments
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_E2E=false
RUN_ALL=false
WITH_COVERAGE=false
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit)
            RUN_UNIT=true
            shift
            ;;
        --integration)
            RUN_INTEGRATION=true
            shift
            ;;
        --e2e)
            RUN_E2E=true
            shift
            ;;
        --all)
            RUN_ALL=true
            shift
            ;;
        --coverage)
            WITH_COVERAGE=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit          Run unit tests only"
            echo "  --integration   Run integration tests only"
            echo "  --e2e           Run E2E tests only (requires services)"
            echo "  --all           Run all tests"
            echo "  --coverage      Generate coverage report"
            echo "  -v, --verbose   Verbose output"
            echo "  -h, --help      Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 --unit                    # Run unit tests"
            echo "  $0 --all --coverage          # Run all tests with coverage"
            echo "  $0 --e2e                     # Run E2E tests (starts services)"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Default to all if nothing specified
if [ "$RUN_UNIT" = false ] && [ "$RUN_INTEGRATION" = false ] && [ "$RUN_E2E" = false ] && [ "$RUN_ALL" = false ]; then
    RUN_ALL=true
fi

if [ "$RUN_ALL" = true ]; then
    RUN_UNIT=true
    RUN_INTEGRATION=true
    RUN_E2E=true
fi

# Build pytest command
PYTEST_CMD="pytest"
if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -v -s"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Change to project directory
cd "$PROJECT_DIR"

# Run unit tests
if [ "$RUN_UNIT" = true ]; then
    print_header "Running Unit Tests"
    
    if [ "$WITH_COVERAGE" = true ]; then
        $PYTEST_CMD $UNIT_TESTS \
            --cov=app.services.policy_service \
            --cov-report=term \
            --cov-report=html:htmlcov/unit
    else
        $PYTEST_CMD $UNIT_TESTS
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Unit tests passed"
    else
        print_error "Unit tests failed"
        exit 1
    fi
    echo ""
fi

# Run integration tests
if [ "$RUN_INTEGRATION" = true ]; then
    print_header "Running Integration Tests"
    
    if [ "$WITH_COVERAGE" = true ]; then
        $PYTEST_CMD $INTEGRATION_TESTS \
            --cov=app.routers.policies \
            --cov-report=term \
            --cov-report=html:htmlcov/integration
    else
        $PYTEST_CMD $INTEGRATION_TESTS
    fi
    
    if [ $? -eq 0 ]; then
        print_success "Integration tests passed"
    else
        print_error "Integration tests failed"
        exit 1
    fi
    echo ""
fi

# Run E2E tests
if [ "$RUN_E2E" = true ]; then
    print_header "Running E2E Tests"
    
    # Check if services are already running
    SERVICES_RUNNING=false
    if docker compose -f "$COMPOSE_FILE" ps | grep -q "Up"; then
        SERVICES_RUNNING=true
        print_info "Services already running"
    fi
    
    # Start services if not running
    if [ "$SERVICES_RUNNING" = false ]; then
        print_info "Starting services..."
        docker compose -f "$COMPOSE_FILE" up -d
        
        # Wait for services to be ready
        print_info "Waiting for services to be ready..."
        sleep 10
        
        # Check OPA health
        MAX_RETRIES=30
        RETRY_COUNT=0
        while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
            if curl -s http://localhost:8181/health > /dev/null 2>&1; then
                print_success "OPA is ready"
                break
            fi
            RETRY_COUNT=$((RETRY_COUNT + 1))
            echo -n "."
            sleep 1
        done
        echo ""
        
        if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
            print_error "OPA failed to start"
            docker compose -f "$COMPOSE_FILE" down
            exit 1
        fi
    fi
    
    # Run E2E tests
    $PYTEST_CMD $E2E_TESTS --run-e2e
    E2E_RESULT=$?
    
    # Stop services if we started them
    if [ "$SERVICES_RUNNING" = false ]; then
        print_info "Stopping services..."
        docker compose -f "$COMPOSE_FILE" down
    fi
    
    if [ $E2E_RESULT -eq 0 ]; then
        print_success "E2E tests passed"
    else
        print_error "E2E tests failed"
        exit 1
    fi
    echo ""
fi

# Summary
print_header "Test Summary"
if [ "$RUN_UNIT" = true ]; then
    print_success "Unit tests: PASSED"
fi
if [ "$RUN_INTEGRATION" = true ]; then
    print_success "Integration tests: PASSED"
fi
if [ "$RUN_E2E" = true ]; then
    print_success "E2E tests: PASSED"
fi

if [ "$WITH_COVERAGE" = true ]; then
    echo ""
    print_info "Coverage reports generated in htmlcov/"
    print_info "Open htmlcov/index.html in your browser to view"
fi

echo ""
print_success "All tests passed! 🎉"

