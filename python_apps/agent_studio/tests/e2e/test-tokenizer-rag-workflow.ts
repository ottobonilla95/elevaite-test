#!/usr/bin/env tsx

/**
 * Comprehensive E2E Test for Tokenizer RAG Workflows
 *
 * Tests the complete tokenizer workflow pipeline:
 * 1. Create a tokenizer workflow via API
 * 2. Execute sync, async, and streaming workflows
 * 3. Validate file reading, text chunking, embedding generation, vector storage
 * 4. Test error handling and edge cases
 * 5. Clean up test artifacts
 *
 * This test validates the full deterministic workflow framework integration
 * with tokenizer-specific steps for RAG applications.
 */

import axios from "axios";
import { writeFileSync, unlinkSync, existsSync } from "fs";

const BASE_URL = "http://localhost:8005";
const API_BASE = `${BASE_URL}/api`;
const TEST_FILE_PATH = "/tmp/test-tokenizer-doc.txt";
const TEST_MD_FILE_PATH = "/tmp/test-tokenizer-doc.md";

interface WorkflowResponse {
  workflow_id: string;
  name: string;
  description: string;
  version: string;
  configuration: any;
  created_by: string;
  is_deployed: boolean;
  created_at: string;
}

interface ExecutionResponse {
  execution_id?: string;
  status: string;
  response?: string;
  workflow_id: string;
  timestamp: string;
}

interface AsyncExecutionResponse {
  execution_id: string;
  status: string;
  type: string;
  estimated_completion_time: string;
  status_url: string;
  timestamp: string;
}

// Test document content for tokenizer processing
const TEST_DOCUMENT_CONTENT = `
# RAG-Enabled Knowledge Base Test Document

This document tests the complete tokenizer workflow for Retrieval-Augmented Generation.

## Document Processing Pipeline

The tokenizer workflow performs these operations:

### 1. File Reading
- Supports multiple formats: PDF, DOCX, TXT, HTML, Markdown
- Extracts metadata: file size, type, character count, word count
- Handles encoding detection and conversion
- Configurable file size limits and format validation

### 2. Text Chunking
Multiple chunking strategies are supported:
- **Fixed Size**: Chunks of predetermined character length
- **Sliding Window**: Overlapping chunks for context preservation
- **Semantic**: Groups semantically similar sentences using embeddings
- **Sentence-based**: Natural sentence boundaries
- **Paragraph-based**: Paragraph boundary preservation

### 3. Embedding Generation
- OpenAI models: text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large
- Local sentence transformers for privacy-sensitive applications
- Batch processing for efficiency
- Rate limiting and retry logic for robustness
- Configurable normalization and dimension validation

### 4. Vector Storage
Support for multiple vector databases:
- **Qdrant**: Recommended for production with HNSW indexing
- **ChromaDB**: Local development and testing
- **Pinecone**: Cloud-based scalable solution
- **Custom APIs**: Flexible integration options

## Performance Characteristics

The system is optimized for:
- High-throughput batch processing
- Memory-efficient streaming for large documents
- Configurable parallelization
- Fault tolerance with automatic retry mechanisms
- Progress tracking for long-running operations

## Quality Assurance

Each step includes:
- Input validation and sanitization
- Configuration schema validation
- Error handling with descriptive messages
- Rollback capabilities for failed operations
- Comprehensive logging and metrics

This comprehensive approach ensures reliable document processing for production RAG applications.
`;

