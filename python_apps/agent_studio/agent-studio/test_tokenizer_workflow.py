#!/usr/bin/env python3
"""
Test script for Tokenizer Workflow Steps

This script tests the tokenizer workflow steps to ensure they work correctly
with the deterministic workflow framework.
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add current directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

async def test_tokenizer_steps():
    """Test tokenizer workflow steps"""
    print("🧪 Testing Tokenizer Workflow Steps")
    print("=" * 50)
    
    try:
        # Test 1: Import and create steps
        print("\n1. Testing step imports and creation...")
        
        from steps.tokenizer.file_reader_step import create_file_reader_step
        from steps.tokenizer.text_chunking_step import create_text_chunking_step
        from steps.tokenizer.embedding_generation_step import create_embedding_generation_step
        from steps.tokenizer.vector_storage_step import create_vector_storage_step
        
        print("✅ All step imports successful")
        
        # Test 2: Create a simple text file for testing
        test_file_path = "/tmp/test_document.txt"
        test_content = """
        This is a test document for the tokenizer workflow.
        It contains multiple paragraphs to test text chunking.
        
        The document processing pipeline should:
        1. Read this file successfully
        2. Chunk the text into smaller segments
        3. Generate embeddings for each chunk
        4. Store the vectors in a database
        
        This approach enables Retrieval-Augmented Generation (RAG)
        by providing relevant context to AI agents based on
        semantic similarity search in the vector space.
        """
        
        with open(test_file_path, 'w') as f:
            f.write(test_content)
        
        print(f"✅ Created test file: {test_file_path}")
        
        # Test 3: File Reader Step
        print("\n2. Testing File Reader Step...")
        
        file_reader_config = {
            "file_path": test_file_path,
            "supported_formats": [".txt"],
            "max_file_size": 1024 * 1024,  # 1MB
            "encoding": "utf-8"
        }
        
        file_reader = create_file_reader_step(file_reader_config)
        file_result = await file_reader.execute({})
        
        if file_result.status.value == "completed":
            print(f"✅ File reader successful: {len(file_result.data['content'])} characters read")
            print(f"   Metadata: {json.dumps(file_result.data['metadata'], indent=2)}")
        else:
            print(f"❌ File reader failed: {file_result.error}")
            return
        
        # Test 4: Text Chunking Step
        print("\n3. Testing Text Chunking Step...")
        
        chunking_config = {
            "chunk_strategy": "sliding_window",
            "chunk_size": 200,
            "overlap": 0.1,
            "min_chunk_size": 50,
            "max_chunk_size": 300
        }
        
        chunking_input = {
            "content": file_result.data['content']
        }
        
        text_chunker = create_text_chunking_step(chunking_config)
        chunk_result = await text_chunker.execute(chunking_input)
        
        if chunk_result.status.value == "completed":
            chunks_count = len(chunk_result.data['chunks'])
            print(f"✅ Text chunking successful: {chunks_count} chunks created")
            print(f"   Average chunk size: {chunk_result.data['metadata']['average_chunk_size']} characters")
            
            # Show first chunk as example
            if chunks_count > 0:
                first_chunk = chunk_result.data['chunks'][0]
                print(f"   First chunk preview: {first_chunk['content'][:100]}...")
        else:
            print(f"❌ Text chunking failed: {chunk_result.error}")
            return
        
        # Test 5: Embedding Generation Step (mock test - requires OpenAI API)
        print("\n4. Testing Embedding Generation Step (validation only)...")
        
        embedding_config = {
            "provider": "openai",
            "model": "text-embedding-ada-002",
            "batch_size": 10,
            "max_retries": 1,
            "timeout": 30
        }
        
        embedding_input = {
            "chunks": chunk_result.data['chunks'][:2]  # Test with just 2 chunks
        }
        
        embedding_generator = create_embedding_generation_step(embedding_config)
        
        # Validate configuration
        validation_result = embedding_generator.validate_config()
        if validation_result.is_valid:
            print("✅ Embedding generation config validation successful")
            if validation_result.warnings:
                print(f"   Warnings: {validation_result.warnings}")
        else:
            print(f"❌ Embedding generation config validation failed: {validation_result.errors}")
        
        # Test 6: Vector Storage Step (validation only - requires Qdrant)
        print("\n5. Testing Vector Storage Step (validation only)...")
        
        storage_config = {
            "vector_db": "qdrant",
            "collection_name": "test_collection",
            "host": "localhost",
            "port": 6333,
            "distance_metric": "cosine",
            "create_collection": True,
            "batch_size": 50
        }
        
        vector_storage = create_vector_storage_step(storage_config)
        
        # Validate configuration
        storage_validation = vector_storage.validate_config()
        if storage_validation.is_valid:
            print("✅ Vector storage config validation successful")
        else:
            print(f"❌ Vector storage config validation failed: {storage_validation.errors}")
        
        # Test 7: Test workflow registry
        print("\n6. Testing Tokenizer Steps Registry...")
        
        from services.tokenizer_steps_registry import tokenizer_steps_registry
        
        available_steps = tokenizer_steps_registry.list_available_steps()
        print(f"✅ Available tokenizer steps: {available_steps}")
        
        # Test getting step implementations
        for step_type in available_steps:
            impl = tokenizer_steps_registry.get_step_implementation(step_type)
            if impl:
                print(f"✅ Step implementation found for: {step_type}")
            else:
                print(f"❌ No implementation found for: {step_type}")
        
        print("\n" + "=" * 50)
        print("🎉 All tokenizer workflow tests completed successfully!")
        print("\nNext steps:")
        print("1. Set up OpenAI API key for embedding generation testing")
        print("2. Set up Qdrant database for vector storage testing")
        print("3. Create a workflow in the database using the API:")
        print("   POST /api/workflows/ with tokenizer_rag_workflow.json")
        print("4. Execute the workflow:")
        print("   POST /api/workflows/{workflow_id}/execute")
        
        # Cleanup
        if os.path.exists(test_file_path):
            os.remove(test_file_path)
            print(f"\n🧹 Cleaned up test file: {test_file_path}")
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_tokenizer_steps())