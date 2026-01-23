import type { Edge, Node } from "@xyflow/react";
import { getModelById } from "../../../components/ui/ModelSelection";
import {
  AgentNodeId,
  CategoryId,
  ExternalAgentNodeId,
  TriggerNodeId,
  InputNodeId,
  OutputNodeId,
  ActionNodeId,
  LogicNodeId,
  PromptNodeId,
} from "../../enums";
import type { SidePanelPayload } from "../../interfaces";
import type { StepConfig, StepConnection, StepType, WorkflowConfig } from "../../model/workflowSteps";


/**
 * Personality prompt prefixes that get prepended to agent instructions
 */
const personalityPrompts: Record<string, string> = {
  professional: "You are a professional assistant. Respond formally, be concise, use proper business language, and maintain a respectful tone.",
  friendly: "You are a friendly, approachable assistant. Use a warm and conversational tone, be encouraging, and feel free to use casual language.",
  creative: "You are a creative assistant. Think outside the box, offer imaginative solutions, use vivid language, and don't be afraid to suggest unconventional ideas.",
  analytical: "You are an analytical assistant. Be precise, use data-driven reasoning, break down complex problems systematically, and provide thorough explanations.",
  casual: "You are a casual assistant. Keep things relaxed and informal, use everyday language, and feel free to be playful in your responses.",
};


/**
 * Maps a canvas node ID (e.g., "agents_chatbot") to a backend step type
 */
function nodeIdToStepType(nodeId: string): StepType {
  // Agents → agent_execution
  if (Object.values(AgentNodeId).includes(nodeId as AgentNodeId)) {
    return "agent_execution";
  }

  // External Agents → agent_execution (A2A)
  if (Object.values(ExternalAgentNodeId).includes(nodeId as ExternalAgentNodeId)) {
    return "agent_execution";
  }

  // Prompts → prompt step
  if (Object.values(PromptNodeId).includes(nodeId as PromptNodeId)) {
    return "prompt";
  }

  // Triggers
  if (Object.values(TriggerNodeId).includes(nodeId as TriggerNodeId)) {
    return "trigger";
  }

  // Inputs
  if (Object.values(InputNodeId).includes(nodeId as InputNodeId)) {
    return "input";
  }

  // Outputs
  if (Object.values(OutputNodeId).includes(nodeId as OutputNodeId)) {
    return "output";
  }

  // Actions → tool_execution
  if (Object.values(ActionNodeId).includes(nodeId as ActionNodeId)) {
    return "tool_execution";
  }

  // Logic
  if (Object.values(LogicNodeId).includes(nodeId as LogicNodeId)) {
    return "conditional";
  }

  // Default fallback
  return "agent_execution";
}

/**
 * Extracts the sub-type from a node ID (e.g., "agents_chatbot" → "chatbot")
 */
function extractSubType(nodeId: string): string {
  const parts = nodeId.split("_");
  return parts.length > 1 ? parts.slice(1).join("_") : nodeId;
}

/**
 * Converts a single canvas node to a workflow step config
 */