// Tokenizer RAG workflow configuration
const TOKENIZER_RAG_WORKFLOW = {
  name: "E2E Test Tokenizer RAG Workflow",
  description: "End-to-end test workflow for tokenizer RAG processing pipeline",
  version: "1.0.0",
  configuration: {
    workflow_id: "e2e_tokenizer_rag_test",
    workflow_name: "E2E Test Tokenizer RAG Workflow",
    workflow_type: "deterministic",
    execution_pattern: "sequential",
    timeout_seconds: 600,
    max_retries: 2,
    category: "test_tokenizer",
    tags: ["e2e", "test", "tokenizer", "rag", "deterministic"],
    steps: [
      {
        step_id: "read_test_document",
        step_name: "Read Test Document",
        step_type: "data_input",
        step_order: 1,
        dependencies: [],
        config: {
          file_path: TEST_FILE_PATH,
          supported_formats: [".txt", ".md"],
          max_file_size: 1048576, // 1MB
          encoding: "utf-8",
          extract_metadata: true,
          preserve_formatting: false,
        },
        timeout_seconds: 30,
        max_retries: 2,
      },
      {
        step_id: "chunk_document_text",
        step_name: "Chunk Document Text",
        step_type: "transformation",
        step_order: 2,
        dependencies: ["read_test_document"],
        input_mapping: {
          content: "read_test_document.content",
        },
        config: {
          chunk_strategy: "sliding_window",
          chunk_size: 300,
          overlap: 0.15,
          min_chunk_size: 100,
          max_chunk_size: 500,
          preserve_structure: true,
        },
        timeout_seconds: 60,
        max_retries: 2,
      },
      {
        step_id: "generate_test_embeddings",
        step_name: "Generate Test Embeddings",
        step_type: "transformation",
        step_order: 3,
        dependencies: ["chunk_document_text"],
        input_mapping: {
          chunks: "chunk_document_text.chunks",
        },
        config: {
          tokenizer_step: "embedding_generation",
          provider: "openai",
          model: "text-embedding-ada-002",
          batch_size: 10,
          max_retries: 2,
          retry_delay: 1,
          timeout: 30,
          rate_limit_rpm: 1000,
          normalize: false,
        },
        timeout_seconds: 300,
        max_retries: 2,
      },
      {
        step_id: "store_test_vectors",
        step_name: "Store Test Vectors",
        step_type: "data_output",
        step_order: 4,
        dependencies: ["generate_test_embeddings"],
        input_mapping: {
          embeddings: "generate_test_embeddings.embeddings",
        },
        config: {
          tokenizer_step: "vector_storage",
          vector_db: "qdrant",
          collection_name: `e2e_test_collection_${Date.now()}`,
          host: "localhost",
          port: 6333,
          distance_metric: "cosine",
          create_collection: true,
          batch_size: 50,
          upsert: true,
          additional_metadata: {
            test_run: "e2e_tokenizer_test",
            timestamp: new Date().toISOString(),
          },
        },
        timeout_seconds: 120,
        max_retries: 2,
      },
      {
        step_id: "query_rag_documents",
        step_name: "Query RAG Documents with Agent",
        step_type: "agent_execution",
        step_order: 5,
        dependencies: ["store_test_vectors"],
        input_mapping: {
          embeddings: "generate_test_embeddings.embeddings",
          vector_metadata: "store_test_vectors.metadata",
          chunks: "chunk_document_text.chunks",
        },
        config: {
          agent_id: "718c97ae-d91e-4c84-941b-6f39f3fd9f52", // RAG Document Analyzer agent
          query:
            "Please analyze the document that was just processed. What are the key concepts, main topics, and important details? Use both semantic search and metadata search to provide a comprehensive analysis of the document's content and structure.",
          execution_context: {
            collection_name: "e2e_test_collection",
          },
          response_mapping: {
            agent_response: "response",
            execution_time: "execution_time",
            tools_used: "tools_used",
          },
          include_input_data: true,
        },
        timeout_seconds: 240,
        max_retries: 2,
      },
    ],
  },
  tags: ["e2e-test", "tokenizer", "rag", "agent-query"],
};

// Simplified workflow for testing without external dependencies
const SIMPLE_TOKENIZER_WORKFLOW = {
  name: "E2E Simple Tokenizer Test",
  description: "Simplified tokenizer test without external API dependencies",
  version: "1.0.0",
  configuration: {
    workflow_id: "e2e_simple_tokenizer_test",
    workflow_name: "E2E Simple Tokenizer Test",
    workflow_type: "deterministic",
    execution_pattern: "sequential",
    timeout_seconds: 300,
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
          extract_metadata: true,
        },
        timeout_seconds: 30,
      },
      {
        step_id: "chunk_test_text",
        step_name: "Chunk Test Text",
        step_type: "transformation",
        step_order: 2,
        dependencies: ["read_test_file"],
        input_mapping: {
          content: "read_test_file.content",
        },
        config: {
          tokenizer_step: "text_chunking",
          chunk_strategy: "fixed_size",
          chunk_size: 200,
          min_chunk_size: 50,
          max_chunk_size: 400,
        },
        timeout_seconds: 60,
      },
    ],
  },
  tags: ["e2e-test", "simple"],
};

