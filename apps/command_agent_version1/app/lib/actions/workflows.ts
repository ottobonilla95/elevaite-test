"use server";

import {
  isWorkflowDeployResponse,
  isWorkflowExecutionResponse,
  isWorkflowResponse,
  isWorkflowResponseArray,
  isWorkflowDeployment,
} from "../discriminators/workflows";
import { isDeploymentOperationResponse } from "../discriminators/common";
import type {
  WorkflowDeployRequest,
  WorkflowDeployResponse,
  WorkflowExecutionRequest,
  WorkflowExecutionResponse,
  WorkflowResponse,
  WorkflowCreateRequest,
  WorkflowDeploymentRequest,
  NewWorkflowExecutionRequest,
  WorkflowDeployment,
  WorkflowExecuteResponseObject,
} from "../interfaces/workflows";
import type { DeploymentOperationResponse } from "../interfaces/common";
import { BACKEND_URL } from "../constants";

export async function getWorkflows(): Promise<WorkflowResponse[]> {
  const url = new URL(`${BACKEND_URL ?? ""}api/workflows/`);

  const response = await fetch(url);
  if (!response.ok) throw new Error("Failed to fetch workflows");

  const data: unknown = await response.json();
  if (isWorkflowResponseArray(data)) return data;
  throw new Error("Invalid data type - expected array of workflows");
}

export async function deployWorkflow(
  workflowRequest: WorkflowDeployRequest
): Promise<WorkflowDeployResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}deploy`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(workflowRequest),
  });

  if (!response.ok) throw new Error("Failed to deploy workflow");

  const data: unknown = await response.json();
  if (isWorkflowDeployResponse(data)) return data;
  throw new Error("Invalid data type - expected workflow deploy response");
}

export async function executeWorkflow(
  executionRequest: WorkflowExecutionRequest
): Promise<WorkflowExecutionResponse> {
  const url = new URL(`${BACKEND_URL ?? ""}run`);

  const response = await fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query: executionRequest.query,
      uid: executionRequest.uid,
      sid: executionRequest.sid,
      collection: executionRequest.collection,
    }),
  });

  if (!response.ok) throw new Error("Failed to execute workflow");

  const data: unknown = await response.json();
  if (isWorkflowExecutionResponse(data)) return data;
  throw new Error("Invalid data type - expected workflow execution response");
}

export async function getWorkflowDetails(
  workflowId: string
): Promise<WorkflowResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/${workflowId}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: unknown = await response.json();
    if (isWorkflowResponse(data)) return data;
    throw new Error("Invalid data type - expected workflow response");
  } catch (error) {
    console.error("Error fetching workflow details:", error);
    throw error;
  }
}

export async function deleteWorkflow(workflowId: string): Promise<void> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/${workflowId}`, {
      method: "DELETE",
    });
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
  } catch (error) {
    console.error("Error deleting workflow:", error);
    throw error;
  }
}

export async function createWorkflow(
  workflowRequest: WorkflowCreateRequest
): Promise<WorkflowResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(workflowRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: unknown = await response.json();
    if (isWorkflowResponse(data)) return data;
    throw new Error("Invalid data type - expected workflow response");
  } catch (error) {
    console.error("Error creating workflow:", error);
    throw error;
  }
}

export async function updateWorkflow(
  workflowId: string,
  workflowRequest: WorkflowCreateRequest
): Promise<WorkflowResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/${workflowId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(workflowRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: unknown = await response.json();
    if (isWorkflowResponse(data)) return data;
    throw new Error("Invalid data type - expected workflow response");
  } catch (error) {
    console.error("Error updating workflow:", error);
    throw error;
  }
}

