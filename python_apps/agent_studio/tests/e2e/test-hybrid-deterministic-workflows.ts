#!/usr/bin/env tsx

/**
 * Comprehensive E2E Test for Hybrid and Deterministic Workflows
 *
 * Tests all three workflow execution endpoints:
 * - POST /api/workflows/{id}/execute (sync)
 * - POST /api/workflows/{id}/execute/async (async)
 * - POST /api/workflows/{id}/stream (streaming)
 *
 * With both workflow types:
 * - Pure deterministic workflows
 * - Hybrid workflows with conditional routing
 */

import axios from "axios";
import { writeFileSync } from "fs";

const BASE_URL = "http://localhost:8005";
const API_BASE = `${BASE_URL}/api`;

interface WorkflowResponse {
  workflow_id: string;
  name: string;
  description: string;
  version: string;
  configuration: any;
  created_by: string;
  is_deployed: boolean;
}

interface ExecutionResponse {
  execution_id: string;
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

// Test workflow configurations
const DETERMINISTIC_WORKFLOW = {
  name: "E2E Test Deterministic Workflow",
  description: "Pure deterministic workflow for endpoint testing",
  version: "1.0.0",
  configuration: {
    workflow_type: "deterministic",
    workflow_name: "E2E Audit Pipeline",
    execution_pattern: "sequential",
    steps: [
      {
        step_id: "input_validation",
        step_type: "data_input",
        step_name: "Validate Input",
        config: {
          validation_rules: ["required_fields"],
          audit_level: "basic",
        },
      },
      {
        step_id: "process_request",
        step_type: "data_processing",
        step_name: "Process Request",
        config: {
          processing_mode: "test",
          output_format: "json",
        },
      },
      {
        step_id: "generate_output",
        step_type: "data_output",
        step_name: "Generate Output",
        config: {
          output_destination: "response",
          include_metadata: true,
        },
      },
    ],
  },
  created_by: "e2e_test",
};

const HYBRID_WORKFLOW = {
  name: "E2E Test Hybrid Workflow",
  description: "Hybrid workflow with conditional routing for endpoint testing",
  version: "1.0.0",
  configuration: {
    workflow_type: "hybrid",
    agents: [
      {
        agent_id: "tokenizer_agent",
        agent_type: "DeterministicWorkflowAgent",
        name: "Document Processor",
        config: {
          workflow_type: "deterministic",
          workflow_name: "Document Processing",
          execution_pattern: "sequential",
          steps: [
            {
              step_id: "file_processing",
              step_type: "data_processing",
              step_name: "Process File",
              config: {
                chunk_size: 500,
                overlap: 100,
              },
            },
          ],
        },
      },
      {
        agent_id: "router_agent",
        agent_type: "CommandAgent",
        name: "Query Router",
        config: {
          system_prompt: "Route queries based on context",
          tools: ["search", "analyze"],
        },
      },
    ],
    connections: [
      {
        source_agent_id: "tokenizer_agent",
        target_agent_id: "router_agent",
        connection_type: "conditional",
      },
    ],
    execution_logic: {
      routing_rules: [
        {
          condition: "input.has_file",
          action: "execute_tokenizer_then_router",
          flow: ["tokenizer_agent", "router_agent"],
          description: "Process file then route query",
        },
        {
          condition: "!input.has_file",
          action: "execute_router_directly",
          flow: ["router_agent"],
          description: "Route query directly",
        },
      ],
      default_action: "execute_router_directly",
    },
  },
  created_by: "e2e_test",
};

class WorkflowTester {
  private deterministicWorkflowId: string = "";
  private hybridWorkflowId: string = "";

  async createTestWorkflows(): Promise<void> {
    console.log("📋 Creating test workflows via API...");

    try {
      // Create deterministic workflow
      console.log("   Creating deterministic workflow...");
      const detResponse = await axios.post<WorkflowResponse>(
        `${API_BASE}/workflows`,
        DETERMINISTIC_WORKFLOW
      );
      this.deterministicWorkflowId = detResponse.data.workflow_id;
      console.log(
        `   ✅ Deterministic workflow: ${this.deterministicWorkflowId}`
      );

      // Create hybrid workflow
      console.log("   Creating hybrid workflow...");
      const hybridResponse = await axios.post<WorkflowResponse>(
        `${API_BASE}/workflows`,
        HYBRID_WORKFLOW
      );
      this.hybridWorkflowId = hybridResponse.data.workflow_id;
      console.log(`   ✅ Hybrid workflow: ${this.hybridWorkflowId}`);
    } catch (error: any) {
      if (
        (error.response?.status === 400 || error.response?.status === 500) &&
        error.response?.data?.detail?.includes("already exists")
      ) {
        console.log(
          "   ℹ️  Workflows already exist, fetching existing ones..."
        );
        await this.findExistingWorkflows();
      } else {
        throw error;
      }
    }
  }