function nodeToStepConfig(node: Node, stepOrder: number, dependencies: string[]): StepConfig {
  const payload = node.data as SidePanelPayload;
  const stepType = nodeIdToStepType(payload.id);
  const subType = extractSubType(payload.id);

  const baseStep = {
    step_id: node.id,
    step_type: stepType,
    step_name: payload.label,
    step_order: stepOrder,
    dependencies: [] as string[],
  };

  // Build config based on step type and category
  const categoryId = payload.nodeDetails?.categoryId;
  const itemDetails = payload.nodeDetails?.itemDetails ?? {};

  switch (stepType) {
    case "trigger":
      return {
        ...baseStep,
        step_type: "trigger",
        parameters: {
          kind: subType === "webhook" ? "webhook" : subType === "scheduler" ? "schedule" : "manual",
          ...itemDetails,
        },
      };

    case "prompt": {
      const { model, text, temperature, maxTokens, ...restDetails } = itemDetails as {
        model?: string;
        text?: string;
        temperature?: number;
        maxTokens?: number;
        [key: string]: unknown;
      };
      const modelInfo = model ? getModelById(model) : undefined;

      // Extract {{variable}} placeholders from the prompt text
      const variablePattern = /\{\{(?<varName>\s*[\w.]+\s*)\}\}/g;
      const extractedVars: string[] = [];
      if (text) {
        let match: RegExpExecArray | null;
        while ((match = variablePattern.exec(text)) !== null) {
          extractedVars.push(match[1].trim());
        }
      }

      // Build variables array: map each extracted variable to a dependency source
      // If we have dependencies, try to map variables to them
      const variables: { name: string; source?: string; default_value?: string }[] = [];
      for (const varName of extractedVars) {
        // Check if varName contains a dot (already a path like "input-node.text")
        if (varName.includes(".")) {
          variables.push({ name: varName.split(".").pop() ?? varName, source: varName });
        } else if (dependencies.length > 0) {
          // Map to first dependency's output (e.g., "node_xxx.text")
          variables.push({ name: varName, source: `${dependencies[0]}.text` });
        } else {
          // No source, just define the variable
          variables.push({ name: varName });
        }
      }

      return {
        ...baseStep,
        step_type: "prompt",
        parameters: {
          system_prompt: text,
          query_template: undefined,
          variables,
          override_agent_prompt: true,
          ...restDetails,
          model_name: modelInfo?.id ?? model,
          provider: modelInfo?.provider ?? "openai_textgen",
          temperature: temperature ?? 0.5,
          max_tokens: maxTokens,
        },
      };
    }

    case "agent_execution": {
      const { model, personality, agentInstructions, ...restDetails } = itemDetails as {
        model?: string;
        personality?: string;
        agentInstructions?: string;
        [key: string]: unknown;
      };
      const modelInfo = model ? getModelById(model) : undefined;
      // Prepend personality prompt to agent instructions if personality is set
      const personalityPrefix = personality ? personalityPrompts[personality] : undefined;
      const systemPrompt = personalityPrefix && agentInstructions
        ? `${personalityPrefix}\n\n${agentInstructions}`
        : personalityPrefix || agentInstructions;
      return {
        ...baseStep,
        step_type: "agent_execution",
        config: {
          agent_name: payload.label,
          // Store agent type info in a2a_agent_id for external agents
          a2a_agent_id: categoryId === CategoryId.EXTERNAL_AGENTS ? subType : undefined,
          ...restDetails,
          system_prompt: systemPrompt,
          model_name: modelInfo?.id ?? model,
          provider: modelInfo?.provider ?? "openai_textgen",
          interactive: false,
          force_real_llm: true,
        },
      };
    }

    case "tool_execution":
      return {
        ...baseStep,
        step_type: "tool_execution",
        config: {
          tool_name: payload.label,
          tool_id: subType,
          ...itemDetails,
        },
      };

    case "input":
      return {
        ...baseStep,
        step_type: "input",
        config: {
          input_type: subType, // text, audio, file, url, image
          ...itemDetails,
        },
      };

    case "output":
      return {
        ...baseStep,
        step_type: "output",
        config: {
          output_type: subType, // text, audio, template, image
          ...itemDetails,
        },
      };

    case "conditional":
      return {
        ...baseStep,
        step_type: "conditional",
        config: {
          condition: typeof itemDetails.condition === "string"
            ? itemDetails.condition
            : `${subType}_condition`,
        },
      };

    default:
      return {
        ...baseStep,
        step_type: stepType,
        config: {
          ...itemDetails,
        },
      } as StepConfig;
  }
}

/**
 * Converts React Flow edges to workflow step connections
 */
function edgesToConnections(edges: Edge[]): StepConnection[] {
  return edges.map((edge) => ({
    source_step_id: edge.source,
    target_step_id: edge.target,
    source_handle: edge.sourceHandle ?? undefined,
    target_handle: edge.targetHandle ?? undefined,
    label: typeof edge.label === "string" ? edge.label : undefined,
    animated: edge.animated ?? false,
  }));
}

/**
 * Computes step dependencies from edges
 * A step depends on all steps that have edges pointing to it
 */
function computeDependencies(edges: Edge[]): Map<string, string[]> {
  const deps = new Map<string, string[]>();

  for (const edge of edges) {
    const existing = deps.get(edge.target) ?? [];
    existing.push(edge.source);
    deps.set(edge.target, existing);
  }

  return deps;
}

export interface CanvasToWorkflowOptions {
  workflowId?: string;
  workflowName: string;
  description?: string;
  version?: string;
  tags?: string[];
}

/**
 * Main converter: transforms canvas nodes/edges into a WorkflowConfig
 */
export function canvasToWorkflowConfig(
  nodes: Node[],
  edges: Edge[],
  options: CanvasToWorkflowOptions
): WorkflowConfig {
  // Compute dependencies from edges
  const dependencyMap = computeDependencies(edges);

  // Convert nodes to steps
  const steps: StepConfig[] = nodes.map((node, index) => {
    const deps = dependencyMap.get(node.id) ?? [];
    const step = nodeToStepConfig(node, index + 1, deps);
    // Attach dependencies
    step.dependencies = deps;
    return step;
  });

  // Convert edges to connections
  const connections = edgesToConnections(edges);

  return {
    id: options.workflowId,
    name: options.workflowName,
    description: options.description,
    version: options.version ?? "1.0.0",
    steps,
    connections,
    tags: options.tags ?? [],
  };
}
