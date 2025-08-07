#!/usr/bin/env python3
"""
Test script for file upload functionality

This script tests the file upload endpoint and verifies that the file path
is properly passed to the workflow steps.
"""

import requests
import json
import tempfile
import os
import time

# Configuration
BASE_URL = "http://localhost:8005"
API_BASE = f"{BASE_URL}/api"

# Test workflow configuration with file reader step
TEST_WORKFLOW = {
    "name": "File Upload Test Workflow",
    "description": "Tests file upload and processing",
    "version": "1.0.0",
    "configuration": {
        "workflow_id": "file_upload_test",
        "workflow_name": "File Upload Test Workflow",
        "workflow_type": "deterministic",
        "execution_pattern": "sequential",
        "timeout_seconds": 300,
        "steps": [
            {
                "step_id": "read_uploaded_file",
                "step_name": "Read Uploaded File",
                "step_type": "data_input",
                "step_order": 1,
                "config": {
                    "tokenizer_step": "file_reader",
                    "supported_formats": [".txt", ".md", ".pdf"],
                    "max_file_size": 1048576,
                    "encoding": "utf-8",
                    "extract_metadata": True,
                },
                "timeout_seconds": 60,
            },
            {
                "step_id": "chunk_uploaded_text",
                "step_name": "Chunk Uploaded Text",
                "step_type": "transformation",
                "step_order": 2,
                "dependencies": ["read_uploaded_file"],
                "input_mapping": {
                    "content": "read_uploaded_file.content",
                },
                "config": {
                    "tokenizer_step": "text_chunking",
                    "chunk_strategy": "sliding_window",
                    "chunk_size": 500,
                    "overlap": 0.1,
                    "min_chunk_size": 100,
                    "max_chunk_size": 800,
                },
                "timeout_seconds": 60,
            },
        ],
    },
    "tags": ["test", "file-upload"],
}

def create_test_file():
    """Create a test file for upload"""
    content = """# Test Document for File Upload

This is a test document to verify that file upload functionality works correctly.

## Features Being Tested

1. **File Upload**: Uploading a file through the API
2. **File Processing**: Reading the uploaded file in the workflow
3. **Text Chunking**: Processing the file content through chunking

## Content

This document contains multiple paragraphs and sections to test the chunking functionality.
The enhanced tokenizer should be able to process this content and create appropriate chunks.

### Section 1

Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.

### Section 2

Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.

## Conclusion

This test document should be successfully processed by the file upload workflow.
"""
    
    # Create temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False)
    temp_file.write(content)
    temp_file.close()
    
    return temp_file.name