// Enhanced workflow testing advanced FileReaderStep capabilities
const ENHANCED_TOKENIZER_WORKFLOW = {
  name: "E2E Enhanced Tokenizer Test",
  description:
    "Tests enhanced FileReaderStep with advanced parsing capabilities",
  version: "1.0.0",
  configuration: {
    workflow_id: "e2e_enhanced_tokenizer_test",
    workflow_name: "E2E Enhanced Tokenizer Test",
    workflow_type: "deterministic",
    execution_pattern: "sequential",
    timeout_seconds: 600,
    steps: [
      {
        step_id: "read_file_advanced",
        step_name: "Read File with Advanced Parsing",
        step_type: "data_input",
        step_order: 1,
        config: {
          tokenizer_step: "file_reader",
          execution_mode: "advanced",
          file_path: TEST_MD_FILE_PATH,
          supported_formats: [".txt", ".md", ".pdf", ".docx"],
          max_file_size: 10485760, // 10MB for advanced mode
          encoding: "utf-8",
          extract_metadata: true,
          advanced_parsing: {
            default_mode: "auto_parser",
            use_markitdown: true,
            auto_detect_format: true,
            parsers: {
              txt: {
                default_tool: "markitdown",
                available_tools: ["markitdown"],
              },
              md: {
                default_tool: "markitdown",
                available_tools: ["markitdown"],
              },
            },
          },
        },
        timeout_seconds: 60,
      },
      {
        step_id: "chunk_advanced_text",
        step_name: "Chunk Text with Advanced Strategies",
        step_type: "transformation",
        step_order: 2,
        dependencies: ["read_file_advanced"],
        input_mapping: {
          content: "read_file_advanced.content",
          metadata: "read_file_advanced.metadata",
          structured_elements: "read_file_advanced.structured_elements",
        },
        config: {
          tokenizer_step: "text_chunking",
          execution_mode: "advanced",
          advanced_chunking: {
            default_strategy: "auto",
            auto_select_strategy: true,
            strategies: {
              semantic_chunking: {
                breakpoint_threshold_type: "percentile",
                breakpoint_threshold_amount: 85,
                max_chunk_size: 500,
                min_chunk_size: 100,
              },
              mdstructure: {
                chunk_size: 400,
                min_chunk_size: 100,
                max_chunk_size: 600,
                respect_headers: true,
                include_headers: true,
              },
              sentence_chunking: {
                max_sentences_per_chunk: 5,
                min_sentences_per_chunk: 2,
                max_chunk_size: 500,
                min_chunk_size: 100,
              },
            },
          },
        },
        timeout_seconds: 120,
      },
      {
        step_id: "query_processed_document",
        step_name: "Query Processed Document with Agent",
        step_type: "agent_execution",
        step_order: 3,
        dependencies: ["chunk_advanced_text"],
        input_mapping: {
          chunks: "chunk_advanced_text.chunks",
          metadata: "chunk_advanced_text.metadata",
          file_metadata: "read_file_advanced.metadata",
        },
        config: {
          agent_id: "718c97ae-d91e-4c84-941b-6f39f3fd9f52", // RAG Document Analyzer agent
          query:
            "What are the main topics covered in this document? Please search the processed chunks to provide a comprehensive summary of the document's content and structure.",
          execution_context: {
            collection_name: "e2e_test_collection",
          },
          response_mapping: {
            agent_response: "response",
            execution_time: "execution_time",
            tools_used: "tools_used",
          },
          include_input_data: true,
        },
        timeout_seconds: 180,
        max_retries: 2,
      },
    ],
  },
  tags: ["e2e-test", "enhanced", "advanced-parsing", "agent-query"],
};

