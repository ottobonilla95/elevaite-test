#!/usr/bin/env node
/**
 * E2E Test for Biggest Workflow: Media Planning Command Agent
 *
 * This script tests the complete workflow execution via API calls:
 * - Executes the biggest workflow (Media Planning Command Agent)
 * - Polls for status updates with exponential backoff
 * - Captures full execution trace including step_metadata
 * - Validates analytics tracking and workflow completion
 */

import axios, { AxiosInstance } from "axios";
import * as fs from "fs";

// Configuration
const CONFIG = {
  baseURL: "http://localhost:8005",
  workflowId: "86ee03db-910d-4d27-81a9-59c855d0a06e", // Media Planning Command Agent
  pollInterval: 100, // Start with 100ms
  maxPollInterval: 2000, // Max 2 seconds
  timeout: 600000, // 10 minutes max
  exportResults: true,
};

// Test query for Nike media planning
const TEST_QUERY = `Create a comprehensive media plan for Nike's new Air Max campaign with the following requirements:
- Budget: $60,000 for Q4 2024
- Target audience: Athletes and fitness enthusiasts aged 18-35
- Geographic focus: North America (US and Canada)
- Campaign objectives: Brand awareness and product launch
- Preferred channels: Digital (social media, search) and traditional (TV, radio)
- Timeline: 3-month campaign starting January 2025
- Key messaging: Innovation, performance, and style
- Please include insertion orders for both Salesforce and Google Drive integration
- Generate comprehensive campaign analytics and ROI projections`;

// Types
interface ExecutionResponse {
  execution_id: string;
  workflow_id: string;
  status: string;
  message: string;
}

interface ExecutionStatus {
  execution_id: string;
  status: "pending" | "running" | "completed" | "failed";
  progress: number;
  current_step: string;
  started_at: string;
  completed_at?: string;
  duration_ms?: number;
  result?: any;
  error?: string;
  workflow_trace?: {
    steps: WorkflowStep[];
    execution_path: string[];
  };
}

interface WorkflowStep {
  step_id: string;
  step_type:
    | "agent_execution"
    | "tool_call"
    | "decision_point"
    | "data_processing";
  agent_id?: string;
  agent_name?: string;
  tool_name?: string;
  status: "pending" | "running" | "completed" | "failed" | "skipped";
  input_data?: any;
  output_data?: any;
  error?: string;
  started_at?: string;
  completed_at?: string;
  duration_ms?: number;
  step_metadata?: Record<string, any>;
}

interface TestResult {
  execution_id: string;
  workflow_id: string;
  test_query: string;
  start_time: string;
  end_time: string;
  total_duration_ms: number;
  final_status: string;
  steps_completed: number;
  agents_involved: string[];
  tools_used: string[];
  polling_attempts: number;
  execution_trace: ExecutionStatus[];
  success: boolean;
  error?: string;
}

// API Client
class WorkflowAPIClient {
  private client: AxiosInstance;

  constructor(baseURL: string) {
    this.client = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        "Content-Type": "application/json",
      },
    });
  }

  async executeWorkflow(
    workflowId: string,
    query: string
  ): Promise<ExecutionResponse> {
    const response = await this.client.post(
      `/api/workflows/${workflowId}/execute`,
      {
        query,
        async_execution: true,
      }
    );
    return response.data;
  }

  async getExecutionStatus(executionId: string): Promise<ExecutionStatus> {
    const response = await this.client.get(
      `/api/workflows/executions/${executionId}/status`
    );
    return response.data;
  }

  async getExecutionAnalytics(executionId: string): Promise<any> {
    try {
      const response = await this.client.get(
        `/api/analytics/executions/${executionId}`
      );
      return response.data;
    } catch (error) {
      console.warn("⚠️  Analytics not available yet:", error.message);
      return null;
    }
  }
}

