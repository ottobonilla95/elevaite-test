.PHONY: help install test test-cov test-fast test-verbose test-debug clean lint format

help:
	@echo "RBAC SDK Test Commands"
	@echo "======================"
	@echo ""
	@echo "  make install      - Install package with test dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-cov     - Run tests with coverage report"
	@echo "  make test-fast    - Run tests in parallel (faster)"
	@echo "  make test-verbose - Run tests with verbose output"
	@echo "  make test-debug   - Run tests with debugging (stop on first failure)"
	@echo "  make clean        - Remove test artifacts and cache"
	@echo "  make lint         - Run linters (ruff, mypy)"
	@echo "  make format       - Format code with ruff"
	@echo ""

install:
	pip install -e ".[test]"

test:
	pytest

test-cov:
	pytest --cov=rbac_sdk --cov-report=term-missing --cov-report=html
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

test-fast:
	pytest -n auto

test-verbose:
	pytest -vv

test-debug:
	pytest -x --pdb

test-client:
	pytest tests/test_client.py -v

test-async-client:
	pytest tests/test_async_client.py -v

test-principal-resolvers:
	pytest tests/test_principal_resolvers.py -v

test-resource-builders:
	pytest tests/test_resource_builders.py -v

test-api-key-validators:
	pytest tests/test_api_key_validators.py -v

test-guards:
	pytest tests/test_guards.py -v

clean:
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf **/__pycache__
	rm -rf **/*.pyc
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

lint:
	@echo "Running ruff..."
	ruff check rbac_sdk tests
	@echo "Running mypy..."
	mypy rbac_sdk

format:
	ruff format rbac_sdk tests
	ruff check --fix rbac_sdk tests

