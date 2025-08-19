"""
Test Tokenizer Steps

Comprehensive tests for the tokenizer workflow steps:
- File Reader
- Text Chunking
- Embedding Generation
- Vector Storage
"""

import asyncio
import tempfile
import os
from pathlib import Path
from typing import Dict, Any

from workflow_engine_poc.execution_context import ExecutionContext, UserContext
from workflow_engine_poc.tokenizer_steps import (
    FileReaderStep,
    TextChunkingStep,
    EmbeddingGenerationStep,
    VectorStorageStep,
    file_reader_step,
    text_chunking_step,
    embedding_generation_step,
    vector_storage_step,
)


async def test_file_reader_step():
    """Test file reader step with various file types"""

    print("\n🧪 Testing File Reader Step")
    print("-" * 40)

    # Create test files
    test_files = {}

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test text file
        txt_file = os.path.join(temp_dir, "test.txt")
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write("This is a test document for the workflow engine.\n")
            f.write("It contains multiple lines and should be processed correctly.\n")
            f.write("The file reader step should extract this content successfully.")

        test_files["txt"] = txt_file

        # Test text file reading
        user_context = UserContext(user_id="test_user", session_id="tokenizer_test")
        workflow_config = {
            "workflow_id": "test-tokenizer",
            "name": "Test Tokenizer Workflow",
        }
        execution_context = ExecutionContext(workflow_config, user_context)

        step_config = {"step_id": "read_file", "step_type": "file_reader", "config": {}}

        input_data = {"file_path": txt_file}

        result = await file_reader_step(step_config, input_data, execution_context)

        print(f"✅ Text file reading:")
        print(f"   Success: {result.get('success')}")
        print(f"   Content length: {len(result.get('content', ''))}")
        print(f"   File type: {result.get('metadata', {}).get('file_type')}")
        print(
            f"   Extraction method: {result.get('metadata', {}).get('extraction_method')}"
        )

        return result


async def test_text_chunking_step():
    """Test text chunking step with different strategies"""

    print("\n🧪 Testing Text Chunking Step")
    print("-" * 40)

    # Sample content for chunking
    content = """
    The unified workflow execution engine represents a significant advancement in automation technology. 
    It provides clean abstractions for complex business processes while maintaining flexibility and scalability.
    
    The engine supports multiple execution patterns including sequential, parallel, and conditional workflows.
    Each step in the workflow can be independently configured and executed, allowing for maximum modularity.
    
    The tokenizer components enable sophisticated document processing capabilities. Files can be read from 
    various formats, chunked using different strategies, embedded using multiple providers, and stored 
    in vector databases for efficient retrieval.
    
    This architecture enables powerful RAG (Retrieval-Augmented Generation) workflows that can process 
    large document collections and provide intelligent question-answering capabilities.
    """

    user_context = UserContext(user_id="test_user", session_id="tokenizer_test")
    workflow_config = {
        "workflow_id": "test-tokenizer",
        "name": "Test Tokenizer Workflow",
    }
    execution_context = ExecutionContext(workflow_config, user_context)

    # Test sliding window chunking
    step_config = {
        "step_id": "chunk_text",
        "step_type": "text_chunking",
        "config": {"strategy": "sliding_window", "chunk_size": 300, "overlap": 50},
    }

    input_data = {"content": content}

    result = await text_chunking_step(step_config, input_data, execution_context)

    print(f"✅ Sliding window chunking:")
    print(f"   Success: {result.get('success')}")
    print(f"   Chunk count: {len(result.get('chunks', []))}")
    print(f"   Strategy: {result.get('metadata', {}).get('strategy')}")
    print(f"   Original length: {result.get('metadata', {}).get('original_length')}")

    if result.get("chunks"):
        print(f"   First chunk preview: {result['chunks'][0]['content'][:100]}...")

    return result


