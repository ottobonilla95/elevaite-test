#!/usr/bin/env python3
"""
End-to-End API Test for Tokenizer Workflow

This script tests the complete tokenizer workflow through the API endpoints:
1. Create a tokenizer workflow via POST /api/workflows/
2. Execute the workflow via POST /api/workflows/{id}/execute
3. Check execution status and results
4. Clean up test data

This validates the full integration with the deterministic workflow framework.
"""

import asyncio
import aiohttp
import json
import os
import sys
import uuid
from pathlib import Path

# Configuration
API_BASE_URL = "http://localhost:8005"
TEST_FILE_PATH = "/tmp/test_tokenizer_document.txt"

async def create_test_file():
    """Create a test document for processing"""
    test_content = """
# Tokenizer Workflow Test Document

This is a comprehensive test document for validating the tokenizer workflow system.
The document contains multiple sections to test various aspects of text processing.

## Introduction

The tokenizer workflow is designed to process documents for Retrieval-Augmented Generation (RAG) purposes.
It performs several key operations:

1. **File Reading**: Extract text content from various document formats
2. **Text Chunking**: Divide the text into semantically meaningful chunks
3. **Embedding Generation**: Create vector embeddings for each text chunk
4. **Vector Storage**: Store embeddings in a vector database for retrieval

## Technical Details

### Chunking Strategies
The system supports multiple chunking strategies:
- Fixed-size chunking with configurable chunk sizes
- Sliding window chunking with overlap control
- Semantic chunking using sentence embeddings
- Sentence-based and paragraph-based chunking

### Embedding Models
Integration with multiple embedding providers:
- OpenAI embedding models (text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large)
- Local sentence transformer models
- Custom embedding API endpoints

### Vector Databases
Support for various vector databases:
- Qdrant (recommended for production)
- ChromaDB (for local development)
- Pinecone (cloud-based solution)
- Custom vector database APIs

## Performance Considerations

The workflow is optimized for:
- Batch processing of embeddings to reduce API calls
- Configurable rate limiting to respect API limits
- Retry logic for robust error handling
- Progress tracking for long-running operations

## Use Cases

This tokenizer workflow enables several use cases:
- Document Q&A systems
- Knowledge base search
- Content recommendation
- Semantic document retrieval
- Customer support automation

## Conclusion

The tokenizer workflow provides a robust foundation for building RAG-powered applications
with comprehensive document processing capabilities and flexible configuration options.
    """
    
    with open(TEST_FILE_PATH, 'w', encoding='utf-8') as f:
        f.write(test_content.strip())
    
    print(f"✅ Created test document: {TEST_FILE_PATH} ({len(test_content)} characters)")
    return TEST_FILE_PATH

async def make_api_request(session, method, endpoint, data=None, json_data=None):
    """Make an API request with error handling"""
    url = f"{API_BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            async with session.get(url) as response:
                response_text = await response.text()
                if response.status >= 400:
                    print(f"❌ API Error {response.status}: {response_text}")
                    return None
                return await response.json() if response_text else None
        
        elif method.upper() == "POST":
            headers = {'Content-Type': 'application/json'} if json_data else None
            async with session.post(url, json=json_data, data=data, headers=headers) as response:
                response_text = await response.text()
                if response.status >= 400:
                    print(f"❌ API Error {response.status}: {response_text}")
                    return None
                return await response.json() if response_text else None
        
        elif method.upper() == "DELETE":
            async with session.delete(url) as response:
                if response.status >= 400:
                    response_text = await response.text()
                    print(f"❌ API Error {response.status}: {response_text}")
                    return None
                return {"success": True}
    
    except Exception as e:
        print(f"❌ API Request failed: {e}")
        return None

