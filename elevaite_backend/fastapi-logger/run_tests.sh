#!/bin/bash

# Exit on error
set -e

# Check for AWS credentials
if [ -z "$AWS_ACCESS_KEY_ID" ] || [ -z "$AWS_SECRET_ACCESS_KEY" ]; then
  echo "AWS credentials not found in environment variables."
  echo "Please set the following environment variables:"
  echo "  - AWS_ACCESS_KEY_ID"
  echo "  - AWS_SECRET_ACCESS_KEY"
  echo "  - AWS_REGION (optional, defaults to us-east-1)"
  exit 1
fi

# Install the package in development mode
pip install -e ".[test]"

# Run the tests
python -m unittest discover -s tests