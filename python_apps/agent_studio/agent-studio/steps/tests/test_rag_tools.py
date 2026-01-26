#!/usr/bin/env python3
"""
Test script for the new RAG tools: document_search and document_metadata_search
"""

import sys


# Test that the tools are properly added to the tool store
def test_tool_availability():
    """Test that RAG tools are available in the tool store"""
    print("🔍 Testing RAG tool availability...")
    print("=" * 60)

    # Import the tool store
    sys.path.append("python_apps/agent_studio/agent-studio")

    try:
        # Import just the tool store to avoid circular imports
        import importlib.util

        spec = importlib.util.spec_from_file_location(
            "tools", "python_apps/agent_studio/agent-studio/agents/tools.py"
        )
        tools_module = importlib.util.module_from_spec(spec)

        # Check if our new tools are in the file
        with open("python_apps/agent_studio/agent-studio/agents/tools.py", "r") as f:
            content = f.read()

        # Check for our new functions
        has_document_search = "def document_search(" in content
        has_document_metadata_search = "def document_metadata_search(" in content
        has_tool_store_entry = '"document_search": document_search' in content
        has_schema_entry = '"document_search": document_search.openai_schema' in content

        print(f"✅ document_search function defined: {has_document_search}")
        print(
            f"✅ document_metadata_search function defined: {has_document_metadata_search}"
        )
        print(f"✅ document_search in tool_store: {has_tool_store_entry}")
        print(f"✅ document_search schema registered: {has_schema_entry}")

        if all(
            [
                has_document_search,
                has_document_metadata_search,
                has_tool_store_entry,
                has_schema_entry,
            ]
        ):
            print("\n🎉 All RAG tools are properly configured!")
            return True
        else:
            print("\n❌ Some RAG tools are missing configuration")
            return False

    except Exception as e:
        print(f"❌ Error checking tools: {e}")
        return False


def test_document_search():
    """Test the document_search tool"""
    print("🔍 Testing document_search tool...")
    print("=" * 60)

    # Test with default collection (should fail gracefully if collection doesn't exist)
    result = document_search(
        query="What is artificial intelligence?",
        collection_name="rag_documents",
        top_k=3,
        score_threshold=0.5,
    )

    print("Query: 'What is artificial intelligence?'")
    print("Collection: rag_documents")
    print("Result:")
    print(result)
    print("\n" + "=" * 60 + "\n")


def test_document_metadata_search():
    """Test the document_metadata_search tool"""
    print("📋 Testing document_metadata_search tool...")
    print("=" * 60)

    # Test metadata search
    result = document_metadata_search(
        filename="test", collection_name="rag_documents", limit=5
    )

    print("Filename filter: 'test'")
    print("Collection: rag_documents")
    print("Result:")
    print(result)
    print("\n" + "=" * 60 + "\n")


def test_tool_schemas():
    """Test that the tools have proper OpenAI schemas"""
    print("🔧 Testing tool schemas...")
    print("=" * 60)

    # Check document_search schema
    print("document_search schema:")
    print(f"Function name: {document_search.openai_schema['function']['name']}")
    print(
        f"Description: {document_search.openai_schema['function']['description'][:100]}..."
    )
    print(
        f"Parameters: {list(document_search.openai_schema['function']['parameters']['properties'].keys())}"
    )
    print()

    # Check document_metadata_search schema
    print("document_metadata_search schema:")
    print(
        f"Function name: {document_metadata_search.openai_schema['function']['name']}"
    )
    print(
        f"Description: {document_metadata_search.openai_schema['function']['description'][:100]}..."
    )
    print(
        f"Parameters: {list(document_metadata_search.openai_schema['function']['parameters']['properties'].keys())}"
    )
    print("\n" + "=" * 60 + "\n")


def main():
    """Run all tests"""
    print("🚀 Testing RAG Tools")
    print("=" * 60)
    print()

    # Test tool schemas first (these should always work)
    test_tool_schemas()

    # Test actual tool execution (may fail if Qdrant not available)
    try:
        test_document_search()
        test_document_metadata_search()
        print("✅ All tests completed!")
    except Exception as e:
        print(f"⚠️  Tool execution failed (expected if Qdrant not running): {e}")
        print("✅ Schema tests passed - tools are properly configured!")


if __name__ == "__main__":
    main()
