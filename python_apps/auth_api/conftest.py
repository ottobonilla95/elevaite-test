"""Global pytest configuration."""

# Apply patches for third-party libraries
from app.patches import starlette_patch, passlib_patch