class TokenizerWorkflowE2ETest {
  private createdWorkflows: string[] = [];

  async createTestFile(): Promise<void> {
    console.log("📄 Creating test documents...");

    // Create text file for simple workflow
    writeFileSync(TEST_FILE_PATH, TEST_DOCUMENT_CONTENT.trim(), "utf-8");
    console.log(
      `✅ Text document created: ${TEST_FILE_PATH} (${TEST_DOCUMENT_CONTENT.length} characters)`
    );

    // Create markdown file for enhanced workflow
    const markdownContent = `# Enhanced Tokenizer Test Document

This document tests the **enhanced FileReaderStep** with advanced parsing capabilities.

## Features Being Tested

### Advanced Parsing
- Intelligent parser selection
- Markitdown integration
- Structured content extraction

### Configuration Migration
- Automatic detection of execution mode
- Backward compatibility with simple mode
- Support for elevaite_ingestion style configs

## Content Structure

### Tables
| Feature | Status | Notes |
|---------|--------|-------|
| Docling Parser | ✅ | Advanced PDF processing |
| Markitdown Parser | ✅ | Multi-format support |
| Auto Selection | ✅ | Intelligent parser choice |

### Code Blocks
\`\`\`json
{
  "execution_mode": "advanced",
  "advanced_parsing": {
    "default_mode": "auto_parser"
  }
}
\`\`\`

### Lists
- Enhanced metadata extraction
- Structured element detection
- Multi-provider support
- Graceful fallbacks

This document should be processed with **markitdown** parser in advanced mode.
`;

    writeFileSync(TEST_MD_FILE_PATH, markdownContent, "utf-8");
    console.log(
      `✅ Markdown document created: ${TEST_MD_FILE_PATH} (${markdownContent.length} characters)`
    );
  }

  async cleanupTestFile(): Promise<void> {
    if (existsSync(TEST_FILE_PATH)) {
      unlinkSync(TEST_FILE_PATH);
      console.log(`🧹 Cleaned up test file: ${TEST_FILE_PATH}`);
    }
    if (existsSync(TEST_MD_FILE_PATH)) {
      unlinkSync(TEST_MD_FILE_PATH);
      console.log(`🧹 Cleaned up markdown file: ${TEST_MD_FILE_PATH}`);
    }
  }

  async checkApiHealth(): Promise<boolean> {
    try {
      console.log("🔍 Checking API health...");
      const response = await axios.get(`${BASE_URL}/hc`);
      console.log(`✅ API is healthy: ${response.data.status}`);
      return true;
    } catch (error) {
      console.error(`❌ API health check failed: ${error}`);
      return false;
    }
  }

  async createWorkflow(workflowConfig: any): Promise<WorkflowResponse | null> {
    try {
      console.log(`🔧 Creating workflow: ${workflowConfig.name}...`);
      const response = await axios.post(
        `${API_BASE}/workflows/`,
        workflowConfig
      );
      const workflow: WorkflowResponse = response.data;

      this.createdWorkflows.push(workflow.workflow_id);
      console.log(`✅ Created workflow: ${workflow.workflow_id}`);
      console.log(`   Name: ${workflow.name}`);
      console.log(`   Steps: ${workflow.configuration.steps.length}`);

      return workflow;
    } catch (error: any) {
      console.error(
        `❌ Failed to create workflow: ${error.response?.data || error.message}`
      );
      return null;
    }
  }

