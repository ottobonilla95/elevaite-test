# Agent Studio Tests

This directory contains all organized tests for the Agent Studio API. Tests have been collected from various locations and organized into logical categories.

## Test Structure

```
tests/
├── analytics/          # Analytics component tests
├── workflows/          # Workflow API and async tests  
├── functional/         # API endpoint and feature tests
├── integration/        # Cross-component integration tests
├── unit/              # Individual component unit tests
├── conftest.py        # Shared test fixtures and configuration
└── README.md          # This file
```

## Test Categories

### 📊 Analytics Tests (`tests/analytics/`)
- Unit tests for analytics components
- Analytics service testing
- Metrics and tracking functionality

### 🔄 Workflow Tests (`tests/workflows/`)
- Workflow API tests
- Async workflow functionality
- Comprehensive workflow scenarios
- Workflow deployment and management

### 🧪 Functional Tests (`tests/functional/`)
- API endpoint tests
- Demo functionality tests
- Tool endpoint tests
- End-to-end feature testing

### 🔗 Integration Tests (`tests/integration/`)
- Cross-component integration
- Redis integration tests
- MCP (Model Context Protocol) integration
- Tool registry integration

### ⚙️ Unit Tests (`tests/unit/`)
- Individual component tests
- Service layer tests
- Agent-specific tests
- Utility function tests

## Running Tests

Use the test runner script for organized test execution:

```bash
# Run all tests
python run_tests.py

# Run specific categories
python run_tests.py --unit
python run_tests.py --workflows
python run_tests.py --analytics-unit
python run_tests.py --functional
python run_tests.py --integration

# Run with coverage
python run_tests.py --coverage

# Quick test suite (critical tests only)
python run_tests.py --quick
```

## Test Overview

To see a detailed overview of all available tests:

```bash
python test_overview.py
```

## Test Configuration

- **pytest.ini**: Main pytest configuration with markers and settings
- **conftest.py**: Shared fixtures and test setup
- **test_requirements.txt**: Test-specific dependencies

## Adding New Tests

1. Place tests in the appropriate category directory
2. Follow the naming convention: `test_*.py`
3. Use appropriate pytest markers
4. Update this README if adding new categories

## Test Markers

Available pytest markers:
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests  
- `@pytest.mark.functional` - Functional tests
- `@pytest.mark.workflows` - Workflow tests
- `@pytest.mark.analytics` - Analytics tests
- `@pytest.mark.slow` - Slow-running tests
- `@pytest.mark.tool_storage` - Tool storage tests
- `@pytest.mark.tool_registry` - Tool registry tests
- `@pytest.mark.tool_api` - Tool API tests