  async findExistingWorkflows(): Promise<void> {
    // Get all workflows and find our test ones
    const response = await axios.get(`${API_BASE}/workflows`);
    const workflows = response.data;

    const detWorkflow = workflows.find(
      (w: any) => w.name === DETERMINISTIC_WORKFLOW.name
    );
    const hybridWorkflow = workflows.find(
      (w: any) => w.name === HYBRID_WORKFLOW.name
    );

    if (detWorkflow) {
      this.deterministicWorkflowId = detWorkflow.workflow_id;
      console.log(
        `   ✅ Found deterministic workflow: ${this.deterministicWorkflowId}`
      );
    }

    if (hybridWorkflow) {
      this.hybridWorkflowId = hybridWorkflow.workflow_id;
      console.log(`   ✅ Found hybrid workflow: ${this.hybridWorkflowId}`);
    }
  }

  async testSyncExecution(): Promise<void> {
    console.log("\n🔄 Testing Synchronous Execution...");

    const testQuery = "Test query for synchronous execution";
    const executionRequest = {
      query: testQuery,
      user_id: "e2e_test_user",
      session_id: "e2e_test_session",
    };

    // Test deterministic workflow
    console.log("   Testing deterministic workflow (sync)...");
    try {
      const response = await axios.post<ExecutionResponse>(
        `${API_BASE}/workflows/${this.deterministicWorkflowId}/execute`,
        executionRequest
      );
      console.log(`   ✅ Deterministic sync: ${response.data.status}`);
    } catch (error: any) {
      console.log(
        `   ❌ Deterministic sync failed: ${error.response?.data?.detail || error.message}`
      );
    }

    // Test hybrid workflow
    console.log("   Testing hybrid workflow (sync)...");
    try {
      const response = await axios.post<ExecutionResponse>(
        `${API_BASE}/workflows/${this.hybridWorkflowId}/execute`,
        executionRequest
      );
      console.log(`   ✅ Hybrid sync: ${response.data.status}`);
    } catch (error: any) {
      console.log(
        `   ❌ Hybrid sync failed: ${error.response?.data?.detail || error.message}`
      );
    }
  }

  async testAsyncExecution(): Promise<void> {
    console.log("\n⏳ Testing Asynchronous Execution...");

    const testQuery = "Test query for asynchronous execution";
    const executionRequest = {
      query: testQuery,
      user_id: "e2e_test_user",
      session_id: "e2e_test_session",
    };

    // Test deterministic workflow
    console.log("   Testing deterministic workflow (async)...");
    try {
      const response = await axios.post<AsyncExecutionResponse>(
        `${API_BASE}/workflows/${this.deterministicWorkflowId}/execute/async`,
        executionRequest
      );
      console.log(
        `   ✅ Deterministic async: ${response.data.status} (${response.data.execution_id})`
      );
    } catch (error: any) {
      console.log(
        `   ❌ Deterministic async failed: ${error.response?.data?.detail || error.message}`
      );
    }

    // Test hybrid workflow
    console.log("   Testing hybrid workflow (async)...");
    try {
      const response = await axios.post<AsyncExecutionResponse>(
        `${API_BASE}/workflows/${this.hybridWorkflowId}/execute/async`,
        executionRequest
      );
      console.log(
        `   ✅ Hybrid async: ${response.data.status} (${response.data.execution_id})`
      );
    } catch (error: any) {
      console.log(
        `   ❌ Hybrid async failed: ${error.response?.data?.detail || error.message}`
      );
    }
  }

  async testStreamingExecution(): Promise<void> {
    console.log("\n🌊 Testing Streaming Execution...");

    const testQuery = "Test query for streaming execution";
    const executionRequest = {
      query: testQuery,
      user_id: "e2e_test_user",
      session_id: "e2e_test_session",
    };

    // Test deterministic workflow (should return error)
    console.log("   Testing deterministic workflow (streaming)...");
    try {
      const response = await axios.post(
        `${API_BASE}/workflows/${this.deterministicWorkflowId}/stream`,
        executionRequest,
        { responseType: "stream" }
      );
      console.log(
        `   ⚠️  Deterministic streaming: Should have returned error but didn't`
      );
    } catch (error: any) {
      console.log(
        `   ✅ Deterministic streaming correctly rejected: ${error.response?.status}`
      );
    }

    // Test hybrid workflow (should succeed with streaming)
    console.log("   Testing hybrid workflow (streaming)...");
    try {
      const response = await axios.post(
        `${API_BASE}/workflows/${this.hybridWorkflowId}/stream`,
        executionRequest,
        { responseType: "stream" }
      );
      console.log(`   ✅ Hybrid streaming accepted: ${response.status}`);
    } catch (error: any) {
      console.log(
        `   ⚠️  Hybrid streaming failed: ${error.response?.status} - ${error.response?.data?.detail || error.message}`
      );
    }
  }

  async runAllTests(): Promise<void> {
    console.log("🚀 Starting Comprehensive Workflow Endpoint Tests");
    console.log("=".repeat(80));

    try {
      await this.createTestWorkflows();
      await this.testSyncExecution();
      await this.testAsyncExecution();
      await this.testStreamingExecution();

      console.log("\n🎉 All tests completed!");
      console.log("=".repeat(80));
    } catch (error: any) {
      console.error("❌ Test suite failed:", error.message);
      if (error.response) {
        console.error("Response:", error.response.data);
      }
      process.exit(1);
    }
  }
}

// Run the tests
const tester = new WorkflowTester();
tester.runAllTests();
