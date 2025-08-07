#!/usr/bin/env node

/**
 * Test Complete Tokenizer RAG Workflow
 * Tests all 4 steps: File Reading + Chunking + OpenAI Embeddings + Qdrant Storage
 */

const axios = require('axios');
const fs = require('fs');

const BASE_URL = "http://localhost:8005";
const API_BASE = `${BASE_URL}/api`;
const TEST_FILE_PATH = "/tmp/test-full-rag.txt";

// Test document content optimized for RAG
const TEST_CONTENT = `
# Complete RAG Pipeline Test Document

This document validates the end-to-end tokenizer RAG workflow implementation.

## Document Processing Pipeline
The complete pipeline processes documents through four critical stages:

### 1. File Reading Stage
- Extracts content from multiple document formats
- Preserves document structure and metadata
- Handles encoding detection automatically
- Validates file size and format constraints

### 2. Text Chunking Stage  
- Applies configurable chunking strategies
- Maintains semantic coherence across chunks
- Optimizes chunk sizes for retrieval performance
- Preserves document structure when required

### 3. Embedding Generation Stage
- Generates high-quality vector embeddings
- Supports multiple embedding providers
- Implements batch processing for efficiency
- Includes rate limiting and retry mechanisms

### 4. Vector Storage Stage
- Stores embeddings in production vector databases
- Creates optimized indexes for fast retrieval
- Maintains metadata associations
- Enables similarity search capabilities

## Quality Assurance
Each stage includes comprehensive error handling, progress tracking, and rollback capabilities to ensure reliable operation in production environments.

## Use Cases
This pipeline enables advanced RAG applications including document Q&A, knowledge base search, content recommendation, and semantic retrieval systems.
`;

// Complete 4-step RAG workflow
const COMPLETE_RAG_WORKFLOW = {
  name: "Complete RAG Pipeline Test",
  description: "End-to-end test of file reading, chunking, embeddings, and vector storage",
  version: "1.0.0", 
  configuration: {
    workflow_id: "complete_rag_test",
    workflow_name: "Complete RAG Pipeline Test",
    workflow_type: "deterministic",
    execution_pattern: "sequential",
    uses_tokenizer_steps: true,
    timeout_seconds: 900,
    steps: [
      {
        step_id: "read_document",
        step_name: "Read Test Document",
        step_type: "data_input",
        step_order: 1,
        config: {
          tokenizer_step: "file_reader",
          file_path: TEST_FILE_PATH,
          supported_formats: [".txt"],
          max_file_size: 1048576,
          encoding: "utf-8",
          extract_metadata: true
        },
        timeout_seconds: 60
      },
      {
        step_id: "chunk_text",
        step_name: "Chunk Document Text", 
        step_type: "transformation",
        step_order: 2,
        dependencies: ["read_document"],
        input_mapping: {
          content: "read_document.content"
        },
        config: {
          tokenizer_step: "text_chunking", 
          chunk_strategy: "sliding_window",
          chunk_size: 300,
          overlap: 0.15,
          min_chunk_size: 100,
          max_chunk_size: 500
        },
        timeout_seconds: 120
      },
      {
        step_id: "generate_embeddings",
        step_name: "Generate OpenAI Embeddings",
        step_type: "batch_processing",
        step_order: 3,
        dependencies: ["chunk_text"],
        input_mapping: {
          chunks: "chunk_text.chunks"
        },
        config: {
          tokenizer_step: "embedding_generation",
          provider: "openai",
          model: "text-embedding-ada-002",
          batch_size: 10,
          max_retries: 2,
          timeout: 45,
          rate_limit_rpm: 1000
        },
        timeout_seconds: 600
      },
      {
        step_id: "store_vectors", 
        step_name: "Store in Qdrant Database",
        step_type: "data_output",
        step_order: 4,
        dependencies: ["generate_embeddings"],
        input_mapping: {
          embeddings: "generate_embeddings.embeddings"
        },
        config: {
          tokenizer_step: "vector_storage",
          vector_db: "qdrant",
          collection_name: `test_rag_${Date.now()}`,
          host: "localhost",
          port: 6333,
          distance_metric: "cosine",
          create_collection: true,
          batch_size: 50,
          upsert: true
        },
        timeout_seconds: 300
      }
    ]
  },
  tags: ["test", "rag", "complete", "openai", "qdrant"]
};

async function createTestDocument() {
  fs.writeFileSync(TEST_FILE_PATH, TEST_CONTENT.trim(), 'utf-8');
  console.log(`✅ Created test document: ${TEST_FILE_PATH} (${TEST_CONTENT.length} chars)`);
}

async function cleanupTestFile() {
  if (fs.existsSync(TEST_FILE_PATH)) {
    fs.unlinkSync(TEST_FILE_PATH);
    console.log(`🧹 Cleaned up test file: ${TEST_FILE_PATH}`);
  }
}

