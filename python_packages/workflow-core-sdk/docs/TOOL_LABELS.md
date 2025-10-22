# Tool Parameter Labels for UI

## Overview

The `@function_schema` decorator automatically generates OpenAI-compatible tool schemas with proper labels and descriptions for UI rendering. It parses Google-style docstrings to extract parameter information and uses the JSON Schema standard `title` field for UI labels.

## Features

- **Automatic Label Generation**: Converts `snake_case` parameter names to `Title Case` labels
- **Docstring Parsing**: Extracts parameter descriptions from Google-style docstrings
- **Multi-line Support**: Handles multi-line parameter descriptions correctly
- **Type Inference**: Uses Python type hints to determine parameter types
- **Required/Optional Detection**: Automatically marks parameters as required or optional based on default values
- **JSON Schema Standard**: Uses the standard `title` field (not custom extensions)

## Usage

### Basic Example

```python
from workflow_core_sdk.tools.decorators import function_schema

@function_schema
def send_email(recipient: str, subject: str, body: str) -> dict:
    """
    Send an email to a recipient.
    
    Args:
        recipient: Email address of the recipient
        subject: Subject line of the email
        body: Main content of the email message
        
    Returns:
        dict: Status of the email send operation
    """
    return {"status": "sent"}
```

### Generated Schema

The decorator generates a schema like this:

```json
{
  "type": "function",
  "function": {
    "name": "send_email",
    "description": "Send an email to a recipient...",
    "parameters": {
      "type": "object",
      "properties": {
        "recipient": {
          "type": "string",
          "title": "Recipient",
          "description": "Email address of the recipient"
        },
        "subject": {
          "type": "string",
          "title": "Subject",
          "description": "Subject line of the email"
        },
        "body": {
          "type": "string",
          "title": "Body",
          "description": "Main content of the email message"
        }
      },
      "required": ["recipient", "subject", "body"]
    }
  }
}
```

## Docstring Formats Supported

### Google Style (Recommended)

```python
@function_schema
def my_tool(param1: str, param2: int) -> str:
    """
    Tool description.
    
    Args:
        param1: Description of param1
        param2: Description of param2
        
    Returns:
        str: Return value description
    """
    pass
```

### Google Style with Type Annotations

```python
@function_schema
def my_tool(param1: str, param2: int) -> str:
    """
    Tool description.
    
    Args:
        param1 (str): Description of param1
        param2 (int): Description of param2
        
    Returns:
        str: Return value description
    """
    pass
```

### Multi-line Descriptions

```python
@function_schema
def my_tool(config: dict) -> str:
    """
    Tool description.
    
    Args:
        config: Configuration dictionary containing various settings
                including API keys, endpoints, and timeout values.
                Must be properly formatted.
        
    Returns:
        str: Result
    """
    pass
```

## UI Integration

### Accessing Labels in Frontend

```typescript
// TypeScript/JavaScript example
interface ToolParameter {
  type: string;
  title: string;        // Use this for form labels
  description: string;  // Use this for tooltips/help text
}

function renderParameterInput(paramName: string, paramInfo: ToolParameter) {
  return (
    <div className="parameter-field">
      <label>{paramInfo.title}</label>
      <input 
        type="text" 
        name={paramName}
        title={paramInfo.description}
      />
      <span className="help-text">{paramInfo.description}</span>
    </div>
  );
}
```

### Example React Component

```tsx
import React from 'react';

interface ToolParameterFormProps {
  schema: {
    function: {
      parameters: {
        properties: Record<string, {
          type: string;
          title: string;
          description: string;
        }>;
        required: string[];
      };
    };
  };
}

export function ToolParameterForm({ schema }: ToolParameterFormProps) {
  const { properties, required } = schema.function.parameters;
  
  return (
    <form>
      {Object.entries(properties).map(([paramName, paramInfo]) => (
        <div key={paramName} className="form-field">
          <label>
            {paramInfo.title}
            {required.includes(paramName) && <span className="required">*</span>}
          </label>
          <input
            type={getInputType(paramInfo.type)}
            name={paramName}
            placeholder={paramInfo.description}
            required={required.includes(paramName)}
          />
          <small className="help-text">{paramInfo.description}</small>
        </div>
      ))}
    </form>
  );
}

function getInputType(jsonType: string): string {
  switch (jsonType) {
    case 'integer':
    case 'number':
      return 'number';
    case 'boolean':
      return 'checkbox';
    default:
      return 'text';
  }
}
```

## Fallback Behavior

If a parameter is not documented in the docstring, the decorator will:

1. Generate a title by converting the parameter name from `snake_case` to `Title Case`
2. Use a generic description: `"Parameter {param_name}"`

Example:

```python
@function_schema
def undocumented_tool(api_key: str) -> str:
    return "result"

# Generated schema will have:
# {
#   "api_key": {
#     "type": "string",
#     "title": "Api Key",
#     "description": "Parameter api_key"
#   }
# }
```

## Best Practices

1. **Always document parameters**: Provide clear, concise descriptions in your docstrings
2. **Use descriptive parameter names**: Even with auto-generated titles, good names help
3. **Include type hints**: They're used to generate the correct JSON Schema types
4. **Multi-line descriptions**: Use them for complex parameters that need detailed explanations
5. **Consistent style**: Stick to Google-style docstrings for consistency

## Type Mapping

Python types are automatically mapped to JSON Schema types:

| Python Type | JSON Schema Type |
|-------------|------------------|
| `str`       | `"string"`       |
| `int`       | `"integer"`      |
| `float`     | `"number"`       |
| `bool`      | `"boolean"`      |
| `list`      | `"array"`        |
| `dict`      | `"object"`       |

## Testing

Run the test suite to verify label generation:

```bash
cd python_packages/workflow-core-sdk
pytest tests/test_tool_labels.py -v
```

## Examples

See `examples/tool_labels_example.py` for comprehensive examples of:
- Basic tools with simple parameters
- Tools with multi-line descriptions
- API integration tools
- How to use the generated schemas in UI code

Run the example:

```bash
python examples/tool_labels_example.py
```

## Migration Guide

If you have existing tools without proper docstrings:

1. Add Google-style docstrings with Args sections
2. Document each parameter with a clear description
3. The decorator will automatically generate titles and descriptions
4. Test the generated schemas to ensure they look correct

## Why JSON Schema `title` Field?

We chose to use the standard JSON Schema `title` field instead of custom extensions (like `x-label`) because:

1. **Standards Compliance**: It's part of the JSON Schema specification
2. **Tool Compatibility**: Many JSON Schema tools and validators recognize it
3. **Simplicity**: No need for custom parsing logic in the UI
4. **Future-Proof**: As a standard field, it's more likely to be supported long-term

## Related Documentation

- [Tool Decorators](./TOOL_DECORATORS.md)
- [Step API](./STEP_API.md)
- [Workflow Core SDK](./README.md)

