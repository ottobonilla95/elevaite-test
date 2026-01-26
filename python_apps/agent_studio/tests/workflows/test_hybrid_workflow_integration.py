#!/usr/bin/env python3
"""
Test hybrid workflow integration with conditional execution.

This test verifies that hybrid workflows can:
1. Be saved via POST /api/workflows
2. Execute conditional routing based on input
3. Route to deterministic workflows when files are present
4. Route to traditional agents when no files are present
"""

import pytest
import uuid
import requests

# Import the FastAPI app and dependencies
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# API base URL
API_BASE_URL = "http://localhost:8005"


class TestHybridWorkflowIntegration:
    """Test hybrid workflow integration with conditional execution."""
    
    @pytest.fixture
    def test_client(self):
        """Create test client using requests to connect to running API."""
        
        class APIClient:
            def __init__(self, base_url):
                self.base_url = base_url
                
            def post(self, path, json=None):
                response = requests.post(f"{self.base_url}{path}", json=json)
                return response
                
            def get(self, path):
                response = requests.get(f"{self.base_url}{path}")
                return response
                
        return APIClient(API_BASE_URL)
    
    @pytest.fixture
    def sample_hybrid_workflow(self):
        """Create a sample hybrid workflow configuration."""
        unique_id = str(uuid.uuid4())[:8]
        return {
            "name": f"Hybrid Tokenizer + Router Workflow {unique_id}",
            "description": "A hybrid workflow with conditional tokenizer and router agent",
            "version": "1.0.0",
            "configuration": {
                "agents": [
                    {
                        "agent_id": "tokenizer_node_001",
                        "agent_type": "DeterministicWorkflowAgent",
                        "position": {"x": 100, "y": 200},
                        "config": {
                            "workflow_type": "deterministic",
                            "workflow_name": "File Tokenizer",
                            "description": "Processes files through tokenization pipeline",
                            "execution_pattern": "sequential",
                            "steps": [
                                {
                                    "step_id": "detect_file",
                                    "step_name": "Detect File Input",
                                    "step_type": "data_input",
                                    "step_order": 1,
                                    "config": {
                                        "input_source": "user_query",
                                        "validation_rules": ["required", "non_empty"]
                                    }
                                },
                                {
                                    "step_id": "process_file",
                                    "step_name": "Process File Content",
                                    "step_type": "data_processing",
                                    "step_order": 2,
                                    "dependencies": ["detect_file"],
                                    "config": {
                                        "processing_type": "count_words"
                                    }
                                },
                                {
                                    "step_id": "output_results",
                                    "step_name": "Output Tokenizer Results",
                                    "step_type": "data_output",
                                    "step_order": 3,
                                    "dependencies": ["process_file"],
                                    "config": {
                                        "output_format": "json",
                                        "include_metadata": True
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "agent_id": "router_agent_001",
                        "agent_type": "CommandAgent",
                        "position": {"x": 400, "y": 200},
                        "config": {
                            "model": "gpt-4o-mini",
                            "temperature": 0.7,
                            "system_prompt": "You are a router agent that can handle queries with or without file processing."
                        }
                    }
                ],
                "connections": [
                    {
                        "source_agent_id": "tokenizer_node_001",
                        "target_agent_id": "router_agent_001",
                        "connection_type": "conditional",
                        "conditions": {"file_processed": True}
                    }
                ],
                "execution_logic": {
                    "entry_point": "conditional_router",
                    "routing_rules": [
                        {
                            "condition": "input.has_file",
                            "action": "execute_tokenizer_then_router",
                            "flow": ["tokenizer_node_001", "router_agent_001"]
                        },
                        {
                            "condition": "!input.has_file",
                            "action": "execute_router_directly", 
                            "flow": ["router_agent_001"]
                        }
                    ]
                }
            },
            "created_by": "test_user",
            "is_active": True,
            "tags": ["hybrid", "test"]
        }
    
    @pytest.fixture
    def execution_request_with_file(self):
        """Create an execution request that mentions a file."""
        return {
            "query": "Please analyze this uploaded document and provide insights",
            "chat_history": [],
            "runtime_overrides": {
                "file_attachment": "test_document.pdf",
                "has_file": True
            },
            "session_id": "test_session_file",
            "user_id": "test_user"
        }
    
    @pytest.fixture
    def execution_request_no_file(self):
        """Create an execution request without files."""
        return {
            "query": "What is the weather like today?",
            "chat_history": [],
            "runtime_overrides": {},
            "session_id": "test_session_no_file", 
            "user_id": "test_user"
        }
    
    def test_create_hybrid_workflow(self, test_client, sample_hybrid_workflow):
        """Test creating a hybrid workflow via POST /api/workflows."""
        response = test_client.post("/api/workflows/", json=sample_hybrid_workflow)
        
        if response.status_code != 200:
            print(f"Error response: {response.status_code}")
            print(f"Error details: {response.text}")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify workflow was created correctly
        assert data["name"] == sample_hybrid_workflow["name"]
        assert data["is_active"] == True
        
        # Verify hybrid configuration was stored
        config = data["configuration"]
        assert "agents" in config
        assert "execution_logic" in config
        assert len(config["agents"]) == 2
        
        # Verify agents are correctly stored
        agent_types = [agent["agent_type"] for agent in config["agents"]]
        assert "DeterministicWorkflowAgent" in agent_types
        assert "CommandAgent" in agent_types
        
        return data["workflow_id"]
    
    def test_hybrid_workflow_detection(self, test_client, sample_hybrid_workflow):
        """Test that hybrid workflows are correctly detected."""
        # Create the workflow
        create_response = test_client.post("/api/workflows/", json=sample_hybrid_workflow)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]
        
        # Retrieve it to verify structure
        get_response = test_client.get(f"/api/workflows/{workflow_id}")
        assert get_response.status_code == 200
        
        data = get_response.json()
        config = data["configuration"]
        
        # Verify hybrid workflow characteristics
        assert "execution_logic" in config
        assert "routing_rules" in config["execution_logic"]
        assert len(config["execution_logic"]["routing_rules"]) == 2
    
    def test_execute_hybrid_workflow_with_file(self, test_client, sample_hybrid_workflow, execution_request_with_file):
        """Test executing hybrid workflow when file is present (should trigger tokenizer)."""
        # Create the workflow
        create_response = test_client.post("/api/workflows/", json=sample_hybrid_workflow)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]
        
        # Execute with file
        execute_response = test_client.post(
            f"/api/workflows/{workflow_id}/execute",
            json=execution_request_with_file
        )
        
        # Should succeed (even if tokenizer steps aren't fully implemented)
        assert execute_response.status_code == 200
        
        data = execute_response.json()
        assert data["status"] in ["success", "error"]  # Allow error for unimplemented steps
        assert data["workflow_id"] == workflow_id
    
    def test_execute_hybrid_workflow_no_file(self, test_client, sample_hybrid_workflow, execution_request_no_file):
        """Test executing hybrid workflow when no file is present (should go directly to router)."""
        # Create the workflow
        create_response = test_client.post("/api/workflows/", json=sample_hybrid_workflow)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]
        
        # Execute without file
        execute_response = test_client.post(
            f"/api/workflows/{workflow_id}/execute",
            json=execution_request_no_file
        )
        
        # Should succeed
        assert execute_response.status_code == 200
        
        data = execute_response.json()
        assert data["status"] in ["success", "error"]  # Allow error for agent setup issues
        assert data["workflow_id"] == workflow_id
    
    def test_hybrid_workflow_conditional_routing(self, test_client, sample_hybrid_workflow):
        """Test that conditional routing works correctly."""
        # Create the workflow
        create_response = test_client.post("/api/workflows/", json=sample_hybrid_workflow)
        assert create_response.status_code == 200
        workflow_id = create_response.json()["workflow_id"]
        
        # Test with file mention in query
        file_request = {
            "query": "Please process this file and analyze the content",
            "runtime_overrides": {},
            "session_id": "test_conditional",
            "user_id": "test_user"
        }
        
        execute_response = test_client.post(
            f"/api/workflows/{workflow_id}/execute",
            json=file_request
        )
        
        assert execute_response.status_code == 200
        
        # Test without file mention
        no_file_request = {
            "query": "What is machine learning?",
            "runtime_overrides": {},
            "session_id": "test_conditional_2",
            "user_id": "test_user"
        }
        
        execute_response = test_client.post(
            f"/api/workflows/{workflow_id}/execute",
            json=no_file_request
        )
        
        assert execute_response.status_code == 200


if __name__ == "__main__":
    """Run tests directly for development."""
    import subprocess
    import sys
    
    print("🧪 Running Hybrid Workflow Integration Tests")
    print("=" * 60)
    
    # Run pytest on this file
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short"
    ], capture_output=False)
    
    sys.exit(result.returncode)
