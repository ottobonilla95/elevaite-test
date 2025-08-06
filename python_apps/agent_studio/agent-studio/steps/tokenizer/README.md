# Tokenizer Steps for RAG Workflows

This directory contains tokenizer workflow steps designed for Retrieval-Augmented Generation (RAG) applications. These steps integrate with the deterministic workflow framework to provide a complete document processing pipeline.

## Overview

The tokenizer workflow consists of four main steps that process documents from raw files to searchable vectors:

1. **FileReaderStep** - Reads and extracts content from various document formats
2. **TextChunkingStep** - Divides text into manageable, semantically meaningful chunks
3. **EmbeddingGenerationStep** - Generates vector embeddings for text chunks
4. **VectorStorageStep** - Stores embeddings in vector databases for retrieval

## Quick Start

### API Usage

```bash
# 1. Create a tokenizer workflow
curl -X POST "http://localhost:8000/api/workflows/" \
  -H "Content-Type: application/json" \
  -d @workflows/tokenizer_rag_workflow.json

# 2. Execute the workflow
curl -X POST "http://localhost:8000/api/workflows/{workflow_id}/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Process document for RAG",
    "session_id": "session_123",
    "user_id": "user_456"
  }'
```

### Example Workflow Configuration

```json
{
  "workflow_name": "Document RAG Processing",
  "workflow_type": "deterministic",
  "execution_pattern": "sequential",
  "steps": [
    {
      "step_id": "read_document",
      "step_type": "file_reader",
      "config": {
        "file_path": "/path/to/document.pdf",
        "supported_formats": [".pdf", ".docx", ".txt"],
        "max_file_size": 10485760,
        "extract_metadata": true
      }
    },
    {
      "step_id": "chunk_text",
      "step_type": "text_chunking",
      "dependencies": ["read_document"],
      "input_mapping": {
        "content": "read_document.content"
      },
      "config": {
        "chunk_strategy": "semantic",
        "chunk_size": 400,
        "overlap": 0.15
      }
    },
    {
      "step_id": "generate_embeddings",
      "step_type": "embedding_generation",
      "dependencies": ["chunk_text"],
      "input_mapping": {
        "chunks": "chunk_text.chunks"
      },
      "config": {
        "provider": "openai",
        "model": "text-embedding-3-large",
        "batch_size": 20
      }
    },
    {
      "step_id": "store_vectors",
      "step_type": "vector_storage",
      "dependencies": ["generate_embeddings"],
      "input_mapping": {
        "embeddings": "generate_embeddings.embeddings"
      },
      "config": {
        "vector_db": "qdrant",
        "collection_name": "documents",
        "create_collection": true
      }
    }
  ]
}
```

## Step Configurations

### FileReaderStep

Extracts content from various document formats with metadata collection.

**Configuration Options:**
```json
{
  "file_path": "/path/to/document.pdf",
  "supported_formats": [".pdf", ".docx", ".txt", ".html", ".md"],
  "max_file_size": 10485760,
  "encoding": "utf-8",
  "extract_metadata": true,
  "preserve_formatting": false
}
```

**Supported Formats:**
- PDF documents (.pdf)
- Microsoft Word (.docx)
- Plain text (.txt)
- HTML files (.html)
- Markdown (.md)

**Output Schema:**
```json
{
  "content": "Extracted text content",
  "metadata": {
    "file_size": 12345,
    "file_type": "pdf",
    "character_count": 5000,
    "word_count": 800,
    "page_count": 5
  }
}
```

### TextChunkingStep

Divides text into chunks using various strategies for optimal retrieval performance.

**Configuration Options:**
```json
{
  "chunk_strategy": "semantic",
  "chunk_size": 400,
  "overlap": 0.15,
  "min_chunk_size": 100,
  "max_chunk_size": 800,
  "preserve_structure": true,
  "sentence_splitter": "nltk"
}
```

**Chunking Strategies:**

1. **Fixed Size** - Simple character-based chunking
   ```json
   {
     "chunk_strategy": "fixed_size",
     "chunk_size": 500,
     "overlap": 0.1
   }
   ```

