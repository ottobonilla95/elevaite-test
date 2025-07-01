"use server";

import {
  isWorkflowDeployResponse,
  isWorkflowExecutionResponse,
  isWorkflowResponse,
  isWorkflowResponseArray,
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
} from "../interfaces/workflows";
import type { DeploymentOperationResponse } from "../interfaces/common";
import { BACKEND_URL } from "../constants";

export async function getWorkflows(): Promise<WorkflowResponse[]> {
  const url = new URL(`${BACKEND_URL ?? ""}api/workflows/`);
  console.log(url);

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

export async function deployWorkflowModern(
  workflowId: string,
  deploymentRequest: WorkflowDeploymentRequest
): Promise<WorkflowDeployResponse> {
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
    if (isWorkflowDeployResponse(data)) return data;
    throw new Error("Invalid data type - expected workflow deploy response");
  } catch (error) {
    console.error("Error deploying workflow:", error);
    throw error;
  }
}

export async function executeWorkflowModern(
  executionRequest: NewWorkflowExecutionRequest
): Promise<WorkflowExecutionResponse> {
  try {
    const response = await fetch(`${BACKEND_URL}api/workflows/execute`, {
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
