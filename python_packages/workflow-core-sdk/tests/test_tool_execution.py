"""
Tests for tool execution through the workflow engine.

This test suite verifies that:
1. Tools can be resolved by name from the registry
2. Tools can be executed with proper parameters
3. Tool execution returns expected results
4. All migrated tools are accessible
"""

import json
from workflow_core_sdk.tools.basic_tools import get_all_tools, get_all_schemas


def test_tool_registry_loaded():
    """Test that the tool registry is properly loaded."""
    tools = get_all_tools()
    schemas = get_all_schemas()

    # SDK should have 25 migrated tools (10 basic + 3 kevel + 6 servicenow + 3 salesforce + 3 database)
    assert len(tools) >= 25, f"Expected at least 25 tools, got {len(tools)}"
    assert len(schemas) >= 25, f"Expected at least 25 schemas, got {len(schemas)}"

    # Tools and schemas should match
    assert len(tools) == len(schemas), "Tool count and schema count should match"


def test_basic_tools_available():
    """Test that basic SDK tools are available."""
    tools = get_all_tools()

    basic_tools = [
        "add_numbers",
        "get_current_time",
        "print_to_console",
        "weather_forecast",
        "web_search",
        "url_to_markdown",
        "calculate",
        "file_operations",
        "json_operations",
        "environment_info",
    ]

    for tool_name in basic_tools:
        assert tool_name in tools, f"Basic tool '{tool_name}' not found in registry"
        assert callable(tools[tool_name]), f"Tool '{tool_name}' is not callable"


def test_kevel_tools_available():
    """Test that Kevel tools are available."""
    tools = get_all_tools()

    kevel_tools = ["kevel_get_sites", "kevel_get_ad_types", "kevel_debug_api"]

    for tool_name in kevel_tools:
        assert tool_name in tools, f"Kevel tool '{tool_name}' not found in registry"
        assert callable(tools[tool_name]), f"Tool '{tool_name}' is not callable"


def test_servicenow_tools_available():
    """Test that ServiceNow tools are available."""
    tools = get_all_tools()

    servicenow_tools = [
        "servicenow_itsm_create_incident",
        "servicenow_itsm_get_incident",
        "servicenow_itsm_update_incident",
        "servicenow_csm_create_case",
        "servicenow_csm_get_case",
        "servicenow_csm_update_case",
    ]

    for tool_name in servicenow_tools:
        assert tool_name in tools, f"ServiceNow tool '{tool_name}' not found in registry"
        assert callable(tools[tool_name]), f"Tool '{tool_name}' is not callable"


def test_salesforce_tools_available():
    """Test that Salesforce tools are available."""
    tools = get_all_tools()

    # Only the migrated Salesforce CSM tools should be in SDK
    # Extended tools (get_salesforce_accounts, etc.) are registered by agent-studio
    salesforce_tools = ["salesforce_csm_create_case", "salesforce_csm_get_case", "salesforce_csm_update_case"]

    for tool_name in salesforce_tools:
        assert tool_name in tools, f"Salesforce tool '{tool_name}' not found in registry"
        assert callable(tools[tool_name]), f"Tool '{tool_name}' is not callable"


def test_database_tools_available():
    """Test that database tools are available."""
    tools = get_all_tools()

    database_tools = ["redis_cache_operation", "postgres_query", "sql_database"]

    for tool_name in database_tools:
        assert tool_name in tools, f"Database tool '{tool_name}' not found in registry"
        assert callable(tools[tool_name]), f"Tool '{tool_name}' is not callable"


def test_sdk_only_has_migrated_tools():
    """Test that SDK only contains migrated tools (no agent-studio tools yet)."""
    tools = get_all_tools()

    # These tools should NOT be in the SDK (they're registered by agent-studio at runtime)
    agent_studio_only_tools = [
        "calculate_mitie_quote",
        "generate_mitie_pdf",
        "document_search",
        "image_generation",
        "get_salesforce_accounts",  # Extended salesforce tools
        "ServiceNow_ITSM",  # Old monolithic tools
        "ServiceNow_CSM",
        "Salesforce_CSM",
    ]

    for tool_name in agent_studio_only_tools:
        assert tool_name not in tools, f"Tool '{tool_name}' should not be in SDK (registered by agent-studio at runtime)"


def test_tool_schemas_valid():
    """Test that all tool schemas are valid OpenAI function schemas."""
    schemas = get_all_schemas()

    for tool_name, schema in schemas.items():
        # Check basic schema structure
        assert "type" in schema, f"Tool '{tool_name}' schema missing 'type'"
        assert schema["type"] == "function", f"Tool '{tool_name}' schema type should be 'function'"

        assert "function" in schema, f"Tool '{tool_name}' schema missing 'function'"
        func_schema = schema["function"]

        assert "name" in func_schema, f"Tool '{tool_name}' schema missing 'name'"
        assert "description" in func_schema, f"Tool '{tool_name}' schema missing 'description'"
        assert "parameters" in func_schema, f"Tool '{tool_name}' schema missing 'parameters'"

        # Check parameters structure
        params = func_schema["parameters"]
        assert "type" in params, f"Tool '{tool_name}' parameters missing 'type'"
        assert params["type"] == "object", f"Tool '{tool_name}' parameters type should be 'object'"
        assert "properties" in params, f"Tool '{tool_name}' parameters missing 'properties'"


def test_basic_tool_execution():
    """Test that basic tools can be executed."""
    tools = get_all_tools()

    # Test add_numbers
    add_numbers = tools["add_numbers"]
    result = add_numbers(a=5, b=3)
    assert isinstance(result, str), "add_numbers should return a string"
    assert "8" in result, f"Result should contain '8', got '{result}'"

    # Test get_current_time
    get_current_time = tools["get_current_time"]
    result = get_current_time()
    assert isinstance(result, str), "get_current_time should return a string"
    assert len(result) > 0, "get_current_time should return non-empty string"

    # Test print_to_console
    print_to_console = tools["print_to_console"]
    result = print_to_console(message="test message")
    assert isinstance(result, str), "print_to_console should return a string"