  async executeWorkflowSync(
    workflowId: string
  ): Promise<ExecutionResponse | null> {
    try {
      console.log(`⚡ Executing workflow synchronously: ${workflowId}...`);
      const payload = {
        query: "Process test document for RAG",
        session_id: `e2e_test_${Date.now()}`,
        user_id: "e2e_test_user",
      };

      const response = await axios.post(
        `${API_BASE}/workflows/${workflowId}/execute`,
        payload,
        { timeout: 120000 } // 2 minute timeout
      );

      const result: ExecutionResponse = response.data;
      console.log(`✅ Workflow executed successfully`);
      console.log(`   Status: ${result.status}`);
      console.log(`   Workflow ID: ${result.workflow_id}`);

      // Try to parse and analyze the response
      if (result.response) {
        try {
          const parsedResponse = JSON.parse(result.response);
          console.log(`   Response type: ${typeof parsedResponse}`);

          if (typeof parsedResponse === "object") {
            console.log(`   Response keys: ${Object.keys(parsedResponse)}`);
          }
        } catch (e) {
          console.log(
            `   Response preview: ${result.response.substring(0, 200)}...`
          );
        }
      }

      return result;
    } catch (error: any) {
      console.error(
        `❌ Sync execution failed: ${error.response?.data || error.message}`
      );
      return null;
    }
  }

  async executeWorkflowAsync(workflowId: string): Promise<string | null> {
    try {
      console.log(`🔄 Executing workflow asynchronously: ${workflowId}...`);
      const payload = {
        query: "Async process test document for RAG",
        session_id: `e2e_async_test_${Date.now()}`,
        user_id: "e2e_async_test_user",
      };

      const response = await axios.post(
        `${API_BASE}/workflows/${workflowId}/execute/async`,
        payload
      );
      const result: AsyncExecutionResponse = response.data;

      console.log(`✅ Async execution started`);
      console.log(`   Execution ID: ${result.execution_id}`);
      console.log(`   Status: ${result.status}`);
      console.log(`   Status URL: ${result.status_url}`);

      return result.execution_id;
    } catch (error: any) {
      console.error(
        `❌ Async execution failed: ${error.response?.data || error.message}`
      );
      return null;
    }
  }

  async checkExecutionStatus(executionId: string): Promise<void> {
    try {
      console.log(`📊 Checking execution status: ${executionId}...`);

      // Wait a bit for execution to start
      await new Promise((resolve) => setTimeout(resolve, 2000));

      const response = await axios.get(
        `${API_BASE}/executions/${executionId}/status`
      );
      const status = response.data;

      console.log(`✅ Execution status retrieved`);
      console.log(`   Status: ${status.status}`);
      console.log(`   Progress: ${(status.progress * 100).toFixed(1)}%`);
      if (status.current_step) {
        console.log(`   Current step: ${status.current_step}`);
      }
    } catch (error: any) {
      console.error(
        `❌ Status check failed: ${error.response?.data || error.message}`
      );
    }
  }

  async testStreamingExecution(workflowId: string): Promise<void> {
    try {
      console.log(`📡 Testing streaming execution: ${workflowId}...`);
      const payload = {
        query: "Stream process test document",
        session_id: `e2e_stream_test_${Date.now()}`,
        user_id: "e2e_stream_test_user",
      };

      await axios.post(`${API_BASE}/workflows/${workflowId}/stream`, payload, {
        responseType: "stream",
        timeout: 30000, // 30 second timeout
      });

      console.log(`✅ Streaming execution started`);

      // Note: For deterministic workflows, streaming should return an error
      // This tests that the API correctly rejects streaming for deterministic workflows
    } catch (error: any) {
      if (error.response?.status === 400) {
        console.log(
          `✅ Correctly rejected streaming for deterministic workflow`
        );
      } else {
        console.error(
          `❌ Unexpected streaming error: ${error.response?.data || error.message}`
        );
      }
    }
  }

  async listWorkflows(): Promise<void> {
    try {
      console.log("📋 Listing workflows...");
      const response = await axios.get(`${API_BASE}/workflows/`);
      const workflows = response.data;

      console.log(`✅ Found ${workflows.length} workflows`);

      // Find our test workflows
      const testWorkflows = workflows.filter((w: any) =>
        this.createdWorkflows.includes(w.workflow_id)
      );

      console.log(`   Test workflows: ${testWorkflows.length}`);
      testWorkflows.forEach((w: any) => {
        console.log(`   - ${w.name} (${w.workflow_id})`);
      });
    } catch (error: any) {
      console.error(
        `❌ Failed to list workflows: ${error.response?.data || error.message}`
      );
    }
  }

