# Dev-time path setup for local SDK within monorepo
# This allows importing `workflow_core_sdk` without pip-install during extraction.
import os
import sys

_here = os.path.dirname(__file__)
_sdk_src = os.path.abspath(os.path.join(_here, "..", "..", "python_packages", "workflow-core-sdk", "src"))
if os.path.isdir(_sdk_src) and _sdk_src not in sys.path:
    sys.path.append(_sdk_src)