def test_database_tool_execution():
    """Test that database tools can be executed (mock mode)."""
    tools = get_all_tools()

    # Test redis_cache_operation
    redis_tool = tools["redis_cache_operation"]
    result = redis_tool(operation="get", key="test_key")
    assert isinstance(result, str), "redis_cache_operation should return a string"
    # Result might be plain text or JSON, just verify it's a non-empty string
    assert len(result) > 0, "redis_cache_operation should return non-empty string"


def test_kevel_tool_execution():
    """Test that Kevel tools can be executed (will fail without API key, but should be callable)."""
    tools = get_all_tools()

    # Test kevel_get_sites - should return error about missing API key
    kevel_get_sites = tools["kevel_get_sites"]
    result = kevel_get_sites()
    assert isinstance(result, str), "kevel_get_sites should return a string"

    # Should be valid JSON
    data = json.loads(result)
    # Either success or error about missing API key
    assert "error" in data or "sites" in data


def test_servicenow_tool_execution():
    """Test that ServiceNow tools can be executed (mock connector)."""
    tools = get_all_tools()

    # Test servicenow_itsm_get_incident (correct parameter name is 'identifier')
    get_incident = tools["servicenow_itsm_get_incident"]
    result = get_incident(identifier="INC0000001", identifier_type="number")
    assert isinstance(result, str), "servicenow_itsm_get_incident should return a string"

    # Should be valid JSON
    data = json.loads(result)
    assert "success" in data or "error" in data or "message" in data


def test_salesforce_tool_execution():
    """Test that Salesforce tools can be executed (mock connector)."""
    tools = get_all_tools()

    # Test salesforce_csm_get_case (correct parameter name is 'identifier')
    get_case = tools["salesforce_csm_get_case"]
    result = get_case(identifier="00001000", identifier_type="case_number")
    assert isinstance(result, str), "salesforce_csm_get_case should return a string"

    # Should be valid JSON
    data = json.loads(result)
    assert "success" in data or "error" in data or "message" in data


def test_tool_parameter_extraction():
    """Test that tool parameters can be extracted from schemas."""
    schemas = get_all_schemas()

    # Test add_numbers schema
    add_numbers_schema = schemas["add_numbers"]
    params = add_numbers_schema["function"]["parameters"]["properties"]

    assert "a" in params, "add_numbers should have parameter 'a'"
    assert "b" in params, "add_numbers should have parameter 'b'"
    assert params["a"]["type"] == "integer", "Parameter 'a' should be integer"
    assert params["b"]["type"] == "integer", "Parameter 'b' should be integer"


def test_no_duplicate_tools():
    """Test that there are no duplicate tools in the registry."""
    tools = get_all_tools()
    get_all_schemas()

    # Tool names should be unique (dict keys are unique by definition)
    # But let's verify that migrated tools aren't duplicated
    tool_names = list(tools.keys())
    assert len(tool_names) == len(set(tool_names)), "Tool names should be unique"

    # Check that we don't have both old and new versions of the same tool
    # For example, we shouldn't have both "ServiceNow_ITSM" and "servicenow_itsm_create_incident"
    # (The wrapper should filter out the old ones)
    assert "ServiceNow_ITSM" not in tools, "Old ServiceNow_ITSM tool should be filtered out"
    assert "ServiceNow_CSM" not in tools, "Old ServiceNow_CSM tool should be filtered out"
    assert "Salesforce_CSM" not in tools, "Old Salesforce_CSM tool should be filtered out"


def test_all_tools_return_strings():
    """Test that all tools return strings (as per SDK pattern)."""
    tools = get_all_tools()

    # Test a sample of tools to ensure they return strings
    test_cases = [
        ("add_numbers", {"a": 1, "b": 2}),
        ("get_current_time", {}),
        ("print_to_console", {"message": "test"}),
    ]

    for tool_name, params in test_cases:
        if tool_name in tools:
            result = tools[tool_name](**params)
            assert isinstance(result, str), f"Tool '{tool_name}' should return a string, got {type(result)}"


if __name__ == "__main__":
    # Run tests manually
    print("Running tool execution tests...\n")

    test_tool_registry_loaded()
    print("✅ Tool registry loaded")

    test_basic_tools_available()
    print("✅ Basic tools available")

    test_kevel_tools_available()
    print("✅ Kevel tools available")

    test_servicenow_tools_available()
    print("✅ ServiceNow tools available")

    test_salesforce_tools_available()
    print("✅ Salesforce tools available")

    test_database_tools_available()
    print("✅ Database tools available")

    test_sdk_only_has_migrated_tools()
    print("✅ SDK only has migrated tools (agent-studio tools excluded)")

    test_tool_schemas_valid()
    print("✅ Tool schemas valid")

    test_basic_tool_execution()
    print("✅ Basic tool execution works")

    test_database_tool_execution()
    print("✅ Database tool execution works")

    test_kevel_tool_execution()
    print("✅ Kevel tool execution works")

    test_servicenow_tool_execution()
    print("✅ ServiceNow tool execution works")

    test_salesforce_tool_execution()
    print("✅ Salesforce tool execution works")

    test_tool_parameter_extraction()
    print("✅ Tool parameter extraction works")

    test_no_duplicate_tools()
    print("✅ No duplicate tools")

    test_all_tools_return_strings()
    print("✅ All tools return strings")

    print("\n🎉 All tests passed!")
