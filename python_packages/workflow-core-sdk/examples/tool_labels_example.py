"""
Example: Tool Parameter Labels and Descriptions

This example demonstrates how to use the @function_schema decorator to automatically
generate OpenAI-compatible tool schemas with proper labels and descriptions for UI rendering.

The decorator parses Google-style docstrings to extract:
- Parameter titles (for UI labels)
- Parameter descriptions (for tooltips/help text)
- Parameter types (from type hints)
- Required vs optional parameters

Key features:
1. Uses JSON Schema standard `title` field for UI labels
2. Automatically converts snake_case to Title Case
3. Supports multi-line parameter descriptions
4. Works with Google-style docstrings (with or without type annotations)
"""

import json
from workflow_core_sdk.tools.decorators import function_schema


# Example 1: Basic tool with simple parameters
@function_schema
def send_email(
    recipient: str,
    subject: str,
    body: str,
    cc: str = None,
    bcc: str = None
) -> dict:
    """
    Send an email to one or more recipients.
    
    Args:
        recipient: Email address of the primary recipient
        subject: Subject line of the email
        body: Main content of the email message
        cc: Carbon copy recipients (comma-separated)
        bcc: Blind carbon copy recipients (comma-separated)
        
    Returns:
        dict: Status of the email send operation
    """
    return {"status": "sent", "recipient": recipient}


# Example 2: Tool with complex multi-line descriptions
@function_schema
def create_database_backup(
    database_name: str,
    backup_location: str,
    compression_level: int = 5,
    include_logs: bool = True
) -> str:
    """
    Create a backup of a database with optional compression.
    
    This tool creates a full backup of the specified database and stores it
    in the designated location with optional compression.
    
    Args:
        database_name: Name of the database to backup. Must be a valid
                      database identifier that exists in the current server.
        backup_location: Full path where the backup file should be stored.
                        The directory must exist and be writable.
        compression_level: Level of compression to apply (0-9). Higher values
                          result in smaller files but take longer to create.
                          Default is 5 for balanced performance.
        include_logs: Whether to include transaction logs in the backup.
                     Including logs allows point-in-time recovery.
                     
    Returns:
        str: Path to the created backup file
    """
    return f"/backups/{database_name}.bak"


# Example 3: Tool with type annotations in docstring (Google style)
@function_schema
def search_products(
    query: str,
    category: str = "all",
    min_price: float = 0.0,
    max_price: float = None,
    in_stock_only: bool = False
) -> list:
    """
    Search for products in the catalog.
    
    Args:
        query (str): Search query string to match against product names and descriptions
        category (str): Product category to filter by (e.g., "electronics", "clothing")
        min_price (float): Minimum price filter in USD
        max_price (float): Maximum price filter in USD
        in_stock_only (bool): Only return products that are currently in stock
        
    Returns:
        list: List of matching products with details
    """
    return []


# Example 4: API integration tool
@function_schema
def call_external_api(
    endpoint: str,
    method: str = "GET",
    headers: dict = None,
    body: dict = None,
    timeout: int = 30
) -> dict:
    """
    Make an HTTP request to an external API.
    
    Args:
        endpoint: Full URL of the API endpoint to call
        method: HTTP method to use (GET, POST, PUT, DELETE, PATCH)
        headers: Optional HTTP headers to include in the request
        body: Request body data (for POST/PUT/PATCH requests)
        timeout: Request timeout in seconds
        
    Returns:
        dict: API response data
    """
    return {"status": 200, "data": {}}


def print_schema_info(tool_func):
    """Helper function to print schema information in a readable format."""
    schema = tool_func.openai_schema
    print(f"\n{'='*80}")
    print(f"Tool: {schema['function']['name']}")
    print(f"{'='*80}")
    print(f"\nDescription: {schema['function']['description'][:100]}...")
    print(f"\nParameters:")
    
    params = schema['function']['parameters']['properties']
    required = schema['function']['parameters'].get('required', [])
    
    for param_name, param_info in params.items():
        req_marker = " (required)" if param_name in required else " (optional)"
        print(f"\n  {param_name}{req_marker}:")
        print(f"    Title: {param_info.get('title', 'N/A')}")
        print(f"    Type: {param_info.get('type', 'N/A')}")
        print(f"    Description: {param_info.get('description', 'N/A')}")


def main():
    """Demonstrate the tool schema generation."""
    
    print("\n" + "="*80)
    print("TOOL PARAMETER LABELS DEMONSTRATION")
    print("="*80)
    
    # Show schemas for all example tools
    tools = [
        send_email,
        create_database_backup,
        search_products,
        call_external_api
    ]
    
    for tool in tools:
        print_schema_info(tool)
    
    # Show full JSON schema for one tool
    print(f"\n{'='*80}")
    print("FULL JSON SCHEMA EXAMPLE (send_email)")
    print(f"{'='*80}\n")
    print(json.dumps(send_email.openai_schema, indent=2))
    
    # Demonstrate how UI can use the title field
    print(f"\n{'='*80}")
    print("HOW UI CAN USE THIS DATA")
    print(f"{'='*80}\n")
    
    params = send_email.openai_schema['function']['parameters']['properties']
    print("Example form rendering:\n")
    
    for param_name, param_info in params.items():
        title = param_info.get('title', param_name)
        description = param_info.get('description', '')
        param_type = param_info.get('type', 'string')
        
        print(f"  <label>{title}</label>")
        print(f"  <input type=\"text\" name=\"{param_name}\" title=\"{description}\" />")
        print(f"  <span class=\"help-text\">{description}</span>")
        print()


if __name__ == "__main__":
    main()

