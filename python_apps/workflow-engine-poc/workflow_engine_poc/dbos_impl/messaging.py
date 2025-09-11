from __future__ import annotations

from typing import Final

# Central helper to keep topic format consistent across engine and routers
_SUFFIX_USER_MSG: Final[str] = "user_msg"


def make_decision_topic(execution_id: str, step_id: str, *, suffix: str | None = None) -> str:
    """Construct a topic for user message decisions targeting a paused step.

    Example: wf:{execution_id}:{step_id}:user_msg
    """
    sfx = suffix or _SUFFIX_USER_MSG
    return f"wf:{execution_id}:{step_id}:{sfx}"

