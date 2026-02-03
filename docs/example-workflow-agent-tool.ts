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

// ============================================================================
// INLINE TOOL DEFINITION TYPES
// ============================================================================

/**
 * Code execution tool configuration (Code Interpreter).
 * Enables the agent to write and execute its own Python code at runtime.
 *
 * Note: This is different from UserFunctionDefinition where the USER provides
 * the code upfront. Here, the AGENT writes the code dynamically.
 */
interface CodeExecutionToolConfig {
  type: "code_execution";
  timeout_seconds?: number; // Execution timeout (1-60s, default: 30)
  memory_mb?: number; // Memory limit (64-512MB, default: 256)
}

/**
 * User-provided function definition for inline execution.
 * The function code runs in a sandboxed environment via the Code Execution Service.
 *
 * Note: This is different from CodeExecutionToolConfig where the AGENT writes
 * the code. Here, the USER provides the code upfront.
 */
interface UserFunctionDefinition {
  type: "user_function";
  name: string; // Function name (must match the `def` in code)
  description: string; // What the function does (shown to LLM)
  parameters_schema: Record<string, any>; // JSON Schema for function parameters
  code: string; // Python function implementation
  timeout_seconds?: number; // Execution timeout (1-60s, default: 30)
  memory_mb?: number; // Memory limit (64-512MB, default: 256)
}

/**
 * User location for web search (optional geo-targeting).
 */
interface WebSearchUserLocation {
  country?: string; // ISO 3166-1 alpha-2 country code (e.g., "US", "GB")
  region?: string; // Region/state code
  city?: string; // City name
}

/**
 * Web search tool configuration.
 * Configures the built-in web search capabilities.
 *
 * Provider Support:
 * - OpenAI: search_context_size ✓, user_location ✓
 * - Gemini: Uses GoogleSearch (no config options, will log warning if provided)
 */
interface WebSearchToolConfig {
  type: "web_search";
  search_context_size?: "low" | "medium" | "high"; // OpenAI only (default: "medium")
  user_location?: WebSearchUserLocation; // OpenAI only - geo-targeted results
  allowed_domains?: string[]; // Reserved for future use
  blocked_domains?: string[]; // Reserved for future use
}

/**
 * Union type for all inline tool definitions.
 * Use this when attaching tools to agents without referencing the tool registry.
 *
 * The 'type' field discriminates between:
 * - 'user_function': User provides code upfront
 * - 'web_search': Web search with optional config
 * - 'code_execution': Agent writes code at runtime (Code Interpreter)
 */
type InlineToolDefinition =
  | UserFunctionDefinition
  | WebSearchToolConfig
  | CodeExecutionToolConfig;

// ============================================================================
// AGENT TOOL BINDING
// ============================================================================

/**
 * Request to attach a tool to an agent.
 *
 * Exactly ONE of the following must be provided:
 * - tool_id: Reference a tool by its database UUID
 * - local_tool_name: Reference a local tool by name (syncs to DB if needed)
 * - inline_definition: Provide full tool definition inline (for user functions or web search config)
 */
interface AgentToolBindingRequest {
  tool_id?: string; // UUID - reference existing tool in database
  local_tool_name?: string; // Reference local tool by name
  inline_definition?: InlineToolDefinition; // Provide full tool definition inline
  is_active?: boolean; // Whether this binding is enabled (default: true)
  override_parameters?: Record<string, any>; // Tool-specific parameter overrides
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

// Option A: Attach existing local tool by name
const attachWebSearchToAnalysisAgent: AgentToolBindingRequest = {
  local_tool_name: "web_search",
  is_active: true,
  override_parameters: {}
};

// Option B: Attach web search with custom configuration (inline definition)
const attachWebSearchWithConfig: AgentToolBindingRequest = {
  inline_definition: {
    type: "web_search",
    search_context_size: "high",
    user_location: {
      country: "US",
      region: "CA",
      city: "San Francisco"
    },
    allowed_domains: ["docs.python.org", "stackoverflow.com", "github.com"],
    blocked_domains: ["pinterest.com"]
  },
  is_active: true
};

// Option C: Attach user-defined function (inline definition)
const attachUserFunction: AgentToolBindingRequest = {
  inline_definition: {
    type: "user_function",
    name: "calculate_discount",
    description: "Calculate the discounted price for a product given the original price and discount percentage",
    parameters_schema: {
      type: "object",
      properties: {
        price: {
          type: "number",
          description: "The original price of the product"
        },
        discount_percent: {
          type: "number",
          description: "The discount percentage (0-100)"
        }
      },
      required: ["price", "discount_percent"]
    },
    code: `def calculate_discount(price: float, discount_percent: float) -> dict:
    """Calculate discounted price."""
    if discount_percent < 0 or discount_percent > 100:
        return {"error": "Discount must be between 0 and 100"}
    discounted_price = price * (1 - discount_percent / 100)
    savings = price - discounted_price
    return {
        "original_price": price,
        "discount_percent": discount_percent,
        "discounted_price": round(discounted_price, 2),
        "savings": round(savings, 2)
    }`,
    timeout_seconds: 10,
    memory_mb: 128
  },
  is_active: true
};

// Option D: Attach code execution tool (Code Interpreter - agent writes code)
const attachCodeExecution: AgentToolBindingRequest = {
  inline_definition: {
    type: "code_execution",
    timeout_seconds: 30,
    memory_mb: 256
  },
  is_active: true
};

// POST to: /api/agents/{analysis_agent_id}/tools
// Body: attachWebSearchToAnalysisAgent, attachWebSearchWithConfig, attachUserFunction, or attachCodeExecution

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
  attachWebSearchWithConfig,
  attachUserFunction,
  attachCodeExecution,
  createWorkflowRequest,
  executeWorkflowRequest
};

export type {
  AgentCreateRequest,
  ToolCreateRequest,
  AgentToolBindingRequest,
  UserFunctionDefinition,
  WebSearchToolConfig,
  WebSearchUserLocation,
  CodeExecutionToolConfig,
  InlineToolDefinition,
  WorkflowCreateRequest,
  WorkflowExecuteRequest
};

