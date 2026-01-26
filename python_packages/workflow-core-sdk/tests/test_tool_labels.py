"""
Tests for tool parameter labels and descriptions from docstrings.
"""

import json
from workflow_core_sdk.tools.decorators import function_schema


def test_basic_docstring_parsing():
    """Test that basic parameter labels and descriptions are extracted."""

    @function_schema
    def example_tool(api_key: str, max_results: int = 10) -> str:
        """
        Example tool for testing docstring parsing.

        Args:
            api_key: Your API key for authentication
            max_results: Maximum number of results to return

        Returns:
            str: The result
        """
        return f"Using {api_key} with max {max_results}"

    schema = example_tool.openai_schema

    # Check that the schema has the correct structure
    assert schema["type"] == "function"
    assert schema["function"]["name"] == "example_tool"

    # Check parameters
    params = schema["function"]["parameters"]["properties"]

    # Check api_key parameter
    assert "api_key" in params
    assert params["api_key"]["type"] == "string"
    assert params["api_key"]["title"] == "Api Key"
    assert params["api_key"]["description"] == "Your API key for authentication"

    # Check max_results parameter
    assert "max_results" in params
    assert params["max_results"]["type"] == "integer"
    assert params["max_results"]["title"] == "Max Results"
    assert params["max_results"]["description"] == "Maximum number of results to return"

    # Check required fields
    assert "api_key" in schema["function"]["parameters"]["required"]
    assert "max_results" not in schema["function"]["parameters"]["required"]


def test_google_style_with_types():
    """Test Google-style docstrings with type annotations."""

    @function_schema
    def search_tool(query: str, limit: int, include_metadata: bool = False) -> dict:
        """
        Search for items in the database.

        Args:
            query (str): The search query string
            limit (int): Maximum number of items to return
            include_metadata (bool): Whether to include metadata in results

        Returns:
            dict: Search results
        """
        return {"query": query, "limit": limit}

    schema = search_tool.openai_schema
    params = schema["function"]["parameters"]["properties"]

    assert params["query"]["title"] == "Query"
    assert params["query"]["description"] == "The search query string"

    assert params["limit"]["title"] == "Limit"
    assert params["limit"]["description"] == "Maximum number of items to return"

    assert params["include_metadata"]["title"] == "Include Metadata"
    assert (
        params["include_metadata"]["description"]
        == "Whether to include metadata in results"
    )


def test_multiline_descriptions():
    """Test that multi-line parameter descriptions are handled correctly."""

    @function_schema
    def complex_tool(config: dict) -> str:
        """
        A tool with complex parameter descriptions.

        Args:
            config: Configuration dictionary containing various settings
                    including API keys, endpoints, and timeout values.
                    Must be properly formatted.

        Returns:
            str: Result
        """
        return "done"

    schema = complex_tool.openai_schema
    params = schema["function"]["parameters"]["properties"]

    assert params["config"]["title"] == "Config"
    # Multi-line description should be collapsed to single line
    assert "Configuration dictionary" in params["config"]["description"]
    assert "API keys" in params["config"]["description"]
    # Should not have excessive whitespace
    assert "  " not in params["config"]["description"]


def test_fallback_for_missing_docstring():
    """Test that tools without docstrings still get reasonable defaults."""

    @function_schema
    def undocumented_tool(some_param: str, another_param: int) -> str:
        return "result"

    schema = undocumented_tool.openai_schema
    params = schema["function"]["parameters"]["properties"]

    # Should still generate titles from parameter names
    assert params["some_param"]["title"] == "Some Param"
    assert params["some_param"]["description"] == "Parameter some_param"

    assert params["another_param"]["title"] == "Another Param"
    assert params["another_param"]["description"] == "Parameter another_param"


def test_snake_case_to_title_case():
    """Test that snake_case parameter names are converted to Title Case."""

    @function_schema
    def naming_test(user_api_key: str, max_retry_count: int) -> str:
        """
        Test snake_case to Title Case conversion.

        Args:
            user_api_key: The user's API key
            max_retry_count: Maximum number of retries
        """
        return "ok"

    schema = naming_test.openai_schema
    params = schema["function"]["parameters"]["properties"]

    assert params["user_api_key"]["title"] == "User Api Key"
    assert params["max_retry_count"]["title"] == "Max Retry Count"


def test_schema_json_serializable():
    """Test that the generated schema is JSON serializable."""

    @function_schema
    def json_test(param1: str, param2: int) -> str:
        """
        Test JSON serialization.

        Args:
            param1: First parameter
            param2: Second parameter
        """
        return "ok"

    schema = json_test.openai_schema

    # Should be able to serialize to JSON without errors
    json_str = json.dumps(schema, indent=2)
    assert json_str is not None

    # Should be able to deserialize back
    parsed = json.loads(json_str)
    assert parsed["function"]["parameters"]["properties"]["param1"]["title"] == "Param1"


def test_real_world_example():
    """Test with a realistic tool example."""

    @function_schema
    def web_search(
        query: str,
        num_results: int = 10,
        search_engine: str = "google",
        safe_search: bool = True,
    ) -> list:
        """
        Search the web for information.

        This tool performs web searches using various search engines
        and returns the top results.

        Args:
            query: The search query to execute
            num_results: Number of search results to return (1-100)
            search_engine: Which search engine to use (google, bing, duckduckgo)
            safe_search: Enable safe search filtering

        Returns:
            list: List of search results with titles and URLs
        """
        return []

    schema = web_search.openai_schema
    params = schema["function"]["parameters"]["properties"]

    # Verify all parameters have proper titles and descriptions
    assert params["query"]["title"] == "Query"
    assert params["query"]["description"] == "The search query to execute"

    assert params["num_results"]["title"] == "Num Results"
    assert (
        params["num_results"]["description"]
        == "Number of search results to return (1-100)"
    )

    assert params["search_engine"]["title"] == "Search Engine"
    assert (
        params["search_engine"]["description"]
        == "Which search engine to use (google, bing, duckduckgo)"
    )

    assert params["safe_search"]["title"] == "Safe Search"
    assert params["safe_search"]["description"] == "Enable safe search filtering"

    # Verify required vs optional
    required = schema["function"]["parameters"]["required"]
    assert "query" in required
    assert "num_results" not in required
    assert "search_engine" not in required
    assert "safe_search" not in required


if __name__ == "__main__":
    # Run tests
    test_basic_docstring_parsing()
    test_google_style_with_types()
    test_multiline_descriptions()
    test_fallback_for_missing_docstring()
    test_snake_case_to_title_case()
    test_schema_json_serializable()
    test_real_world_example()

    print("✅ All tests passed!")