export async function deployWorkflowModern(
  workflowId: string,
  deploymentRequest: WorkflowDeploymentRequest
): Promise<WorkflowDeployment> {
  try {
    const response = await fetch(
      `${BACKEND_URL}api/workflows/${workflowId}/deploy`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(deploymentRequest),
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: unknown = await response.json();
    // The backend returns a WorkflowDeployment object, not WorkflowDeployResponse
    if (isWorkflowDeployment(data)) return data;
    throw new Error("Invalid data type - expected workflow deployment response");
  } catch (error) {
    console.error("Error deploying workflow:", error);
    throw error;
  }
}

export async function executeWorkflowModern(
  workflowId: string,
  executionRequest: NewWorkflowExecutionRequest
): Promise<WorkflowExecutionResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/${workflowId}/execute`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(executionRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: unknown = await response.json();
	if (isWorkflowExecutionResponse(data)) return data;
    throw new Error("Invalid data type - expected workflow execution response");
  } catch (error) {
    console.error("Error executing workflow:", error);
    throw error;
  }
}

export async function executeWorkflowStream(
  workflowId: string,
  executionRequest: NewWorkflowExecutionRequest
): Promise<ReadableStream<Uint8Array> | null> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/${workflowId}/stream`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(executionRequest),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.body;
  } catch (error) {
    console.error("Error executing workflow stream:", error);
    throw error;
  }
}

export async function stopWorkflowDeployment(
  deploymentName: string
): Promise<DeploymentOperationResponse> {
  try {
    const response = await fetch(
      `${BACKEND_URL}api/workflows/deployments/${deploymentName}/stop`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: unknown = await response.json();
    if (isDeploymentOperationResponse(data)) return data;
    throw new Error(
      "Invalid data type - expected deployment operation response"
    );
  } catch (error) {
    console.error("Error stopping workflow deployment:", error);
    throw error;
  }
}

export async function deleteWorkflowDeployment(
  deploymentName: string
): Promise<DeploymentOperationResponse> {
  try {
    const response = await fetch(
      `${BACKEND_URL}api/workflows/deployments/${deploymentName}`,
      {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: unknown = await response.json();
    if (isDeploymentOperationResponse(data)) return data;
    throw new Error(
      "Invalid data type - expected deployment operation response"
    );
  } catch (error) {
    console.error("Error deleting workflow deployment:", error);
    throw error;
  }
}

export async function getActiveDeployments(): Promise<WorkflowDeployment[]> {
  try {
    const response = await fetch(
      `${BACKEND_URL}api/workflows/deployments/active`
    );

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const data: unknown = await response.json();
    if (Array.isArray(data)) return data as WorkflowDeployment[];
    throw new Error("Invalid data type - expected array of deployments");
  } catch (error) {
    console.error("Error fetching active deployments:", error);
    throw error;
  }
}

export async function getWorkflowDeploymentStatus(
  workflowId: string
): Promise<WorkflowDeployment | undefined> {
  try {
    const activeDeployments = await getActiveDeployments();
    const deployment = activeDeployments.find(
      (d) => d.workflow_id === workflowId && d.status === "active"
    );
    return deployment ?? undefined;
  } catch (error) {
    console.error("Error checking workflow deployment status:", error);
    return undefined;
  }
}

export async function isWorkflowDeployed(workflowId: string): Promise<boolean> {
  try {
    const deployment = await getWorkflowDeploymentStatus(workflowId);
    return deployment !== null;
  } catch (error) {
    console.error("Error checking if workflow is deployed:", error);
    return false;
  }
}

export async function getWorkflowDeploymentDetails(
  workflowId: string
): Promise<{
  isDeployed: boolean;
  deployment?: WorkflowDeployment;
  inferenceUrl?: string;
}> {
  try {
    const deployment = await getWorkflowDeploymentStatus(workflowId);
    const isDeployed = deployment !== null;

    let inferenceUrl: string | undefined;
    if (deployment) {
      // Generate inference URL based on workflow ID (webhook-style)
      inferenceUrl = `${BACKEND_URL}api/workflows/${workflowId}/execute`;
    }

    return {
      isDeployed,
      deployment,
      inferenceUrl,
    };
  } catch (error) {
    console.error("Error getting workflow deployment details:", error);
    return { isDeployed: false };
  }
}
