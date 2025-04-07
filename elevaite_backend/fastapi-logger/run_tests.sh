#!/bin/bash

# Exit on error
set -e

# Parse command line arguments
AWS_REQUIRED=true
OTEL_TEST=false
DECORATOR_TEST=false

while [[ "$#" -gt 0 ]]; do
  case $1 in
    --no-aws-check) AWS_REQUIRED=false; shift ;;
    --with-otel) OTEL_TEST=true; shift ;;
    --with-decorators) DECORATOR_TEST=true; shift ;;
    *) echo "Unknown parameter: $1"; exit 1 ;;
  esac
done

# Check for AWS credentials if required
if [ "$AWS_REQUIRED" = true ] && ([ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]); then
  echo "AWS credentials not found in environment variables."
  echo "Please set the following environment variables:"
  echo "  - AWS_ACCESS_KEY_ID"
  echo "  - AWS_SECRET_ACCESS_KEY"
  echo "  - AWS_REGION (optional, defaults to us-east-1)"
  echo ""
  echo "If you want to skip AWS credential check, run with: --no-aws-check"
  exit 1
fi

# Install Python with uv if not installed
uv python install 3.11

# Install the package in development mode
uv pip install -e ".[test]"

# Run regular tests
echo "Running standard tests..."
python -m unittest discover -s tests

# Run decorator example if requested
if [ "$DECORATOR_TEST" = true ]; then
  echo ""
  echo "Running decorator example..."
  echo "Starting example server - press Ctrl+C to stop after testing"
  python examples/decorator_example.py
fi

# Run OpenTelemetry example if requested
if [ "$OTEL_TEST" = true ]; then
  echo ""
  echo "Running OpenTelemetry example..."
  echo "Make sure you have an OpenTelemetry collector running (such as Jaeger)."
  echo "Starting example server - press Ctrl+C to stop after testing"
  python examples/opentelemetry_example.py
fi