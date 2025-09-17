# Dev-time path setup for local SDK within monorepo
# This allows importing `workflow_core_sdk` without pip-install during extraction.
import os
import sys

_here = os.path.dirname(__file__)
# Prefer package root (new layout); fall back to old src layout if present.
_sdk_root = os.path.abspath(os.path.join(_here, "..", "..", "python_packages", "workflow-core-sdk"))
_sdk_src = os.path.join(_sdk_root, "src")
for _p in (_sdk_root, _sdk_src):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.append(_p)