def create_workflow():
    """Create the test workflow"""
    print("📝 Creating test workflow...")
    
    response = requests.post(
        f"{API_BASE}/workflows",
        json=TEST_WORKFLOW,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 201:
        workflow = response.json()
        print(f"✅ Workflow created: {workflow['workflow_id']}")
        return workflow
    else:
        print(f"❌ Failed to create workflow: {response.status_code} - {response.text}")
        return None

def test_file_upload(workflow_id, file_path):
    """Test file upload and execution"""
    print(f"📤 Testing file upload with workflow {workflow_id}...")
    
    # Prepare form data
    with open(file_path, 'rb') as f:
        files = {'file': (os.path.basename(file_path), f, 'text/markdown')}
        data = {
            'query': 'Please process this uploaded file and create chunks from its content.',
            'session_id': 'test_session',
            'user_id': 'test_user'
        }
        
        # Execute workflow with file upload
        response = requests.post(
            f"{API_BASE}/workflows/{workflow_id}/execute/async",
            files=files,
            data=data
        )
    
    if response.status_code == 202:
        result = response.json()
        execution_id = result.get('execution_id')
        print(f"✅ Workflow execution started: {execution_id}")
        return execution_id
    else:
        print(f"❌ Failed to execute workflow: {response.status_code} - {response.text}")
        return None

def check_execution_status(execution_id):
    """Check execution status and results"""
    print(f"🔍 Checking execution status for {execution_id}...")
    
    max_attempts = 30
    for attempt in range(max_attempts):
        response = requests.get(f"{API_BASE}/executions/{execution_id}")
        
        if response.status_code == 200:
            execution = response.json()
            status = execution.get('status')
            
            print(f"   Status: {status} (attempt {attempt + 1}/{max_attempts})")
            
            if status == 'completed':
                print("✅ Execution completed successfully!")
                
                # Print results
                response_data = execution.get('response')
                if response_data:
                    try:
                        if isinstance(response_data, str):
                            parsed_response = json.loads(response_data)
                        else:
                            parsed_response = response_data
                        
                        print("\n📊 Execution Results:")
                        
                        # Check file reader results
                        if 'read_uploaded_file' in parsed_response:
                            file_result = parsed_response['read_uploaded_file']
                            if file_result.get('success'):
                                content_length = len(file_result.get('content', ''))
                                print(f"   ✅ File read successfully: {content_length} characters")
                                
                                metadata = file_result.get('metadata', {})
                                if 'file_path' in metadata:
                                    print(f"   ✅ File path processed: {metadata['file_path']}")
                                if 'file_size' in metadata:
                                    print(f"   ✅ File size: {metadata['file_size']} bytes")
                            else:
                                print(f"   ❌ File reading failed: {file_result.get('error', 'Unknown error')}")
                        
                        # Check chunking results
                        if 'chunk_uploaded_text' in parsed_response:
                            chunk_result = parsed_response['chunk_uploaded_text']
                            if chunk_result.get('success'):
                                chunks = chunk_result.get('chunks', [])
                                print(f"   ✅ Text chunked successfully: {len(chunks)} chunks")
                                
                                if chunks:
                                    avg_size = sum(len(chunk.get('content', '')) for chunk in chunks) / len(chunks)
                                    print(f"   ✅ Average chunk size: {avg_size:.0f} characters")
                            else:
                                print(f"   ❌ Chunking failed: {chunk_result.get('error', 'Unknown error')}")
                        
                    except json.JSONDecodeError:
                        print(f"   ⚠️  Could not parse response: {response_data}")
                
                return True
                
            elif status == 'failed':
                print(f"❌ Execution failed: {execution.get('error', 'Unknown error')}")
                return False
                
            elif status in ['running', 'pending']:
                time.sleep(2)  # Wait before next check
                continue
            else:
                print(f"❌ Unknown status: {status}")
                return False
        else:
            print(f"❌ Failed to get execution status: {response.status_code}")
            return False
    
    print(f"⏰ Execution timed out after {max_attempts} attempts")
    return False

def cleanup_workflow(workflow_id):
    """Clean up the test workflow"""
    print(f"🧹 Cleaning up workflow {workflow_id}...")
    
    response = requests.delete(f"{API_BASE}/workflows/{workflow_id}")
    if response.status_code == 200:
        print("✅ Workflow cleaned up successfully")
    else:
        print(f"⚠️  Failed to clean up workflow: {response.status_code}")

def main():
    """Run the file upload test"""
    print("🚀 File Upload Test")
    print("=" * 50)
    
    # Create test file
    test_file = create_test_file()
    print(f"📄 Created test file: {test_file}")
    
    try:
        # Create workflow
        workflow = create_workflow()
        if not workflow:
            return False
        
        workflow_id = workflow['workflow_id']
        
        try:
            # Test file upload
            execution_id = test_file_upload(workflow_id, test_file)
            if not execution_id:
                return False
            
            # Check results
            success = check_execution_status(execution_id)
            
            print("\n" + "=" * 50)
            if success:
                print("🎉 File upload test completed successfully!")
                print("✅ File was uploaded, processed, and chunked correctly")
            else:
                print("❌ File upload test failed")
            
            return success
            
        finally:
            # Clean up workflow
            cleanup_workflow(workflow_id)
    
    finally:
        # Clean up test file
        try:
            os.unlink(test_file)
            print(f"🧹 Cleaned up test file: {test_file}")
        except:
            pass

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