async function testCompleteRAGWorkflow() {
  console.log("🧪 Testing Complete Tokenizer RAG Workflow");
  console.log("==========================================");
  
  let workflowId = null;
  
  try {
    // Create test document
    await createTestDocument();
    
    // Verify services are available
    console.log("\n🔍 Verifying services...");
    
    // Check API
    const healthResponse = await axios.get(`${BASE_URL}/hc`);
    console.log(`✅ API server: ${healthResponse.data.status}`);
    
    // Check Qdrant
    const qdrantResponse = await axios.get("http://localhost:6333/");
    console.log(`✅ Qdrant database: v${qdrantResponse.data.version}`);
    
    // Create complete RAG workflow
    console.log("\n🔧 Creating complete RAG workflow...");
    const workflowResponse = await axios.post(`${API_BASE}/workflows/`, COMPLETE_RAG_WORKFLOW);
    workflowId = workflowResponse.data.workflow_id;
    console.log(`✅ Created workflow: ${workflowId}`);
    console.log(`   Name: ${workflowResponse.data.name}`);
    console.log(`   Steps: ${workflowResponse.data.configuration.steps.length}`);
    
    // Execute complete pipeline
    console.log("\n⚡ Executing complete RAG pipeline...");
    console.log("   This will test:");
    console.log("   1️⃣  File reading and content extraction");
    console.log("   2️⃣  Text chunking with sliding window strategy");
    console.log("   3️⃣  OpenAI embedding generation (ada-002)");
    console.log("   4️⃣  Qdrant vector storage with collection creation");
    
    const executionPayload = {
      query: "Process complete RAG pipeline test",
      session_id: `rag_test_${Date.now()}`,
      user_id: "rag_test_user"
    };
    
    const startTime = Date.now();
    const executionResponse = await axios.post(
      `${API_BASE}/workflows/${workflowId}/execute`,
      executionPayload,
      { timeout: 180000 } // 3 minute timeout
    );
    const executionTime = ((Date.now() - startTime) / 1000).toFixed(1);
    
    console.log(`\n🎉 Pipeline execution completed in ${executionTime}s`);
    console.log(`   Status: ${executionResponse.data.status}`);
    
    if (executionResponse.data.status === 'success') {
      const response = executionResponse.data.response;
      console.log(`\n📊 Pipeline Results:`);
      console.log(`   Response keys: ${Object.keys(response).join(', ')}`);
      
      // Analyze results from each step
      if (response.read_document) {
        const docData = response.read_document;
        console.log(`   📄 Document: ${docData.metadata?.character_count || 'unknown'} chars, ${docData.metadata?.word_count || 'unknown'} words`);
      }
      
      if (response.chunk_text) {
        const chunkData = response.chunk_text;
        console.log(`   📝 Chunks: ${chunkData.chunks?.length || 'unknown'} chunks created`);
        console.log(`   📏 Avg size: ${chunkData.metadata?.average_chunk_size || 'unknown'} chars`);
      }
      
      if (response.generate_embeddings) {
        const embeddingData = response.generate_embeddings;
        console.log(`   🔢 Embeddings: ${embeddingData.embeddings?.length || 'unknown'} vectors`);
        console.log(`   📐 Dimensions: ${embeddingData.embeddings?.[0]?.vector?.length || 'unknown'}`);
        console.log(`   ⚡ Time: ${embeddingData.metadata?.processing_time_seconds || 'unknown'}s`);
      }
      
      if (response.store_vectors) {
        const storageData = response.store_vectors; 
        console.log(`   💾 Storage: ${storageData.storage_result?.stored_vectors || 'unknown'} vectors stored`);
        console.log(`   🗄️  Collection: ${storageData.storage_result?.collection_name || 'unknown'}`);
        console.log(`   ⚡ Time: ${storageData.metadata?.processing_time_seconds || 'unknown'}s`);
      }
      
      console.log(`\n✅ Complete RAG pipeline test SUCCESSFUL! 🚀`);
      console.log(`   All 4 stages completed successfully:`);
      console.log(`   ✅ File Reading → Text Chunking → Embeddings → Vector Storage`);
      
    } else if (executionResponse.data.status === 'error') {
      console.log(`\n❌ Pipeline execution FAILED`);
      const error = executionResponse.data.response;
      if (error && error.error) {
        console.log(`   Error: ${error.error}`);
      }
    }
    
  } catch (error) {
    console.error(`\n❌ Test failed: ${error.message}`);
    if (error.response && error.response.data) {
      console.error(`   API Response: ${JSON.stringify(error.response.data, null, 2)}`);
    }
  } finally {
    // Cleanup workflow
    if (workflowId) {
      console.log(`\n🧹 Cleaning up workflow: ${workflowId}`);
      try {
        await axios.delete(`${API_BASE}/workflows/${workflowId}`);
        console.log("✅ Workflow deleted successfully");
      } catch (error) {
        console.log(`❌ Failed to delete workflow: ${error.message}`);
      }
    }
    
    // Cleanup test file
    await cleanupTestFile();
  }
}

// Run the complete test
testCompleteRAGWorkflow().catch(console.error);