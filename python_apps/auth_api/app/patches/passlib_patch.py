"""Patch for Passlib to avoid using the deprecated crypt module."""

import sys
from unittest.mock import MagicMock

# Create a mock crypt module to prevent passlib from importing the real one
sys.modules["crypt"] = MagicMock()
sys.modules["crypt"].crypt = MagicMock()
