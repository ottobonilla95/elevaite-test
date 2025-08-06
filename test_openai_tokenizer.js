#!/usr/bin/env node

/**
 * Test OpenAI Tokenizer Steps (File Reading + Chunking + Embeddings)
 * Tests the tokenizer workflow up to embedding generation without requiring Qdrant
 */

const axios = require('axios');
const fs = require('fs');

const BASE_URL = "http://localhost:8005";
const API_BASE = `${BASE_URL}/api`;
const TEST_FILE_PATH = "/tmp/test-openai-tokenizer.txt";

// Test document content
const TEST_CONTENT = `
# OpenAI Tokenizer Test Document

This document tests the OpenAI integration in the tokenizer workflow.

## Document Processing
The tokenizer workflow processes documents through multiple stages:
1. File reading and content extraction
2. Text chunking with configurable strategies  
3. Embedding generation using OpenAI models
4. Vector storage in databases

## Test Sections
This document contains multiple sections to create several text chunks.
Each chunk will be processed by OpenAI's embedding API.

The embedding generation step supports:
- text-embedding-ada-002 (legacy)
- text-embedding-3-small (efficient) 
- text-embedding-3-large (high quality)

## Quality Metrics
The system tracks processing metrics including:
- Processing time per chunk
- API rate limiting compliance
- Batch efficiency optimization
- Error handling and retries
`;

// Workflow configuration (file reading + chunking + embeddings only)
const OPENAI_TOKENIZER_WORKFLOW = {
  name: "OpenAI Tokenizer Test",
  description: "Test file reading, chunking, and OpenAI embedding generation",
  version: "1.0.0",
  configuration: {
    workflow_id: "openai_tokenizer_test",
    workflow_name: "OpenAI Tokenizer Test",
    workflow_type: "deterministic",
    execution_pattern: "sequential",
    timeout_seconds: 600,
    steps: [
      {
        step_id: "read_test_file",
        step_name: "Read Test File", 
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
        timeout_seconds: 30
      },
      {
        step_id: "chunk_test_content",
        step_name: "Chunk Test Content",
        step_type: "transformation", 
        step_order: 2,
        dependencies: ["read_test_file"],
        input_mapping: {
          content: "read_test_file.content"
        },
        config: {
          tokenizer_step: "text_chunking",
          chunk_strategy: "sliding_window",
          chunk_size: 200,
          overlap: 0.1,
          min_chunk_size: 100,
          max_chunk_size: 400
        },
        timeout_seconds: 60
      },
      {
        step_id: "generate_openai_embeddings",
        step_name: "Generate OpenAI Embeddings",
        step_type: "batch_processing",
        step_order: 3,
        dependencies: ["chunk_test_content"],
        input_mapping: {
          chunks: "chunk_test_content.chunks"
        },
        config: {
          tokenizer_step: "embedding_generation",
          provider: "openai",
          model: "text-embedding-ada-002",
          batch_size: 5,
          max_retries: 2,
          timeout: 30,
          rate_limit_rpm: 1000
        },
        timeout_seconds: 300
      }
    ]
  },
  tags: ["test", "openai", "embeddings"]
};

async function createTestFile() {
  fs.writeFileSync(TEST_FILE_PATH, TEST_CONTENT.trim(), 'utf-8');
  console.log(`✅ Created test file: ${TEST_FILE_PATH}`);
}

async function cleanupTestFile() {
  if (fs.existsSync(TEST_FILE_PATH)) {
    fs.unlinkSync(TEST_FILE_PATH);
    console.log(`🧹 Cleaned up test file: ${TEST_FILE_PATH}`);
  }
}

async function testOpenAITokenizer() {
  console.log("🧪 Testing OpenAI Tokenizer Workflow");
  console.log("=====================================");
  
  // Check if OpenAI API key is available
  if (!process.env.OPENAI_API_KEY) {
    console.log("❌ OPENAI_API_KEY environment variable not set");
    console.log("   Please set your OpenAI API key: export OPENAI_API_KEY='your-key'");
    return;
  }
  
  console.log("✅ OpenAI API key detected");
  
  let workflowId = null;
  
  try {
    // Create test file
    await createTestFile();
    
    // Check API health
    console.log("\n🔍 Checking API health...");
    const healthResponse = await axios.get(`${BASE_URL}/hc`);
    console.log(`✅ API is healthy: ${healthResponse.data.status}`);
    
    // Create workflow
    console.log("\n🔧 Creating OpenAI tokenizer workflow...");
    const workflowResponse = await axios.post(`${API_BASE}/workflows/`, OPENAI_TOKENIZER_WORKFLOW);
    workflowId = workflowResponse.data.workflow_id;
    console.log(`✅ Created workflow: ${workflowId}`);
    console.log(`   Steps: ${workflowResponse.data.configuration.steps.length}`);
    
    // Execute workflow
    console.log("\n⚡ Executing OpenAI tokenizer workflow...");
    const executionPayload = {
      query: "Process test document with OpenAI embeddings",
      session_id: `openai_test_${Date.now()}`,
      user_id: "openai_test_user"
    };
    
    const executionResponse = await axios.post(
      `${API_BASE}/workflows/${workflowId}/execute`, 
      executionPayload,
      { timeout: 120000 } // 2 minute timeout
    );
    
    console.log(`✅ Execution completed`);
    console.log(`   Status: ${executionResponse.data.status}`);
    
    if (executionResponse.data.status === 'success') {
      const response = executionResponse.data.response;
      if (typeof response === 'object') {
        console.log(`   Response keys: ${Object.keys(response).join(', ')}`);
        
        // Check embedding results
        if (response.generate_openai_embeddings) {
          const embeddingData = response.generate_openai_embeddings;
          if (embeddingData.embeddings) {
            console.log(`   📊 Generated ${embeddingData.embeddings.length} embeddings`);
            console.log(`   🔢 Vector dimensions: ${embeddingData.embeddings[0]?.vector?.length || 'unknown'}`);
            console.log(`   ⚡ Processing time: ${embeddingData.metadata?.processing_time_seconds || 'unknown'}s`);
          }
        }
      }
    } else if (executionResponse.data.status === 'error') {
      console.log(`❌ Execution failed`);
      if (executionResponse.data.response && executionResponse.data.response.error) {
        console.log(`   Error: ${executionResponse.data.response.error}`);
      }
    }
    
    console.log("\n🎉 OpenAI tokenizer test completed!");
    
  } catch (error) {
    console.error(`❌ Test failed: ${error.message}`);
    if (error.response && error.response.data) {
      console.error(`   API Error: ${JSON.stringify(error.response.data, null, 2)}`);
    }
  } finally {
    // Cleanup workflow
    if (workflowId) {
      console.log(`\n🧹 Cleaning up workflow: ${workflowId}`);
      try {
        await axios.delete(`${API_BASE}/workflows/${workflowId}`);
        console.log("✅ Workflow deleted");
      } catch (error) {
        console.log(`❌ Failed to delete workflow: ${error.message}`);
      }
    }
    
    // Cleanup test file
    await cleanupTestFile();
  }
}

// Run the test
testOpenAITokenizer().catch(console.error);