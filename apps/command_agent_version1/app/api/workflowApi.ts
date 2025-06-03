import { executeWorkflowModern } from "../lib/actions";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

export const WorkflowAPI = {
  // Deploy a workflow (save the workflow structure) - DEPRECATED
  deployWorkflow: async (nodes, edges) => {
    // Convert nodes to agents format
    const agents = nodes.map((node) => [
      node.data.type.charAt(0), // First letter as shorthand (r for router)
      node.id,
    ]);

    // Convert edges to connections format
    const connections = edges.map(
      (edge) =>
        `${nodes.find((n) => n.id === edge.source)?.data.type.charAt(0)}->${nodes
          .find((n) => n.id === edge.target)
          ?.data.type.charAt(0)}`
    );

    // Create the payload
    const payload = {
      agents: agents,
      connections: connections,
    };

    console.log("Sending deploy payload:", payload);

    const response = await fetch(`${API_BASE_URL}/deploy`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    });

    if (!response.ok) {
      throw new Error("Failed to deploy workflow");
    }

    return response.json();
  },

  // Run a query through the workflow using modern API
  runWorkflow: async (
    workflowId: string,
    query: string,
    chatHistory: Array<{ actor: string; content: string }> = []
  ) => {
    try {
      const executionRequest = {
        workflow_id: workflowId,
        query: query,
        chat_history: chatHistory,
        runtime_overrides: {},
      };

      console.log("Executing workflow with modern API:", executionRequest);

      const result = await executeWorkflowModern(executionRequest);
      return result;
    } catch (error) {
      console.error("Error executing workflow:", error);
      throw error;
    }
  },

  // Stream execution using modern API
  runWorkflowStream: async (
    workflowId: string,
    query: string,
    chatHistory: Array<{ actor: string; content: string }> = []
  ) => {
    try {
      const executionRequest = {
        workflow_id: workflowId,
        query: query,
        chat_history: chatHistory,
        runtime_overrides: {},
      };

      console.log("Streaming workflow execution:", executionRequest);

      const response = await fetch(
        `${API_BASE_URL}/api/workflows/execute/stream`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(executionRequest),
        }
      );

      if (!response.ok) {
        throw new Error(`Failed to execute workflow: ${response.status}`);
      }

      return response.body?.getReader();
    } catch (error) {
      console.error("Error streaming workflow execution:", error);
      throw error;
    }
  },

  // Execute workflow by deployment name
  runWorkflowByDeployment: async (
    deploymentName: string,
    query: string,
    chatHistory: Array<{ actor: string; content: string }> = []
  ) => {
    try {
      const executionRequest = {
        deployment_name: deploymentName,
        query: query,
        chat_history: chatHistory,
        runtime_overrides: {},
      };

      console.log("Executing workflow by deployment:", executionRequest);

      const result = await executeWorkflowModern(executionRequest);
      return result;
    } catch (error) {
      console.error("Error executing workflow by deployment:", error);
      throw error;
    }
  },
};