// Console formatting utilities
const colors = {
  reset: "\x1b[0m",
  bright: "\x1b[1m",
  red: "\x1b[31m",
  green: "\x1b[32m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  magenta: "\x1b[35m",
  cyan: "\x1b[36m",
};

function colorize(text: string, color: keyof typeof colors): string {
  return `${colors[color]}${text}${colors.reset}`;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  return `${(ms / 60000).toFixed(1)}m`;
}

function printProgress(status: ExecutionStatus, attempt: number): void {
  const timestamp = new Date().toISOString().split("T")[1].split(".")[0];
  const progressBar =
    "█".repeat(Math.floor(status.progress * 20)) +
    "░".repeat(20 - Math.floor(status.progress * 20));

  console.log(
    `[${colorize(timestamp, "cyan")}] ` +
      `${colorize(`#${attempt.toString().padStart(3, "0")}`, "yellow")} ` +
      `${colorize(status.status.toUpperCase(), status.status === "completed" ? "green" : status.status === "failed" ? "red" : "blue")} ` +
      `[${progressBar}] ${(status.progress * 100).toFixed(1)}% ` +
      `${colorize(status.current_step || "Initializing...", "magenta")}`
  );
}

// Main test execution
async function runWorkflowTest(): Promise<TestResult> {
  const client = new WorkflowAPIClient(CONFIG.baseURL);
  const startTime = new Date();
  const executionTrace: ExecutionStatus[] = [];

  console.log(colorize("\n🚀 Starting E2E Workflow Test", "bright"));
  console.log(colorize("=".repeat(80), "cyan"));
  console.log(`📋 Workflow: Media Planning Command Agent`);
  console.log(`🆔 Workflow ID: ${CONFIG.workflowId}`);
  console.log(`🎯 Test Query: ${TEST_QUERY.substring(0, 100)}...`);
  console.log(colorize("=".repeat(80), "cyan"));

  try {
    // Step 1: Start workflow execution
    console.log(colorize("\n📤 Starting workflow execution...", "blue"));
    const execution = await client.executeWorkflow(
      CONFIG.workflowId,
      TEST_QUERY
    );
    console.log(
      colorize(`✅ Execution started: ${execution.execution_id}`, "green")
    );

    // Step 2: Poll for completion
    console.log(colorize("\n📊 Polling for status updates...", "blue"));
    let pollInterval = CONFIG.pollInterval;
    let attempt = 0;
    let lastStatus: ExecutionStatus;

    while (true) {
      attempt++;

      try {
        const status = await client.getExecutionStatus(execution.execution_id);
        executionTrace.push({ ...status });
        lastStatus = status;

        printProgress(status, attempt);

        // Check if completed
        if (status.status === "completed" || status.status === "failed") {
          break;
        }

        // Check timeout
        if (Date.now() - startTime.getTime() > CONFIG.timeout) {
          throw new Error("Test timeout exceeded");
        }

        // Exponential backoff
        await new Promise((resolve) => setTimeout(resolve, pollInterval));
        pollInterval = Math.min(pollInterval * 1.1, CONFIG.maxPollInterval);
      } catch (pollError) {
        console.error(
          colorize(`❌ Polling error: ${pollError.message}`, "red")
        );
        await new Promise((resolve) => setTimeout(resolve, pollInterval));
      }
    }

    const endTime = new Date();
    const totalDuration = endTime.getTime() - startTime.getTime();

    // Step 3: Get analytics data
    console.log(colorize("\n📈 Fetching analytics data...", "blue"));
    const analytics = await client.getExecutionAnalytics(
      execution.execution_id
    );

    // Step 4: Analyze results
    const finalStatus = lastStatus!;
    const success = finalStatus.status === "completed";

    const stepsCompleted =
      finalStatus.workflow_trace?.steps?.filter((s) => s.status === "completed")
        .length || 0;
    const agentsInvolved = [
      ...new Set(
        finalStatus.workflow_trace?.steps
          ?.map((s) => s.agent_name)
          .filter(Boolean) || []
      ),
    ];
    const toolsUsed = [
      ...new Set(
        finalStatus.workflow_trace?.steps
          ?.map((s) => s.tool_name)
          .filter(Boolean) || []
      ),
    ];

    console.log(colorize("\n📊 Test Results Summary", "bright"));
    console.log(colorize("=".repeat(80), "cyan"));
    console.log(
      `${success ? colorize("✅ SUCCESS", "green") : colorize("❌ FAILED", "red")} - Workflow ${finalStatus.status}`
    );
    console.log(
      `⏱️  Total Duration: ${colorize(formatDuration(totalDuration), "yellow")}`
    );
    console.log(
      `🔄 Polling Attempts: ${colorize(attempt.toString(), "yellow")}`
    );
    console.log(
      `📋 Steps Completed: ${colorize(stepsCompleted.toString(), "yellow")}`
    );
    console.log(
      `🤖 Agents Involved: ${colorize(agentsInvolved.join(", "), "magenta")}`
    );
    console.log(`🔧 Tools Used: ${colorize(toolsUsed.join(", "), "cyan")}`);

    if (finalStatus.workflow_trace?.steps) {
      console.log(colorize("\n🔍 Step Details:", "bright"));
      finalStatus.workflow_trace.steps.forEach((step, i) => {
        const statusIcon =
          step.status === "completed"
            ? "✅"
            : step.status === "failed"
              ? "❌"
              : "⏳";
        const duration = step.duration_ms
          ? ` (${formatDuration(step.duration_ms)})`
          : "";
        console.log(
          `  ${statusIcon} ${step.step_type}: ${step.agent_name || step.tool_name || step.step_id}${duration}`
        );

        if (step.step_metadata && Object.keys(step.step_metadata).length > 0) {
          console.log(
            `     📝 Metadata: ${JSON.stringify(step.step_metadata)}`
          );
        }
      });
    }

    // Create test result
    const testResult: TestResult = {
      execution_id: execution.execution_id,
      workflow_id: CONFIG.workflowId,
      test_query: TEST_QUERY,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      total_duration_ms: totalDuration,
      final_status: finalStatus.status,
      steps_completed: stepsCompleted,
      agents_involved: agentsInvolved,
      tools_used: toolsUsed,
      polling_attempts: attempt,
      execution_trace: executionTrace,
      success,
    };

    // Export results if configured
    if (CONFIG.exportResults) {
      const filename = `workflow-test-${execution.execution_id}-${Date.now()}.json`;
      fs.writeFileSync(filename, JSON.stringify(testResult, null, 2));
      console.log(colorize(`\n💾 Results exported to: ${filename}`, "green"));
    }

    return testResult;
  } catch (error) {
    const endTime = new Date();
    console.error(colorize(`\n❌ Test failed: ${error.message}`, "red"));

    return {
      execution_id: "",
      workflow_id: CONFIG.workflowId,
      test_query: TEST_QUERY,
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      total_duration_ms: endTime.getTime() - startTime.getTime(),
      final_status: "failed",
      steps_completed: 0,
      agents_involved: [],
      tools_used: [],
      polling_attempts: 0,
      execution_trace: [],
      success: false,
      error: error.message,
    };
  }
}

// Run the test
if (require.main === module) {
  runWorkflowTest()
    .then((result) => {
      console.log(colorize("\n🎯 Test completed!", "bright"));
      process.exit(result.success ? 0 : 1);
    })
    .catch((error) => {
      console.error(colorize(`\n💥 Unexpected error: ${error.message}`, "red"));
      process.exit(1);
    });
}

export { runWorkflowTest, WorkflowAPIClient };
