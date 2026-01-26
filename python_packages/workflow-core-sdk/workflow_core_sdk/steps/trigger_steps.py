from typing import Dict, Any, List, Optional
import base64
from pathlib import Path

from workflow_core_sdk.execution_context import ExecutionContext


def _to_data_url(path: Path, mime: str) -> Optional[str]:
    try:
        with open(path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    except Exception:
        return None


async def trigger_step(
    step_config: Dict[str, Any],
    input_data: Dict[str, Any],
    execution_context: ExecutionContext,
) -> Dict[str, Any]:
    """Normalize trigger input into a standard structure under 'trigger'.

    Reads raw trigger payload placed by the router at execution_context.step_io_data['trigger_raw'].
    Returns a dict that becomes the step's output_data (stored by the engine), typically at step_id.
    """
    raw = execution_context.step_io_data.get("trigger_raw", {})
    kind = (raw.get("kind") or raw.get("trigger", {}).get("kind") or "webhook").lower()

    if kind == "chat":
        data = raw if "kind" in raw else raw.get("trigger", {})
        current_message = data.get("current_message")
        history = data.get("history", []) if data.get("need_history", True) else []
        attachments = data.get("attachments", [])
        # Accept messages directly if provided; otherwise build from history + current_message
        messages: List[Dict[str, Any]] = []
        raw_messages = data.get("messages")
        if isinstance(raw_messages, list) and raw_messages:
            for msg in raw_messages:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(
                        {"role": str(msg["role"]), "content": str(msg["content"])}
                    )
        else:
            for msg in history:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    messages.append(
                        {"role": str(msg["role"]), "content": str(msg["content"])}
                    )
            if current_message:
                messages.append({"role": "user", "content": current_message})

        # Attachments may have been preprocessed by router (paths, mime, size, data_url)
        return {
            "kind": "chat",
            "messages": messages,
            "current_message": current_message,
            "attachments": attachments,
        }

    # Default: webhook (pass-through JSON payload)
    payload = raw.get("data", raw)
    return {"kind": kind, "data": payload}