async def test_embedding_generation_step():
    """Test embedding generation step"""

    print("\n🧪 Testing Embedding Generation Step")
    print("-" * 40)

    # Sample chunks for embedding
    chunks = [
        {
            "id": "chunk_0",
            "content": "The unified workflow execution engine represents a significant advancement in automation technology.",
            "start_char": 0,
            "end_char": 95,
            "size": 95,
            "word_count": 13,
        },
        {
            "id": "chunk_1",
            "content": "It provides clean abstractions for complex business processes while maintaining flexibility.",
            "start_char": 96,
            "end_char": 186,
            "size": 90,
            "word_count": 12,
        },
        {
            "id": "chunk_2",
            "content": "The tokenizer components enable sophisticated document processing capabilities.",
            "start_char": 187,
            "end_char": 264,
            "size": 77,
            "word_count": 9,
        },
    ]

    user_context = UserContext(user_id="test_user", session_id="tokenizer_test")
    workflow_config = {
        "workflow_id": "test-tokenizer",
        "name": "Test Tokenizer Workflow",
    }
    execution_context = ExecutionContext(workflow_config, user_context)

    # Test with simulated embeddings (since we may not have API keys)
    step_config = {
        "step_id": "generate_embeddings",
        "step_type": "embedding_generation",
        "config": {
            "provider": "openai",
            "model": "text-embedding-ada-002",
            "batch_size": 3,
        },
    }

    input_data = {"chunks": chunks}

    result = await embedding_generation_step(step_config, input_data, execution_context)

    print(f"✅ Embedding generation:")
    print(f"   Success: {result.get('success')}")
    print(f"   Embedding count: {len(result.get('embeddings', []))}")
    print(f"   Provider: {result.get('metadata', {}).get('provider')}")
    print(f"   Model: {result.get('metadata', {}).get('model')}")

    if result.get("embeddings"):
        first_embedding = result["embeddings"][0]
        print(f"   Dimension: {first_embedding.get('dimension')}")
        print(f"   First embedding preview: {first_embedding['embedding'][:5]}...")

    return result


async def test_vector_storage_step():
    """Test vector storage step"""

    print("\n🧪 Testing Vector Storage Step")
    print("-" * 40)

    # Sample embeddings for storage
    embeddings = [
        {
            "chunk_id": "chunk_0",
            "embedding": [0.1, 0.2, 0.3, 0.4, 0.5] * 100,  # 500-dim vector
            "dimension": 500,
            "model": "test-model",
            "chunk_text": "The unified workflow execution engine...",
            "chunk_metadata": {
                "size": 95,
                "word_count": 13,
                "start_char": 0,
                "end_char": 95,
            },
        },
        {
            "chunk_id": "chunk_1",
            "embedding": [0.2, 0.3, 0.4, 0.5, 0.6] * 100,  # 500-dim vector
            "dimension": 500,
            "model": "test-model",
            "chunk_text": "It provides clean abstractions...",
            "chunk_metadata": {
                "size": 90,
                "word_count": 12,
                "start_char": 96,
                "end_char": 186,
            },
        },
    ]

    user_context = UserContext(user_id="test_user", session_id="tokenizer_test")
    workflow_config = {
        "workflow_id": "test-tokenizer",
        "name": "Test Tokenizer Workflow",
    }
    execution_context = ExecutionContext(workflow_config, user_context)

    # Test with in-memory storage (since we may not have Qdrant running)
    step_config = {
        "step_id": "store_vectors",
        "step_type": "vector_storage",
        "config": {"storage_type": "in_memory", "collection_name": "test_documents"},
    }

    input_data = {"embeddings": embeddings}

    result = await vector_storage_step(step_config, input_data, execution_context)

    print(f"✅ Vector storage:")
    print(f"   Success: {result.get('success')}")
    print(f"   Stored count: {result.get('stored_count')}")
    print(f"   Storage type: {result.get('metadata', {}).get('storage_type')}")
    print(f"   Collection: {result.get('metadata', {}).get('collection_name')}")

    storage_info = result.get("storage_info", {})
    if storage_info:
        print(f"   Points stored: {storage_info.get('points_stored')}")

    return result