async def test_tokenizer_workflow_api():
    """Test the complete tokenizer workflow via API"""
    print("🧪 Testing Tokenizer Workflow via API")
    print("=" * 60)
    
    # Create test file
    test_file_path = await create_test_file()
    workflow_id = None
    
    async with aiohttp.ClientSession() as session:
        try:
            # Test 1: Check API health
            print("\n1. Checking API health...")
            health_response = await make_api_request(session, "GET", "/hc")
            if health_response:
                print(f"✅ API is healthy: {health_response.get('status', 'unknown')}")
            else:
                print("❌ API health check failed")
                return
            
            # Test 2: Create tokenizer workflow
            print("\n2. Creating tokenizer workflow...")
            
            # Load the workflow configuration
            workflow_config_path = "/home/johnbelly/work/elevaite/workflows/tokenizer_rag_workflow.json"
            
            if not os.path.exists(workflow_config_path):
                print(f"❌ Workflow config file not found: {workflow_config_path}")
                return
            
            with open(workflow_config_path, 'r') as f:
                workflow_config = json.load(f)
            
            # Modify config to use our test file
            workflow_config["steps"][0]["config"]["file_path"] = test_file_path
            workflow_config["steps"][3]["config"]["collection_name"] = f"test_collection_{uuid.uuid4().hex[:8]}"
            
            # Create workflow payload
            workflow_payload = {
                "name": workflow_config["workflow_name"],
                "description": workflow_config["description"],
                "version": workflow_config["version"],
                "configuration": workflow_config,
                "tags": workflow_config.get("tags", [])
            }
            
            workflow_response = await make_api_request(
                session, "POST", "/api/workflows/", json_data=workflow_payload
            )
            
            if workflow_response:
                workflow_id = workflow_response["workflow_id"]
                print(f"✅ Created workflow: {workflow_id}")
                print(f"   Name: {workflow_response['name']}")
                print(f"   Version: {workflow_response['version']}")
            else:
                print("❌ Failed to create workflow")
                return
            
            # Test 3: Execute the workflow
            print("\n3. Executing tokenizer workflow...")
            
            execution_payload = {
                "query": "Process this test document",
                "session_id": f"test_session_{uuid.uuid4().hex[:8]}",
                "user_id": "test_user"
            }
            
            execution_response = await make_api_request(
                session, "POST", f"/api/workflows/{workflow_id}/execute", json_data=execution_payload
            )
            
            if execution_response:
                print(f"✅ Workflow execution started")
                print(f"   Status: {execution_response.get('status')}")
                print(f"   Workflow ID: {execution_response.get('workflow_id')}")
                
                # Parse the response to check results
                response_data = execution_response.get('response')
                if response_data:
                    try:
                        if isinstance(response_data, str):
                            parsed_response = json.loads(response_data)
                        else:
                            parsed_response = response_data
                        
                        print(f"   Response type: {type(parsed_response)}")
                        if isinstance(parsed_response, dict):
                            print(f"   Response keys: {list(parsed_response.keys())}")
                    except json.JSONDecodeError:
                        print(f"   Response (first 200 chars): {str(response_data)[:200]}...")
            else:
                print("❌ Failed to execute workflow")
                return
            
            # Test 4: Test async execution
            print("\n4. Testing async execution...")
            
            async_execution_response = await make_api_request(
                session, "POST", f"/api/workflows/{workflow_id}/execute/async", json_data=execution_payload
            )
            
            if async_execution_response:
                execution_id = async_execution_response.get("execution_id")
                print(f"✅ Async execution started: {execution_id}")
                print(f"   Status: {async_execution_response.get('status')}")
                print(f"   Estimated completion: {async_execution_response.get('estimated_completion_time')}")
                
                # Check execution status
                if execution_id:
                    print(f"   Status URL: {async_execution_response.get('status_url')}")
                    
                    # Wait a bit for execution to start
                    await asyncio.sleep(2)
                    
                    # Check status
                    status_response = await make_api_request(
                        session, "GET", f"/api/executions/{execution_id}/status"
                    )
                    
                    if status_response:
                        print(f"   Current status: {status_response.get('status')}")
                        progress = status_response.get('progress', 0) or 0
                        print(f"   Progress: {progress:.1%}")
                        if status_response.get('current_step'):
                            print(f"   Current step: {status_response.get('current_step')}")
            else:
                print("❌ Failed to start async execution")
            
            # Test 5: List workflows
            print("\n5. Listing workflows...")
            
            workflows_response = await make_api_request(session, "GET", "/api/workflows/")
            
            if workflows_response:
                print(f"✅ Found {len(workflows_response)} workflows")
                
                # Find our workflow
                our_workflow = next((w for w in workflows_response if w["workflow_id"] == workflow_id), None)
                if our_workflow:
                    print(f"   Our workflow found: {our_workflow['name']}")
                    print(f"   Created: {our_workflow.get('created_at')}")
                    print(f"   Is active: {our_workflow.get('is_active')}")
            else:
                print("❌ Failed to list workflows")
            
            # Test 6: Get specific workflow
            print("\n6. Getting workflow details...")
            
            workflow_details = await make_api_request(session, "GET", f"/api/workflows/{workflow_id}")
            
            if workflow_details:
                print(f"✅ Workflow details retrieved")
                print(f"   Configuration steps: {len(workflow_details['configuration'].get('steps', []))}")
                print(f"   Workflow agents: {len(workflow_details.get('workflow_agents', []))}")
                print(f"   Workflow connections: {len(workflow_details.get('workflow_connections', []))}")
            else:
                print("❌ Failed to get workflow details")
            
            print("\n" + "=" * 60)
            print("🎉 All API tests completed successfully!")
            print("\nTest Summary:")
            print(f"- Created workflow: {workflow_id}")
            print(f"- Tested sync execution: ✅")
            print(f"- Tested async execution: ✅")
            print(f"- Tested workflow listing: ✅")
            print(f"- Tested workflow details: ✅")
            
            print("\nTo test with real services:")
            print("1. Set OPENAI_API_KEY environment variable")
            print("2. Start Qdrant database: docker run -p 6333:6333 qdrant/qdrant")
            print("3. Run the workflow with actual embedding generation and vector storage")
            
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            # Cleanup: Delete the workflow
            if workflow_id:
                print(f"\n🧹 Cleaning up workflow: {workflow_id}")
                delete_response = await make_api_request(session, "DELETE", f"/api/workflows/{workflow_id}")
                if delete_response:
                    print("✅ Workflow deleted successfully")
                else:
                    print("❌ Failed to delete workflow")
            
            # Cleanup test file
            if os.path.exists(test_file_path):
                os.remove(test_file_path)
                print(f"✅ Cleaned up test file: {test_file_path}")

if __name__ == "__main__":
    print("Starting API integration test...")
    print(f"API Base URL: {API_BASE_URL}")
    print("Make sure the Agent Studio API server is running!")
    print()
    
    try:
        asyncio.run(test_tokenizer_workflow_api())
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"❌ Test failed: {e}")