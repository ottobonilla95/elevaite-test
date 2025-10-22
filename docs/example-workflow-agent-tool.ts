/**
 * Example workflow demonstrating agent + tool execution
 * This file shows the complete request objects needed to create agents, tools, and workflows
 */

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

interface AgentCreateRequest {
  name: string;
  description?: string;
  system_prompt_id: string; // UUID
  provider_type: "openai_textgen" | "gemini_textgen" | "bedrock_textgen" | "on-prem_textgen";
  provider_config: {
    model_name?: string;
    temperature?: number;
    max_tokens?: number;
  };
  tags?: string[];
  status?: "active" | "inactive" | "draft";
  organization_id?: string;
  created_by?: string;
}

interface ToolCreateRequest {
  name: string;
  display_name?: string;
  description: string;
  version?: string;
  tool_type: "local" | "remote" | "mcp" | "api";
  execution_type?: "function" | "api" | "command";
  parameters_schema: Record<string, any>;
  return_schema?: Record<string, any>;
  module_path?: string;
  function_name?: string;
  mcp_server_id?: string; // UUID
  remote_name?: string;
  api_endpoint?: string;
  http_method?: "GET" | "POST" | "PUT" | "DELETE";
  headers?: Record<string, string>;
  auth_required?: boolean;
  category_id?: string; // UUID
  tags?: string[];
  documentation?: string;
  examples?: Array<Record<string, any>>;
}

interface AgentToolBindingRequest {
  local_tool_name?: string;
  tool_id?: string; // UUID - use either this or local_tool_name
  is_active?: boolean;
  override_parameters?: Record<string, any>;
}

interface WorkflowCreateRequest {
  name: string;
  description?: string;
  version?: string;
  execution_pattern?: "sequential" | "parallel" | "conditional";
  configuration: {
    steps: Array<{
      step_id: string;
      step_type: "trigger" | "agent" | "tool" | "subflow" | "condition" | "parallel";
      name?: string;
      parameters?: Record<string, any>;
      depends_on?: string[];
    }>;
  };
  global_config?: Record<string, any>;
  tags?: string[];
  timeout_seconds?: number;
  status?: "draft" | "active" | "inactive" | "archived";
  created_by?: string;
  editable?: boolean;
}

interface WorkflowExecuteRequest {
  trigger: {
    kind: "webhook" | "chat" | "file";
    data?: Record<string, any>;
    message?: string;
    files?: Array<{
      filename: string;
      content_type: string;
      size: number;
    }>;
  };
  user_id?: string;
  session_id?: string;
  metadata?: Record<string, any>;
}

// ============================================================================
// STEP 1: CREATE PROMPT (prerequisite for agent)
// ============================================================================

const createPromptRequest = {
  name: "Analysis Agent Prompt",
  content: "You are a helpful AI assistant that analyzes user requests and extracts key information. Be concise and accurate.",
  description: "System prompt for the analysis agent",
  category: "general",
  variables: [],
  tags: ["agent", "analysis"]
};

// Response will include: { id: "prompt-uuid-here", ... }
// Use this ID for system_prompt_id in agent creation

// ============================================================================
// STEP 2: CREATE AGENTS
// ============================================================================

const createAnalysisAgentRequest: AgentCreateRequest = {
  name: "Analysis Agent",
  description: "Analyzes user requests and extracts key information",
  system_prompt_id: "REPLACE_WITH_PROMPT_UUID", // From step 1
  provider_type: "openai_textgen",
  provider_config: {
    model_name: "gpt-4o",
    temperature: 0.7,
    max_tokens: 500
  },
  tags: ["analysis", "extraction"],
  status: "active"
};

const createSummaryAgentRequest: AgentCreateRequest = {
  name: "Summary Agent",
  description: "Summarizes search results and provides concise answers",
  system_prompt_id: "REPLACE_WITH_PROMPT_UUID_2", // Create another prompt for this
  provider_type: "openai_textgen",
  provider_config: {
    model_name: "gpt-4o",
    temperature: 0.5,
    max_tokens: 300
  },
  tags: ["summary", "synthesis"],
  status: "active"
};

// ============================================================================
// STEP 3: CREATE OR REFERENCE TOOLS
// ============================================================================

// Option A: Use existing local tool (like "web_search")
// No creation needed - just reference by name when attaching to agent

// Option B: Create a custom tool in the database
const createCustomToolRequest: ToolCreateRequest = {
  name: "custom_data_processor",
  display_name: "Custom Data Processor",
  description: "Processes and transforms data according to specified rules",
  version: "1.0.0",
  tool_type: "local",
  execution_type: "function",
  parameters_schema: {
    type: "object",
    properties: {
      data: {
        type: "string",
        description: "The data to process"
      },
      operation: {
        type: "string",
        enum: ["uppercase", "lowercase", "reverse"],
        description: "The operation to perform"
      }
    },
    required: ["data", "operation"]
  },
  return_schema: {
    type: "object",
    properties: {
      result: {
        type: "string",
        description: "The processed data"
      }
    }
  },
  module_path: "tools.data_processing",
  function_name: "process_data",
  auth_required: false,
  tags: ["data", "processing", "custom"]
};