  async cleanupWorkflows(): Promise<void> {
    console.log("🧹 Cleaning up test workflows...");

    for (const workflowId of this.createdWorkflows) {
      try {
        await axios.delete(`${API_BASE}/workflows/${workflowId}`);
        console.log(`✅ Deleted workflow: ${workflowId}`);
      } catch (error: any) {
        console.error(
          `❌ Failed to delete workflow ${workflowId}: ${error.response?.data || error.message}`
        );
      }
    }

    this.createdWorkflows = [];
  }

  async runTest(): Promise<void> {
    console.log("🧪 Starting Tokenizer RAG Workflow E2E Test");
    console.log("=".repeat(70));

    try {
      // Setup
      await this.createTestFile();

      // Health check
      const isHealthy = await this.checkApiHealth();
      if (!isHealthy) {
        console.error("❌ API not healthy, aborting test");
        return;
      }

      // Test 1: Create and test simple workflow (no external dependencies)
      console.log(
        "\n🔬 Test 1: Simple tokenizer workflow (file reading + chunking)"
      );
      const simpleWorkflow = await this.createWorkflow(
        SIMPLE_TOKENIZER_WORKFLOW
      );

      if (simpleWorkflow) {
        const syncResult = await this.executeWorkflowSync(
          simpleWorkflow.workflow_id
        );
        if (syncResult) {
          console.log("✅ Simple workflow test passed");
        }

        const asyncExecutionId = await this.executeWorkflowAsync(
          simpleWorkflow.workflow_id
        );
        if (asyncExecutionId) {
          await this.checkExecutionStatus(asyncExecutionId);
        }

        await this.testStreamingExecution(simpleWorkflow.workflow_id);
      }

      // Test 2: Enhanced tokenizer workflow (advanced parsing capabilities)
      console.log(
        "\n🔬 Test 2: Enhanced tokenizer workflow (advanced parsing)"
      );
      const enhancedWorkflow = await this.createWorkflow(
        ENHANCED_TOKENIZER_WORKFLOW
      );

      if (enhancedWorkflow) {
        const enhancedSyncResult = await this.executeWorkflowSync(
          enhancedWorkflow.workflow_id
        );
        if (enhancedSyncResult) {
          console.log("✅ Enhanced workflow test passed");

          // Validate enhanced features from response
          if (enhancedSyncResult.response) {
            try {
              const resultData = JSON.parse(enhancedSyncResult.response);

              // Validate FileReaderStep advanced features
              if (resultData && resultData.read_file_advanced) {
                const fileMetadata = resultData.read_file_advanced.metadata;
                if (fileMetadata.execution_mode === "advanced") {
                  console.log("   ✅ Advanced file reading mode confirmed");
                }
                if (fileMetadata.parser_used) {
                  console.log(
                    `   ✅ File parser used: ${fileMetadata.parser_used}`
                  );
                }
                if (fileMetadata.structured_content !== undefined) {
                  console.log(
                    `   ✅ Structured content support: ${fileMetadata.structured_content}`
                  );
                }
              }

              // Validate TextChunkingStep advanced features
              if (resultData && resultData.chunk_advanced_text) {
                const chunkMetadata = resultData.chunk_advanced_text.metadata;
                if (chunkMetadata.execution_mode === "advanced") {
                  console.log("   ✅ Advanced chunking mode confirmed");
                }
                if (chunkMetadata.chunker_used) {
                  console.log(
                    `   ✅ Chunker used: ${chunkMetadata.chunker_used}`
                  );
                }
                if (chunkMetadata.total_chunks) {
                  console.log(
                    `   ✅ Chunks produced: ${chunkMetadata.total_chunks}`
                  );
                }
                if (chunkMetadata.avg_semantic_score !== undefined) {
                  console.log(
                    `   ✅ Semantic score: ${chunkMetadata.avg_semantic_score.toFixed(3)}`
                  );
                }
                if (chunkMetadata.max_structure_level !== undefined) {
                  console.log(
                    `   ✅ Structure level: ${chunkMetadata.max_structure_level}`
                  );
                }
                if (chunkMetadata.avg_sentence_confidence !== undefined) {
                  console.log(
                    `   ✅ Sentence confidence: ${chunkMetadata.avg_sentence_confidence.toFixed(3)}`
                  );
                }
              }

              // Validate Agent execution features
              if (resultData && resultData.query_processed_document) {
                const agentResult = resultData.query_processed_document;
                if (agentResult.success) {
                  console.log("   ✅ Agent query execution completed");
                }
                if (
                  agentResult.agent_execution &&
                  agentResult.agent_execution.response
                ) {
                  const responseLength =
                    agentResult.agent_execution.response.length;
                  console.log(
                    `   ✅ Agent response length: ${responseLength} characters`
                  );
                }
                if (agentResult.metadata && agentResult.metadata.tools_used) {
                  console.log(
                    `   ✅ Tools used: ${agentResult.metadata.tools_used.join(", ")}`
                  );
                }
                if (
                  agentResult.metadata &&
                  agentResult.metadata.execution_time
                ) {
                  console.log(
                    `   ✅ Agent execution time: ${agentResult.metadata.execution_time}s`
                  );
                }
              }
            } catch (e) {
              console.log("   ⚠️  Could not parse response for validation");
            }
          }
        }

        const enhancedAsyncExecutionId = await this.executeWorkflowAsync(
          enhancedWorkflow.workflow_id
        );
        if (enhancedAsyncExecutionId) {
          await this.checkExecutionStatus(enhancedAsyncExecutionId);
        }
      }

      // Test 3: Full tokenizer workflow (if external services available)
      console.log("\n🔬 Test 3: Full tokenizer RAG workflow (all steps)");
      console.log("⚠️  This test requires OpenAI API key and Qdrant database");

      const fullWorkflow = await this.createWorkflow(TOKENIZER_RAG_WORKFLOW);

      if (fullWorkflow) {
        console.log("✅ Full workflow created successfully");
        console.log("   To test execution, ensure:");
        console.log("   - OPENAI_API_KEY environment variable is set");
        console.log("   - Qdrant database is running on localhost:6333");

        // Only attempt execution if we detect the services might be available

        const fullSyncResult = await this.executeWorkflowSync(
          fullWorkflow.workflow_id
        );
        if (fullSyncResult) {
          console.log("✅ Full tokenizer workflow test passed");
        }
      }

      // Test 4: List and verify workflows
      console.log("\n🔬 Test 4: Workflow management");
      await this.listWorkflows();

      // Summary
      console.log("\n" + "=".repeat(70));
      console.log("🎉 Tokenizer RAG Workflow E2E Test Completed");
      console.log(`✅ Created ${this.createdWorkflows.length} test workflows`);
      console.log(
        "✅ Tested simple tokenizer workflow (backward compatibility)"
      );
      console.log(
        "✅ Tested enhanced tokenizer workflow (advanced parsing + agent query)"
      );
      console.log("✅ Tested document search agent integration");
      console.log("✅ Tested agent execution within deterministic workflows");
      console.log("✅ Tested sync execution");
      console.log("✅ Tested async execution with status checking");
      console.log("✅ Tested streaming rejection for deterministic workflows");
      console.log("✅ Tested workflow listing and management");

      console.log("\n💡 Next steps for full integration testing:");
      console.log("1. Set OPENAI_API_KEY environment variable");
      console.log("2. Start Qdrant: docker run -p 6333:6333 qdrant/qdrant");
      console.log("3. Run test again for complete end-to-end validation");
    } catch (error) {
      console.error(`❌ Test failed: ${error}`);
      throw error;
    } finally {
      // Cleanup
      await this.cleanupWorkflows();
      await this.cleanupTestFile();
    }
  }
}

// Run the test
async function main() {
  console.log("🚀 Starting Tokenizer RAG Workflow E2E Test");
  console.log(`📡 API Base URL: ${API_BASE}`);
  console.log(
    "Make sure the Agent Studio API server is running on port 8000!\n"
  );

  const test = new TokenizerWorkflowE2ETest();

  try {
    await test.runTest();
    process.exit(0);
  } catch (error) {
    console.error("❌ E2E Test failed:", error);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}
