"""
Example Workflow Configurations

This module contains example workflow configurations for testing and demonstration.
These examples showcase different features and patterns of the workflow engine:

- EXAMPLE_SIMPLE_WORKFLOW: Basic sequential workflow with data processing
- EXAMPLE_AGENT_WORKFLOW: Workflow with AI agent execution
- EXAMPLE_PARALLEL_WORKFLOW: Parallel execution with data merging
- EXAMPLE_SUBFLOW_CHILD: Reusable subflow for text processing
- EXAMPLE_SUBFLOW_PARENT: Parent workflow that uses subflows
"""

# Example workflow configurations for testing
EXAMPLE_SIMPLE_WORKFLOW = {
    "name": "Simple Test Workflow",
    "description": "A simple workflow for testing",
    "execution_pattern": "sequential",
    "steps": [
        {
            "step_id": "step1",
            "step_name": "Initialize",
            "step_type": "data_input",
            "step_order": 1,
            "config": {"input_type": "static", "data": {"message": "Hello, World!"}},
        },
        {
            "step_id": "step2",
            "step_name": "Process",
            "step_type": "data_processing",
            "step_order": 2,
            "dependencies": ["step1"],
            "input_mapping": {"input_data": "step1.data"},
            "config": {
                "processing_type": "transform",
                "options": {"transformation": "uppercase"},
            },
        },
    ],
}

EXAMPLE_AGENT_WORKFLOW = {
    "name": "Agent Execution Workflow",
    "description": "Workflow with agent execution",
    "execution_pattern": "sequential",
    "steps": [
        {
            "step_id": "setup_data",
            "step_name": "Setup Data",
            "step_type": "data_input",
            "step_order": 1,
            "config": {
                "input_type": "static",
                "data": {"content": "This is a sample text for analysis."},
            },
        },
        {
            "step_id": "analyze_content",
            "step_name": "Analyze Content",
            "step_type": "agent_execution",
            "step_order": 2,
            "dependencies": ["setup_data"],
            "input_mapping": {"content": "setup_data.data.content"},
            "config": {
                "agent_name": "Content Analyzer",
                "system_prompt": "You are a content analyzer. Analyze the provided content and summarize it.",
                "query": "Please analyze and summarize the provided content: {content}",
                "tools": [],
                "force_real_llm": False,
            },
        },
    ],
}

EXAMPLE_PARALLEL_WORKFLOW = {
    "name": "Parallel Processing Workflow",
    "description": "Workflow with parallel step execution",
    "execution_pattern": "parallel",
    "steps": [
        {
            "step_id": "init",
            "step_name": "Initialize Data",
            "step_type": "data_input",
            "step_order": 1,
            "config": {
                "input_type": "static",
                "data": {"text": "This is a sample text for parallel processing."},
            },
        },
        {
            "step_id": "process_a",
            "step_name": "Process A",
            "step_type": "data_processing",
            "step_order": 2,
            "dependencies": ["init"],
            "input_mapping": {"text": "init.data.text"},
            "config": {"processing_type": "count"},
        },
        {
            "step_id": "process_b",
            "step_name": "Process B",
            "step_type": "data_processing",
            "step_order": 2,
            "dependencies": ["init"],
            "input_mapping": {"text": "init.data.text"},
            "config": {"processing_type": "sentiment_analysis"},
        },
        {
            "step_id": "merge",
            "step_name": "Merge Results",
            "step_type": "data_merge",
            "step_order": 3,
            "dependencies": ["process_a", "process_b"],
            "input_mapping": {
                "data_sources": {
                    "word_count": "process_a.result",
                    "sentiment": "process_b.result",
                }
            },
            "config": {"merge_strategy": "combine"},
        },
    ],
}

