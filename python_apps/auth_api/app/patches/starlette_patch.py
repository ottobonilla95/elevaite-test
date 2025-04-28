"""Patch for Starlette to use python-multipart instead of multipart."""

import sys
from importlib.util import find_spec

# Check if python-multipart is installed
if find_spec("python_multipart"):
    # Create a module alias
    sys.modules["multipart"] = __import__("python_multipart")