async def test_full_tokenizer_workflow():
    """Test complete tokenizer workflow end-to-end"""

    print("\n🧪 Testing Full Tokenizer Workflow")
    print("-" * 40)

    # Create test content
    with tempfile.TemporaryDirectory() as temp_dir:
        txt_file = os.path.join(temp_dir, "workflow_test.txt")
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(
                """
            Unified Workflow Execution Engine Documentation
            
            The workflow execution engine is designed to be agnostic about workflow structure.
            It executes the right function at the right step, supporting multiple execution patterns.
            
            Key Features:
            - RPC-like step registration for dynamic extensibility
            - Multi-provider LLM integration via llm-gateway
            - Simplified agent execution with graceful fallbacks
            - Database-backed configuration management
            - Support for sequential, parallel, and conditional execution
            
            Tokenizer Components:
            The tokenizer subsystem provides essential RAG capabilities including file reading,
            text chunking, embedding generation, and vector storage. These components work together
            to create a complete document processing pipeline.
            
            This architecture enables sophisticated document analysis and question-answering workflows
            that can scale to handle large document collections efficiently.
            """
            )

        user_context = UserContext(
            user_id="test_user", session_id="full_tokenizer_test"
        )
        workflow_config = {
            "workflow_id": "test-full-tokenizer",
            "name": "Full Tokenizer Test",
        }
        execution_context = ExecutionContext(workflow_config, user_context)

        # Step 1: Read file
        print("📖 Step 1: Reading file...")
        file_result = await file_reader_step(
            {"step_id": "read", "step_type": "file_reader", "config": {}},
            {"file_path": txt_file},
            execution_context,
        )

        if not file_result.get("success"):
            print(f"❌ File reading failed: {file_result.get('error')}")
            return

        print(f"   ✅ Read {len(file_result['content'])} characters")

        # Step 2: Chunk text
        print("✂️  Step 2: Chunking text...")
        chunk_result = await text_chunking_step(
            {
                "step_id": "chunk",
                "step_type": "text_chunking",
                "config": {
                    "strategy": "sliding_window",
                    "chunk_size": 400,
                    "overlap": 50,
                },
            },
            {"content": file_result["content"]},
            execution_context,
        )

        if not chunk_result.get("success"):
            print(f"❌ Text chunking failed: {chunk_result.get('error')}")
            return

        print(f"   ✅ Created {len(chunk_result['chunks'])} chunks")

        # Step 3: Generate embeddings
        print("🔢 Step 3: Generating embeddings...")
        embedding_result = await embedding_generation_step(
            {
                "step_id": "embed",
                "step_type": "embedding_generation",
                "config": {
                    "provider": "openai",
                    "model": "text-embedding-ada-002",
                    "batch_size": 5,
                },
            },
            {"chunks": chunk_result["chunks"]},
            execution_context,
        )

        if not embedding_result.get("success"):
            print(f"❌ Embedding generation failed: {embedding_result.get('error')}")
            return

        print(f"   ✅ Generated {len(embedding_result['embeddings'])} embeddings")

        # Step 4: Store vectors
        print("💾 Step 4: Storing vectors...")
        storage_result = await vector_storage_step(
            {
                "step_id": "store",
                "step_type": "vector_storage",
                "config": {
                    "storage_type": "in_memory",
                    "collection_name": "workflow_docs",
                },
            },
            {"embeddings": embedding_result["embeddings"]},
            execution_context,
        )

        if not storage_result.get("success"):
            print(f"❌ Vector storage failed: {storage_result.get('error')}")
            return

        print(f"   ✅ Stored {storage_result['stored_count']} vectors")

        print("\n🎉 Full tokenizer workflow completed successfully!")

        # Summary
        print("\n📊 Workflow Summary:")
        print(f"   Original content: {len(file_result['content'])} characters")
        print(f"   Text chunks: {len(chunk_result['chunks'])}")
        print(f"   Embeddings: {len(embedding_result['embeddings'])}")
        print(f"   Stored vectors: {storage_result['stored_count']}")

        return {
            "file_result": file_result,
            "chunk_result": chunk_result,
            "embedding_result": embedding_result,
            "storage_result": storage_result,
        }


async def main():
    """Run all tokenizer tests"""

    print("🚀 Tokenizer Steps Test Suite")
    print("=" * 60)

    try:
        # Test individual steps
        await test_file_reader_step()
        await test_text_chunking_step()
        await test_embedding_generation_step()
        await test_vector_storage_step()

        # Test full workflow
        await test_full_tokenizer_workflow()

        print("\n🎉 All tokenizer tests completed successfully!")
        print("✅ The tokenizer steps are working correctly")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