# Example subflow workflows for testing nested execution
EXAMPLE_SUBFLOW_CHILD = {
    "workflow_id": "text-processing-subflow",
    "name": "Text Processing Subflow",
    "description": "A reusable subflow for text processing operations",
    "execution_pattern": "sequential",
    "steps": [
        {
            "step_id": "input_step",
            "step_name": "Get Input",
            "step_type": "data_input",
            "step_order": 1,
            "config": {"input_type": "dynamic", "source": "subflow_input"},
        },
        {
            "step_id": "process_text",
            "step_name": "Process Text",
            "step_type": "data_processing",
            "step_order": 2,
            "dependencies": ["input_step"],
            "input_mapping": {"input_data": "input_step.data"},
            "config": {
                "processing_type": "transform",
                "options": {"transformation": "uppercase"},
            },
        },
        {
            "step_id": "add_metadata",
            "step_name": "Add Metadata",
            "step_type": "data_processing",
            "step_order": 3,
            "dependencies": ["process_text"],
            "input_mapping": {"input_data": "process_text.result"},
            "config": {
                "processing_type": "transform",
                "options": {
                    "transformation": "identity",
                    "metadata": {
                        "processed_by": "text-processing-subflow",
                        "processing_timestamp": "auto",
                    },
                },
            },
        },
    ],
}

EXAMPLE_SUBFLOW_PARENT = {
    "workflow_id": "document-processing-workflow",
    "name": "Document Processing with Subflows",
    "description": "A workflow that uses subflows for modular text processing",
    "execution_pattern": "sequential",
    "steps": [
        {
            "step_id": "initialize",
            "step_name": "Initialize Document",
            "step_type": "data_input",
            "step_order": 1,
            "config": {
                "input_type": "static",
                "data": {
                    "document": {
                        "title": "Sample Document",
                        "content": "This is a sample document for processing.",
                        "author": "Test User",
                    }
                },
            },
        },
        {
            "step_id": "process_title",
            "step_name": "Process Document Title",
            "step_type": "subflow",
            "step_order": 2,
            "dependencies": ["initialize"],
            "config": {
                "workflow_id": "text-processing-subflow",
                "input_mapping": {"text": "initialize.data.document.title"},
                "output_mapping": {"processed_title": "add_metadata.result"},
                "inherit_context": True,
            },
        },
        {
            "step_id": "process_content",
            "step_name": "Process Document Content",
            "step_type": "subflow",
            "step_order": 3,
            "dependencies": ["initialize"],
            "config": {
                "workflow_id": "text-processing-subflow",
                "input_mapping": {"text": "initialize.data.document.content"},
                "output_mapping": {"processed_content": "add_metadata.result"},
                "inherit_context": True,
            },
        },
        {
            "step_id": "combine_results",
            "step_name": "Combine Processed Results",
            "step_type": "data_merge",
            "step_order": 4,
            "dependencies": ["process_title", "process_content"],
            "input_mapping": {
                "data_sources": {
                    "title": "process_title.processed_title",
                    "content": "process_content.processed_content",
                    "original_author": "initialize.data.document.author",
                }
            },
        },
    ],
}

# RAG (Retrieval-Augmented Generation) workflow example
EXAMPLE_RAG_WORKFLOW = {
    "workflow_id": "rag-document-processing",
    "name": "RAG Document Processing",
    "description": "Complete RAG workflow: file reading, chunking, embedding, storage, and querying",
    "execution_pattern": "sequential",
    "steps": [
        {
            "step_id": "read_document",
            "step_name": "Read Document",
            "step_type": "file_reader",
            "step_order": 1,
            "config": {
                "file_path": "/path/to/document.pdf",
                "supported_formats": ["pdf", "docx", "txt"],
            },
        },
        {
            "step_id": "chunk_text",
            "step_name": "Chunk Text",
            "step_type": "text_chunking",
            "step_order": 2,
            "dependencies": ["read_document"],
            "input_mapping": {"content": "read_document.content"},
            "config": {
                "strategy": "sliding_window",
                "chunk_size": 1000,
                "overlap": 100,
            },
        },
        {
            "step_id": "generate_embeddings",
            "step_name": "Generate Embeddings",
            "step_type": "embedding_generation",
            "step_order": 3,
            "dependencies": ["chunk_text"],
            "input_mapping": {"chunks": "chunk_text.chunks"},
            "config": {
                "model": "text-embedding-ada-002",
                "batch_size": 10,
            },
        },
        {
            "step_id": "store_vectors",
            "step_name": "Store Vectors",
            "step_type": "vector_storage",
            "step_order": 4,
            "dependencies": ["generate_embeddings"],
            "input_mapping": {
                "embeddings": "generate_embeddings.embeddings",
                "chunks": "chunk_text.chunks",
            },
            "config": {
                "storage_type": "qdrant",
                "collection_name": "documents",
                "qdrant_host": "localhost",
                "qdrant_port": 6333,
            },
        },
    ],
}