// ============================================================================
// STEP 4: ATTACH TOOLS TO AGENTS (Optional)
// ============================================================================

// Attach web_search tool to Analysis Agent
const attachWebSearchToAnalysisAgent: AgentToolBindingRequest = {
  local_tool_name: "web_search",
  is_active: true,
  override_parameters: {}
};

// POST to: /api/agents/{analysis_agent_id}/tools
// Body: attachWebSearchToAnalysisAgent

// ============================================================================
// STEP 5: CREATE WORKFLOW
// ============================================================================

const createWorkflowRequest: WorkflowCreateRequest = {
  name: "Agent + Tool Analysis Workflow",
  description: "Demonstrates agent execution, tool usage, and multi-step processing",
  version: "1.0.0",
  execution_pattern: "sequential",
  configuration: {
    steps: [
      // Step 1: Trigger
      {
        step_id: "trigger_1",
        step_type: "trigger",
        name: "Webhook Trigger",
        parameters: {
          kind: "webhook"
        }
      },
      
      // Step 2: First Agent - Analysis
      {
        step_id: "agent_analysis",
        step_type: "agent",
        name: "Analysis Agent Step",
        parameters: {
          agent_id: "REPLACE_WITH_ANALYSIS_AGENT_UUID", // From step 2
          system_prompt: "You are a helpful AI assistant that analyzes user requests.",
          model: "gpt-4o",
          temperature: 0.7,
          query: "{trigger.data.message}"
        },
        depends_on: ["trigger_1"]
      },
      
      // Step 3: Tool Execution - Web Search
      {
        step_id: "tool_search",
        step_type: "tool",
        name: "Web Search Tool Step",
        parameters: {
          tool_name: "web_search",
          param_mapping: {
            query: "{agent_analysis.response}"
          }
        },
        depends_on: ["agent_analysis"]
      },
      
      // Step 4: Second Agent - Summary
      {
        step_id: "agent_summary",
        step_type: "agent",
        name: "Summary Agent Step",
        parameters: {
          agent_id: "REPLACE_WITH_SUMMARY_AGENT_UUID", // From step 2
          system_prompt: "You are a helpful AI assistant that summarizes information.",
          model: "gpt-4o",
          temperature: 0.5,
          query: "Summarize these search results: {tool_search.result}"
        },
        depends_on: ["tool_search"]
      }
    ]
  },
  tags: ["example", "agent", "tool", "multi-step"],
  timeout_seconds: 300,
  status: "active",
  editable: true
};

// ============================================================================
// STEP 6: EXECUTE WORKFLOW
// ============================================================================

const executeWorkflowRequest: WorkflowExecuteRequest = {
  trigger: {
    kind: "webhook",
    data: {
      message: "What are the latest developments in AI agents?"
    }
  },
  user_id: "user-123",
  session_id: "session-456",
  metadata: {
    source: "api",
    environment: "production"
  }
};

// POST to: /api/workflows/{workflow_id}/execute
// Body: executeWorkflowRequest

// ============================================================================
// EXECUTION FLOW
// ============================================================================

/**
 * Complete execution flow:
 * 
 * 1. POST /api/prompts
 *    Body: createPromptRequest
 *    Response: { id: "prompt-uuid-1", ... }
 * 
 * 2. POST /api/agents
 *    Body: createAnalysisAgentRequest (with prompt-uuid-1)
 *    Response: { id: "agent-uuid-1", ... }
 * 
 * 3. POST /api/agents
 *    Body: createSummaryAgentRequest (with prompt-uuid-2)
 *    Response: { id: "agent-uuid-2", ... }
 * 
 * 4. (Optional) POST /api/agents/{agent-uuid-1}/tools
 *    Body: attachWebSearchToAnalysisAgent
 * 
 * 5. POST /api/workflows
 *    Body: createWorkflowRequest (with agent UUIDs)
 *    Response: { id: "workflow-uuid", ... }
 * 
 * 6. POST /api/workflows/{workflow-uuid}/execute
 *    Body: executeWorkflowRequest
 *    Response: { execution_id: "exec-uuid", status: "running", ... }
 * 
 * 7. GET /api/executions/{exec-uuid}
 *    Poll for completion
 * 
 * 8. GET /api/executions/{exec-uuid}/results
 *    Get final results
 */

export {
  createPromptRequest,
  createAnalysisAgentRequest,
  createSummaryAgentRequest,
  createCustomToolRequest,
  attachWebSearchToAnalysisAgent,
  createWorkflowRequest,
  executeWorkflowRequest
};