2. **Sliding Window** - Overlapping chunks for context preservation
   ```json
   {
     "chunk_strategy": "sliding_window",
     "chunk_size": 400,
     "overlap": 0.2
   }
   ```

3. **Semantic** - Semantically similar sentences grouped together
   ```json
   {
     "chunk_strategy": "semantic",
     "similarity_threshold": 0.7,
     "max_chunk_size": 600
   }
   ```

4. **Sentence-based** - Natural sentence boundaries
   ```json
   {
     "chunk_strategy": "sentence",
     "sentences_per_chunk": 3
   }
   ```

5. **Paragraph-based** - Paragraph boundary preservation
   ```json
   {
     "chunk_strategy": "paragraph",
     "min_paragraphs": 1,
     "max_paragraphs": 3
   }
   ```

**Output Schema:**
```json
{
  "chunks": [
    {
      "content": "Chunk text content",
      "chunk_id": "chunk_001",
      "start_position": 0,
      "end_position": 400,
      "metadata": {
        "chunk_index": 0,
        "word_count": 65,
        "sentence_count": 3
      }
    }
  ],
  "metadata": {
    "total_chunks": 10,
    "average_chunk_size": 380,
    "chunking_strategy": "semantic"
  }
}
```

### EmbeddingGenerationStep

Generates vector embeddings with support for multiple providers and batch processing.

**Configuration Options:**
```json
{
  "provider": "openai",
  "model": "text-embedding-3-large",
  "batch_size": 20,
  "max_retries": 3,
  "retry_delay": 1.0,
  "timeout": 30,
  "rate_limit_rpm": 1000,
  "normalize": true,
  "dimensions": null
}
```

**Supported Providers:**

1. **OpenAI**
   ```json
   {
     "provider": "openai",
     "model": "text-embedding-3-large",
     "api_key": "${OPENAI_API_KEY}"
   }
   ```

2. **Sentence Transformers** (local)
   ```json
   {
     "provider": "sentence_transformers",
     "model": "all-MiniLM-L6-v2",
     "device": "cpu"
   }
   ```

3. **Custom API**
   ```json
   {
     "provider": "custom",
     "api_endpoint": "https://api.example.com/embeddings",
     "api_key": "${CUSTOM_API_KEY}",
     "headers": {"Custom-Header": "value"}
   }
   ```

**Output Schema:**
```json
{
  "embeddings": [
    {
      "chunk_id": "chunk_001",
      "vector": [0.1, -0.2, 0.3, ...],
      "dimensions": 1536,
      "model": "text-embedding-3-large"
    }
  ],
  "metadata": {
    "total_embeddings": 10,
    "embedding_model": "text-embedding-3-large",
    "dimensions": 1536,
    "processing_time": 2.5
  }
}
```

### VectorStorageStep

Stores embeddings in vector databases with metadata and supports multiple backends.

**Configuration Options:**
```json
{
  "vector_db": "qdrant",
  "collection_name": "documents",
  "host": "localhost",
  "port": 6333,
  "distance_metric": "cosine",
  "create_collection": true,
  "batch_size": 50,
  "upsert": true,
  "index_config": {
    "hnsw_ef": 128,
    "hnsw_m": 16
  }
}
```

**Supported Vector Databases:**

1. **Qdrant** (Recommended)
   ```json
   {
     "vector_db": "qdrant",
     "host": "localhost",
     "port": 6333,
     "collection_name": "documents",
     "distance_metric": "cosine",
     "create_collection": true
   }
   ```

2. **ChromaDB** (Local development)
   ```json
   {
     "vector_db": "chromadb",
     "persist_directory": "./chroma_db",
     "collection_name": "documents"
   }
   ```

3. **Pinecone** (Cloud)
   ```json
   {
     "vector_db": "pinecone",
     "api_key": "${PINECONE_API_KEY}",
     "environment": "us-west1-gcp",
     "index_name": "documents"
   }
   ```

4. **Custom API**
   ```json
   {
     "vector_db": "custom",
     "api_endpoint": "https://vectordb.example.com/api",
     "api_key": "${VECTOR_DB_API_KEY}"
   }
   ```

