"""
Quick demonstration of tool parameter labels.

Run this to see how the @function_schema decorator generates
labels and descriptions from docstrings.
"""

import json
from workflow_core_sdk.tools.decorators import function_schema


@function_schema
def send_notification(
    user_id: str, message: str, priority: str = "normal", send_email: bool = True
) -> dict:
    """
    Send a notification to a user.

    Args:
        user_id: Unique identifier of the user to notify
        message: The notification message content
        priority: Priority level (low, normal, high, urgent)
        send_email: Whether to also send an email notification

    Returns:
        dict: Notification delivery status
    """
    return {"status": "sent", "user_id": user_id}


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("TOOL PARAMETER LABELS - QUICK DEMO")
    print("=" * 80 + "\n")

    schema = send_notification.openai_schema
    params = schema["function"]["parameters"]["properties"]

    print("Generated Parameter Schemas:\n")

    for param_name, param_info in params.items():
        print(f"Parameter: {param_name}")
        print(f"  ├─ Title: {param_info.get('title', 'N/A')}")
        print(f"  ├─ Type: {param_info.get('type', 'N/A')}")
        print(f"  └─ Description: {param_info.get('description', 'N/A')}")
        print()

    print("=" * 80)
    print("FULL JSON SCHEMA")
    print("=" * 80 + "\n")
    print(json.dumps(schema, indent=2))

    print("\n" + "=" * 80)
    print("HOW THE UI WOULD USE THIS")
    print("=" * 80 + "\n")

    print("React/TypeScript Example:\n")
    print("```tsx")
    print("function ToolParameterInput({ name, param }) {")
    print("  return (")
    print('    <div className="parameter-field">')
    print("      <label>{param.title}</label>  {/* Uses the 'title' field */}")
    print("      <input")
    print("        name={name}")
    print("        type={getInputType(param.type)}")
    print("        placeholder={param.description}")
    print("      />")
    print('      <span className="help-text">{param.description}</span>')
    print("    </div>")
    print("  );")
    print("}")
    print("```")

    print("\n" + "=" * 80)
    print("RENDERED FORM WOULD LOOK LIKE")
    print("=" * 80 + "\n")

    for param_name, param_info in params.items():
        required = param_name in schema["function"]["parameters"].get("required", [])
        req_marker = " *" if required else ""
        print(f"┌─ {param_info['title']}{req_marker}")
        print(f"│  [{param_info['type']} input field]")
        print(f"└─ ℹ️  {param_info['description']}")
        print()
