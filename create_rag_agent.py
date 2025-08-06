#!/usr/bin/env python3
"""
Create a RAG-enabled agent in the database and test it via the API
"""

import asyncio
import aiohttp
import json
import tempfile
import os
from pathlib import Path

class RAGAgentTester:
    def __init__(self, base_url="http://localhost:8005"):
        self.base_url = base_url
        self.session = None
        self.agent_id = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def create_rag_agent(self):
        """Create a RAG-enabled agent with document search tools"""
        print("🤖 Creating RAG-enabled agent...")
        
        agent_config = {
            "name": "RAG Document Assistant",
            "description": "An intelligent agent that can search and analyze documents using vector similarity",
            "agent_type": "CommandAgent",
            "system_prompt": """You are a RAG-enabled document assistant. You have access to a vector database containing processed documents. When users ask questions, you should:

1. Use the document_search tool to find relevant context from the processed documents
2. Analyze the retrieved context carefully
3. Provide comprehensive, accurate answers based on the retrieved information
4. If the information isn't in the documents, clearly state that
5. Always cite which parts of the documents you're referencing

You excel at understanding document content and providing detailed, contextual responses.""",
            "model": "gpt-4",
            "temperature": 0.1,
            "max_tokens": 2000,
            "tools": [
                {
                    "name": "document_search",
                    "description": "Search the processed document collection using vector similarity",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "The search query to find relevant document chunks"
                            },
                            "collection_name": {
                                "type": "string",
                                "description": "Name of the Qdrant collection containing documents",
                                "default": "rag_documents"
                            },
                            "top_k": {
                                "type": "integer",
                                "description": "Number of most relevant chunks to retrieve",
                                "default": 5
                            },
                            "score_threshold": {
                                "type": "number",
                                "description": "Minimum similarity score for results",
                                "default": 0.7
                            }
                        },
                        "required": ["query"]
                    }
                },
                {
                    "name": "document_metadata_search",
                    "description": "Search documents by metadata filters (filename, upload date, etc.)",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "filename": {
                                "type": "string",
                                "description": "Filter by specific filename"
                            },
                            "collection_name": {
                                "type": "string",
                                "description": "Name of the Qdrant collection",
                                "default": "rag_documents"
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of documents to return",
                                "default": 10
                            }
                        }
                    }
                }
            ]
        }
        
        async with self.session.post(
            f"{self.base_url}/api/agents/",
            json=agent_config,
            headers={"Content-Type": "application/json"}
        ) as response:
            if response.status in [200, 201]:
                result = await response.json()
                self.agent_id = result["agent_id"]
                print(f"   ✅ Created RAG agent: {self.agent_id}")
                return result
            else:
                error_text = await response.text()
                print(f"   ❌ Failed to create agent: {response.status} - {error_text}")
                raise Exception(f"Failed to create agent: {response.status} - {error_text}")
    
    async def test_rag_agent_execution(self):
        """Test the RAG agent with various queries"""
        print("\n🔍 Testing RAG agent execution...")
        
        test_queries = [
            "What documents are available in the system?",
            "Search for information about artificial intelligence",
            "Find documents related to machine learning",
            "What is the content of any research papers?",
            "Show me documents that contain the word 'technology'"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"\n   Query {i}: {query}")
            
            execution_request = {
                "query": query,
                "user_id": "rag_test_user",
                "session_id": "rag_test_session"
            }
            
            try:
                async with self.session.post(
                    f"{self.base_url}/api/agents/{self.agent_id}/execute",
                    json=execution_request,
                    headers={"Content-Type": "application/json"}
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        print(f"   ✅ Response: {result.get('response', 'No response')[:200]}...")
                        
                        # Check if tools were called
                        tools_called = result.get('tools_called', [])
                        if tools_called:
                            print(f"   🔧 Tools used: {', '.join(tools_called)}")
                        else:
                            print("   ℹ️  No tools were called")
                    else:
                        error_text = await response.text()
                        print(f"   ❌ Execution failed: {response.status} - {error_text}")
                        
            except Exception as e:
                print(f"   ❌ Error executing query: {e}")
    
    async def test_agent_schema(self):
        """Test the agent's OpenAI schema endpoint"""
        print("\n📋 Testing agent schema...")
        
        try:
            async with self.session.get(
                f"{self.base_url}/api/agents/{self.agent_id}/schema"
            ) as response:
                if response.status == 200:
                    schema = await response.json()
                    print(f"   ✅ Agent schema retrieved")
                    print(f"   📝 System prompt: {schema.get('system_prompt', '')[:100]}...")
                    
                    tools = schema.get('tools', [])
                    print(f"   🔧 Available tools: {len(tools)}")
                    for tool in tools:
                        tool_name = tool.get('function', {}).get('name', 'Unknown')
                        print(f"      - {tool_name}")
                else:
                    error_text = await response.text()
                    print(f"   ❌ Failed to get schema: {response.status} - {error_text}")
                    
        except Exception as e:
            print(f"   ❌ Error getting schema: {e}")
    
    async def cleanup_agent(self):
        """Clean up the test agent"""
        if self.agent_id:
            print(f"\n🧹 Cleaning up agent {self.agent_id}...")
            try:
                async with self.session.delete(
                    f"{self.base_url}/api/agents/{self.agent_id}"
                ) as response:
                    if response.status == 200:
                        print("   ✅ Agent deleted successfully")
                    else:
                        print(f"   ⚠️  Failed to delete agent: {response.status}")
            except Exception as e:
                print(f"   ⚠️  Error deleting agent: {e}")

async def main():
    """Run the complete RAG agent test"""
    print("🚀 Starting RAG Agent Test")
    print("=" * 80)
    
    async with RAGAgentTester() as tester:
        try:
            # Create the RAG agent
            await tester.create_rag_agent()
            
            # Test agent schema
            await tester.test_agent_schema()
            
            # Test agent execution
            await tester.test_rag_agent_execution()
            
            print("\n🎉 RAG agent test completed!")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ Test failed: {e}")
        finally:
            # Clean up
            await tester.cleanup_agent()

if __name__ == "__main__":
    asyncio.run(main())
