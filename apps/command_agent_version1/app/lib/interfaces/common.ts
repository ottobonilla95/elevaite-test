export interface ChatCompletionToolParam {
  type: "function";
  function: {
    name: string;
    description?: string;
    parameters?: Record<string, any>;
  };
}

export interface AgentFunction {
  function: {
    name: string;
  };
}

export interface DeploymentOperationResponse {
  status: "success" | "error";
  message: string;
  deployment_name?: string;
  operation?: string;
}