**Output Schema:**
```json
{
  "stored_vectors": [
    {
      "vector_id": "vec_001",
      "chunk_id": "chunk_001",
      "status": "stored"
    }
  ],
  "metadata": {
    "total_stored": 10,
    "collection_name": "documents",
    "storage_time": 1.2,
    "index_updated": true
  }
}
```

## Example Workflows

### Basic RAG Processing
```bash
# Use the basic workflow configuration
cat workflows/tokenizer_rag_workflow.json
```

### High-Quality Semantic Processing
```bash
# Use semantic chunking with high-quality embeddings
cat workflows/tokenizer_semantic_rag_workflow.json
```

### Hybrid Agent Integration
```bash
# Combine deterministic tokenizer with AI agent routing
cat workflows/hybrid_tokenizer_agent_workflow.json
```

## Testing

### Unit Tests
```bash
# Test individual steps
python test_tokenizer_workflow.py
```

### API Integration Tests
```bash
# Test full API workflow
python test_tokenizer_api.py
```

### E2E Tests
```bash
# Run comprehensive E2E tests
cd tests/e2e
npm run test:tokenizer
```

## Dependencies

### Required Python Packages
```bash
pip install openai qdrant-client chromadb nltk sentence-transformers
```

### Optional Dependencies
```bash
# For PDF processing
pip install pypdf2 pdfplumber

# For DOCX processing
pip install python-docx

# For advanced text processing
pip install spacy transformers
```

### External Services

1. **OpenAI API** (for embeddings)
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. **Qdrant Database** (recommended)
   ```bash
   docker run -p 6333:6333 qdrant/qdrant
   ```

3. **ChromaDB** (local alternative)
   ```bash
   # Automatically installed with pip install chromadb
   ```

## Performance Tuning

### Batch Processing
- Adjust `batch_size` based on API rate limits and memory constraints
- OpenAI: 100-500 chunks per batch recommended
- Local models: 50-200 chunks per batch

### Rate Limiting
- Set `rate_limit_rpm` to respect API limits
- Use `retry_delay` and `max_retries` for robust error handling

### Memory Optimization
- Process large documents in streaming mode
- Use appropriate chunk sizes (200-800 characters typically optimal)
- Consider semantic chunking for better retrieval quality

### Vector Database Optimization
- Use HNSW indexing for large collections (>10k vectors)
- Adjust `hnsw_ef` and `hnsw_m` parameters for speed/accuracy tradeoff
- Enable compression for storage efficiency

## Error Handling

The tokenizer steps include comprehensive error handling:

- **Validation errors** - Invalid configurations or input data
- **File processing errors** - Unsupported formats, corrupted files
- **API errors** - Rate limits, authentication, network issues
- **Database errors** - Connection failures, storage limits
- **Rollback support** - Automatic cleanup on step failures

## Monitoring and Logging

- Progress tracking for long-running operations
- Detailed logging for debugging and monitoring
- Metrics collection for performance analysis
- Integration with workflow analytics system

## Security Considerations

- API keys stored securely in environment variables
- Input validation and sanitization
- File size and format restrictions
- No sensitive data logged
- Secure vector database connections

## Troubleshooting

### Common Issues

1. **OpenAI API Key not found**
   ```bash
   export OPENAI_API_KEY="your-api-key"
   ```

2. **Qdrant connection refused**
   ```bash
   docker run -d -p 6333:6333 qdrant/qdrant
   ```

3. **Out of memory during processing**
   - Reduce batch sizes
   - Use streaming mode for large files
   - Increase system memory

4. **Slow embedding generation**
   - Use faster models (text-embedding-ada-002 vs text-embedding-3-large)
   - Increase batch sizes within rate limits
   - Consider local sentence transformer models

### Debug Mode
```json
{
  "config": {
    "debug": true,
    "verbose_logging": true,
    "save_intermediate_results": true
  }
}
```

## Contributing

When adding new tokenizer steps:

1. Extend the appropriate base step class
2. Implement required methods: `execute()`, `validate_config()`
3. Add comprehensive error handling
4. Include unit tests
5. Update the step registry
6. Document configuration options

## License

This tokenizer implementation is part of the Agent Studio platform and follows the same licensing terms.