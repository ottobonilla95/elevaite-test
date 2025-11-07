"use client";
import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ReactFlowProvider, type ReactFlowInstance } from "react-flow-renderer";
import { toast } from "react-toastify";
// eslint-disable-next-line import/named -- Seems to be a problem with eslint
import { v4 as uuidv4 } from "uuid";
import { getWorkflowDeploymentDetails } from "../lib/actions";
import { isAgentNodeData, isAgentResponse, isTool } from "../lib/discriminators";
import {
  type ToolParametersSchema, type AgentConfigData, type AgentCreate, type AgentFunction, type AgentNodeData, type AgentResponse,
  type AgentUpdate, type ChatCompletionToolParam, type Edge, type Node, type ToolNodeData,
  type WorkflowAgent, type WorkflowCreateRequest, type WorkflowDeployment, type WorkflowResponse,
  Tool,
} from "../lib/interfaces";
import { mapActionTypeToConnectionType, mapConnectionTypeToActionType } from "../lib/interfaces/workflows";
import { useAgents } from "../ui/contexts/AgentsContext";
import { usePrompts } from "../ui/contexts/PromptsContext.tsx";
import { useTools } from "../ui/contexts/ToolsContext.tsx";
import { useWorkflows } from "../ui/contexts/WorkflowsContext";
import "./AgentConfigForm.scss";
import AgentConfigModal from "./agents/AgentConfigModal";
import ChatInterface from "./agents/ChatInterface";
import ChatSidebar from "./agents/ChatSidebar";
import { ToolsConfigPanel } from "./agents/config/ToolsConfigPanel.tsx";
import ConfigPanel, { type ConfigPanelHandle } from "./agents/ConfigPanel";
import DesignerCanvas from "./agents/DesignerCanvas";
import DesignerSidebar from "./agents/DesignerSidebar";
import HeaderBottom from "./agents/HeaderBottom.tsx";
import VectorizerBottomDrawer, { type PipelineStep, type VectorizationStepData } from "./agents/VectorizerBottomDrawer";
import VectorizerConfigPanel from "./agents/VectorizerConfigPanel";
import AgentTestingPanel from "./AgentTestingPanel.tsx";
import { getProviderForModel } from "./agents/config/configUtils";



// Helper function to convert ChatCompletionToolParam to AgentFunction
function convertToolsToAgentFunctions(
  tools: ChatCompletionToolParam[]
): AgentFunction[] {
  return tools.map((tool) => ({
    function: {
      name: tool.function.name,
    },
  }));
}

// Helper function to convert AgentConfigData to AgentCreate
function convertConfigToAgentCreate(
  configData: AgentConfigData,
  tools: ChatCompletionToolParam[],
  agentName: string,
  selectedPromptId: string | null
): AgentCreate {
  // Validate required fields
  if (!selectedPromptId) {
    throw new Error("A prompt must be selected to create an agent");
  }

  // Map output format to response_type with exact case matching
  const getResponseType = (
    outputFormat?: string
  ): "json" | "yaml" | "markdown" | "HTML" | "None" => {
    if (!outputFormat) return "json";

    const format = outputFormat.toLowerCase();
    switch (format) {
      case "json": return "json";
      case "yaml": return "yaml";
      case "markdown": return "markdown";
      case "html": return "HTML";
      case "none": return "None";
      case "text": return "None";
      default: return "json";
    }
  };

  // Build provider_config with model settings
  const providerConfig: Record<string, unknown> = {
    model_name: configData.model || "gpt-4o",
    temperature: 0.7,
    max_tokens: 4096,
  };

  return {
    name: agentName,
    agent_type: configData.agentType ?? "router",
    description: configData.description ?? "",
    parent_agent_id: null,
    system_prompt_id: selectedPromptId,
    persona: null,
    routing_options: {},
    short_term_memory: false,
    long_term_memory: false,
    reasoning: false,
    input_type: ["text"],
    output_type: ["text"],
    response_type: getResponseType(configData.outputFormat),
    max_retries: 3,
    timeout: null,
    deployed: false,
    status: "active",
    priority: null,
    failure_strategies: null,
    collaboration_mode: "single",
    available_for_deployment: true,
    deployment_code: null,
    functions: convertToolsToAgentFunctions(tools),
    provider_type: getProviderForModel(configData.model || "gpt-4o"),
    provider_config: providerConfig,
  };
}

function AgentConfigForm(): JSX.Element {
  // First, let's handle the client-side initialization properly
  const [mounted, setMounted] = useState(false);
  const panelRef = useRef<ConfigPanelHandle>(null);

  // Use workflows context
  const { createWorkflowAndRefresh, updateWorkflowAndRefresh, deployWorkflowAndRefresh } = useWorkflows();

  // Use agents context
  const { createAgentAndRefresh, updateAgentAndRefresh, sidebarRightOpen, setSidebarRightOpen } = useAgents();
  const toolsContext = useTools();
  const { isEditingPrompt } = usePrompts();

  // Use refs for values that need to be stable across renders
  const workflowIdRef = useRef("");
  const reactFlowWrapper = useRef<HTMLDivElement>(null);
  const reactFlowInstanceRef = useRef<ReactFlowInstance | null>(null);

  // State for flow management
  const [nodes, setNodes] = useState<Node[]>([]);
  const [edges, setEdges] = useState<Edge[]>([]);

  // State for selected node and configuration
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [isPromptModalOpen, setIsPromptModalOpen] = useState(false);

  // State for UI
  const [workflowName, setWorkflowName] = useState("");
  const [workflowDescription, setWorkflowDescription] = useState("");
  const [workflowTags, setWorkflowTags] = useState<string[]>([]);
  const [isChatMode, setIsChatMode] = useState(false);

  const [isLoading, setIsLoading] = useState(false);
  const [showConfigPanel, setShowConfigPanel] = useState(false);
  const [activeTab, setActiveTab] = useState("actions");
  const [showTestingSidebar, setShowTestingSidebar] = useState(false);
  const [currentTestingWorkflowId, setCurrentTestingWorkflowId] = useState<string | undefined>(undefined);
  const [isToolEditing, setIsToolEditing] = useState(false);

  // Vectorizer drawer state
  const [showVectorizerDrawer, setShowVectorizerDrawer] = useState(false);
  const [vectorizerAgentName, setVectorizerAgentName] = useState("");
  const [vectorizerAgentId, setVectorizerAgentId] = useState("");
  const [isPipelineRunning, setIsPipelineRunning] = useState(false);



  // Pipeline progress listener function using polling

  const startPipelineProgressListener = useCallback(
    (pipelineId: string, backendUrl: string) => {
      let isPolling = true;
      let pollCount = 0;
      let lastCompletedSteps: string[] = [];
      let lastCurrentStage = "";
      let currentProgressData: any = null;
      const maxPolls = 600; // 10 minutes max

      if ("currentPollingCleanup" in window && typeof window.currentPollingCleanup === "function") {
        window.currentPollingCleanup();
      }

      const updateStepStatus = (
        stepType: string,
        status: "pending" | "running" | "completed" | "error"
      ): void => {
        if ("updateVectorizerStepStatus" in window && typeof window.updateVectorizerStepStatus === "function") {
          // console.log(` Updating step ${stepType} to ${status}`);
          window.updateVectorizerStepStatus(stepType, status);
        }
      };

      const cleanup = (): void => {
        // console.log("🧹 Cleaning up pipeline polling");
        isPolling = false;
        if ("currentPollingTimeout" in window && window.currentPollingTimeout && (typeof window.currentPollingTimeout === "string"
          || typeof window.currentPollingTimeout === "number")
        ) {
          clearTimeout(window.currentPollingTimeout);
          window.currentPollingTimeout = null;
        }
      };

      // Store cleanup function globally
      (window as any).currentPollingCleanup = cleanup;

      const pollProgress = async () => {
        if (!isPolling || pollCount >= maxPolls) {
          // console.log(" Stopping pipeline polling - max polls reached");
          cleanup();
          setIsPipelineRunning(false);
          return;
        }

        try {
          pollCount++;
          const statusUrl = `${backendUrl.replace(/\/$/, "")}/api/pipeline/${pipelineId}/status`;

          const response = await fetch(statusUrl, {
            method: "GET",
            headers: {
              "Content-Type": "application/json",
            },
          });

          if (response.ok) {
            const progressData = await response.json();
            currentProgressData = progressData;

            // Debug logging (reduce frequency)
            // if (pollCount % 5 === 0) {
            //   console.log("🔍 Backend Response:", progressData);
            //   console.log("🔍 Status:", progressData.status);
            //   console.log("🔍 Current step:", progressData.current_step);
            //   console.log("🔍 Total steps:", progressData.total_steps);
            // }

            // Map backend step names to frontend step types
            const stepMapping: Record<string, string> = {
              load: "load",
              parse: "parse",
              chunk: "chunk",
              embed: "embed",
              store: "store",
            };

            // Check for pipeline completion FIRST (multiple conditions)
            const isCompleted =
              progressData.status === "completed" ||
              progressData.status === "success" ||
              (progressData.current_step >= progressData.total_steps &&
                progressData.total_steps > 0) ||
              (progressData.completed_steps &&
                progressData.completed_steps.length >= 5);

            if (isCompleted) {
              // console.log("🎉 Pipeline completed! Stopping polling...");

              Object.keys(stepMapping).forEach((backendStepName) => {
                updateStepStatus(stepMapping[backendStepName], "completed");
              });

              cleanup();
              setIsPipelineRunning(false);

              if (
                typeof (window as any).pipelineCompletionHandler === "function"
              ) {
                (window as any).pipelineCompletionHandler();
              }

              // console.log("🎉 All pipeline steps completed successfully!");
              return;
            }

            if (
              progressData.status === "failed" ||
              progressData.status === "error"
            ) {
              toast.error(`❌ Pipeline failed: ${progressData.message || "Unknown error"}`);

              if (
                progressData.current_stage &&
                stepMapping[progressData.current_stage]
              ) {
                updateStepStatus(
                  stepMapping[progressData.current_stage],
                  "error"
                );
              }

              cleanup();
              setIsPipelineRunning(false);

              if (
                typeof (window as any).pipelineCompletionHandler === "function"
              ) {
                (window as any).pipelineCompletionHandler();
              }
              return;
            }

            if (
              progressData.completed_steps &&
              Array.isArray(progressData.completed_steps)
            ) {
              const newlyCompletedSteps = progressData.completed_steps.filter(
                (step: string) => !lastCompletedSteps.includes(step)
              );

              newlyCompletedSteps.forEach((stepName: string) => {
                if (stepMapping[stepName]) {
                  updateStepStatus(stepMapping[stepName], "completed");
                }
              });

              lastCompletedSteps = [...progressData.completed_steps];
            }

            if (
              progressData.current_stage &&
              stepMapping[progressData.current_stage] &&
              progressData.current_stage !== lastCurrentStage
            ) {
              const currentStepType = stepMapping[progressData.current_stage];

              if (
                !progressData.completed_steps?.includes(
                  progressData.current_stage
                )
              ) {
                updateStepStatus(currentStepType, "running");
              }

              lastCurrentStage = progressData.current_stage;
            }
          } else {
            toast.warn(` Status check failed: ${response.status.toString()}`);

            if (response.status === 404) {
              // console.log(" Pipeline not found (404) - assuming completion");
              cleanup();
              setIsPipelineRunning(false);
              return;
            }
          }
        } catch (error) {
          toast.error("Error polling pipeline status:", error);
          if (pollCount > 50) {
            // console.log(" Too many errors, stopping polling");
            cleanup();
            setIsPipelineRunning(false);
            return;
          }
        }

        // Continue polling with dynamic interval
        if (isPolling) {
          let pollInterval = 1000; // Default 1 second

          if (currentProgressData?.current_step >= 2) {
            // chunk and beyond
            pollInterval = 2000; // 2 seconds for later stages
          }

          // eslint-disable-next-line @typescript-eslint/no-misused-promises -- idk man
          (window as any).currentPollingTimeout = setTimeout(pollProgress, pollInterval);
        }
      };

      // Start polling after a short delay
      // eslint-disable-next-line @typescript-eslint/no-misused-promises -- idk man
      (window as any).currentPollingTimeout = setTimeout(pollProgress, 1000);

      // Return cleanup function
      return cleanup;
    },
    []
  );
  // Vectorizer pipeline state - persists when drawer is closed, per agent
  const [vectorizerPipelines, setVectorizerPipelines] = useState<
    Record<string, PipelineStep[]>
  >({});

  // Vectorizer step selection and configuration state
  const [selectedVectorizerStep, setSelectedVectorizerStep] =
    useState<VectorizationStepData | null>(null);
  const [vectorizerStepConfigs, setVectorizerStepConfigs] = useState<
    Record<string, Record<string, unknown>>
  >({});

  // Get current vectorizer pipeline with memoization
  const currentVectorizerPipeline = useMemo(() => {
    return vectorizerPipelines[vectorizerAgentId] ?? [];
  }, [vectorizerPipelines, vectorizerAgentId]);

  const updateVectorizerPipeline = useCallback(
    (
      pipelineOrUpdater:
        | PipelineStep[]
        | ((prev: PipelineStep[]) => PipelineStep[])
    ) => {
      setVectorizerPipelines((prev) => {
        const currentPipeline = prev[vectorizerAgentId] ?? [];
        const newPipeline =
          typeof pipelineOrUpdater === "function"
            ? pipelineOrUpdater(currentPipeline)
            : pipelineOrUpdater;

        return {
          ...prev,
          [vectorizerAgentId]: newPipeline,
        };
      });
    },
    [vectorizerAgentId]
  );

  // Handle vectorizer step selection
  const handleVectorizerStepSelect = useCallback(
    (stepData: VectorizationStepData | null) => {
      setSelectedVectorizerStep(stepData);
      // Clear regular agent selection when vectorizer step is selected
      if (stepData) {
        setShowConfigPanel(false);
        setSelectedNode(null);
      }
    },
    []
  );

  // Handle vectorizer step configuration changes
  const handleVectorizerStepConfigChange = useCallback(
    (stepId: string, config: Record<string, unknown>) => {
      setVectorizerStepConfigs((prev) => ({
        ...prev,
        [stepId]: config,
      }));
    },
    []
  );
  const handleVectorizerWorkflowSaved = useCallback(
    (newWorkflowId: string) => {
      // console.log("🎉 Vectorizer workflow saved with ID:", newWorkflowId);

      // Set the workflow ID for the testing panel
      setCurrentTestingWorkflowId(newWorkflowId);

      // Close vectorizer drawer and clear state
      setShowVectorizerDrawer(false);
      setSelectedVectorizerStep(null);

      // Clear the pipeline for this agent
      setVectorizerPipelines((prev) => ({
        ...prev,
        [vectorizerAgentId]: [],
      }));

      // Clear step configs
      setVectorizerStepConfigs({});

      // Show testing sidebar automatically
      setShowTestingSidebar(true);
    },
    [vectorizerAgentId]
  );
  // Vectorizer action handlers
  const handleVectorizerRunAllSteps = useCallback(async () => {
    setIsPipelineRunning(true);
    try {
      // console.log("Running all vectorizer steps for agent:", vectorizerAgentId);

      // Get current pipeline steps
      const currentPipeline = vectorizerPipelines[vectorizerAgentId] ?? [];

      if (currentPipeline.length === 0) {
        toast.error("No pipeline steps configured. Please add steps before running.");
        setIsPipelineRunning(false);
        return;
      }

      // Convert pipeline steps to API format
      const steps = currentPipeline.map((step) => ({
        step_type: step.type,
        config: vectorizerStepConfigs[step.id] ?? {},
      }));

      // Automatically collect file IDs from Load steps
      const loadSteps = currentPipeline.filter((step) => step.type === "load");
      const allFileIds: string[] = [];

      for (const loadStep of loadSteps) {
        const stepConfig = vectorizerStepConfigs[loadStep.id];
        const uploadedFileIds = stepConfig.uploaded_file_ids as
          | string[]
          | undefined;
        if (uploadedFileIds && uploadedFileIds.length > 0) {
          allFileIds.push(...uploadedFileIds);
        }
      }

      // console.log("Found uploaded files:", allFileIds);

      // Check if any load step uses S3
      const s3LoadSteps = loadSteps.filter((step) => {
        const stepConfig = vectorizerStepConfigs[step.id];
        return stepConfig.provider === "s3";
      });

      if (s3LoadSteps.length > 0 && allFileIds.length > 0) {
        // console.log("S3 load steps detected. Files should already be uploaded directly to S3.");

        const s3StepConfig = vectorizerStepConfigs[s3LoadSteps[0].id];
        const bucketName = s3StepConfig?.bucket_name as string;

        if (!bucketName) {
          toast.error("S3 bucket name is required for S3 pipeline. Please configure the bucket name in the load step.");
          setIsPipelineRunning(false);
          return;
        }

        // console.log(`Using S3 bucket: ${bucketName} for pipeline execution`);
      }

      // console.log("Executing pipeline with steps:", steps);
      // console.log("Step configurations:", vectorizerStepConfigs);

      // Create the request payload
      const requestPayload = {
        steps,
        file_id: allFileIds[0], // Use the first file ID for backward compatibility
        file_ids: allFileIds, // Pass all file IDs for multi-file support
        pipeline_name: `${vectorizerAgentName}-pipeline`,
      };

      // console.log("Full request payload:", JSON.stringify(requestPayload, null, 2));

      // Import the action dynamically to avoid server-side issues
      const { executeVectorizationPipeline } = await import(
        "../lib/actions/vectorization"
      );

      // Generate pipeline ID on frontend to establish connection early
      const pipelineId = `frontend-${Date.now().toString()}-${Math.random().toString(36).substr(2, 9)}`;
      const backendUrl = (
        process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"
      ).replace("127.0.0.1", "localhost");

      // Create a completion handler that will stop the running state
      const completionHandler = (): void => {
        // console.log("🎉 Pipeline execution completed - stopping UI loading state");
        setIsPipelineRunning(false);
      };

      // Store completion handler globally so polling can access it
      (window as any).pipelineCompletionHandler = completionHandler;

      // Start pipeline progress monitoring BEFORE starting the pipeline
      startPipelineProgressListener(pipelineId, backendUrl);

      // Add pipeline_id to request payload
      const requestWithId = {
        ...requestPayload,
        pipeline_id: pipelineId,
      };

      const result = await executeVectorizationPipeline(requestWithId);
      // console.log("Pipeline execution started:", result);

      // Set a backup timeout to stop the loading state (10 minutes max)
      setTimeout(() => {
        // console.log("⏰ Checking if pipeline is still running after 10 minutes...");
        if (isPipelineRunning) {
          // console.log("⏰ Pipeline timeout reached - stopping loading state");
          setIsPipelineRunning(false);
        }
      }, 600000); // 10 minutes

      // Pipeline started successfully - polling will handle status updates and completion
    } catch (error) {
      console.error("Failed to execute vectorization pipeline:", error);
      setIsPipelineRunning(false);

      // Mark the first step as error if execution failed to start
      if (typeof (window as any).updateVectorizerStepStatus === "function") {
        (window as any).updateVectorizerStepStatus("load", "error");
      }
    }
  }, [
    vectorizerAgentId,
    vectorizerPipelines,
    vectorizerStepConfigs,
    vectorizerAgentName,
    startPipelineProgressListener,
    isPipelineRunning,
  ]);

  const handleVectorizerDeploy = useCallback(() => {
    // TODO: Implement deploy functionality
    console.log("Deploying vectorizer pipeline for agent:", vectorizerAgentId);
  }, [vectorizerAgentId]);

  const handleVectorizerClone = useCallback(() => {
    // TODO: Implement clone functionality
    console.log("Cloning vectorizer pipeline for agent:", vectorizerAgentId);
  }, [vectorizerAgentId]);

  // Auto-close vectorizer drawer when clicking on other nodes in the main canvas
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent): void => {
      if (!showVectorizerDrawer) return;

      const target = event.target as Element;

      // Don't close if clicking on the drawer itself
      if (target.closest(".vectorizer-bottom-drawer")) {
        return;
      }

      // Don't close if clicking on the configuration panel
      if (target.closest(".config-panel-container")) {
        return;
      }

      // Only close if clicking on a different node in the main canvas
      const clickedNode = target.closest(".react-flow__node");
      if (clickedNode) {
        const nodeElement = clickedNode as HTMLElement;
        const nodeId = nodeElement.getAttribute("data-id");
        const node = nodes.find((n) => n.id === nodeId);

        // If it's a vectorizer node, don't close (keep drawer open)
        if (node && node.data.name === "Vectorizer Conversative Agent") {
          return;
        }

        // If it's any other type of node, close the drawer
        if (node) {
          setShowVectorizerDrawer(false);
          setSelectedVectorizerStep(null);
        }
      }
    };

    if (showVectorizerDrawer) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [showVectorizerDrawer, nodes]);

  // Workflow state management
  const [isExistingWorkflow, setIsExistingWorkflow] = useState(false);
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [lastSavedState, setLastSavedState] = useState<string>("");
  const [currentWorkflowData, setCurrentWorkflowData] = useState<WorkflowResponse | null>(null);
  const [deploymentStatus, setDeploymentStatus] = useState<{
    isDeployed: boolean;
    deployment?: WorkflowDeployment;
    inferenceUrl?: string;
  }>({ isDeployed: false });

  // State for deployment result dialog
  const [deploymentResult, setDeploymentResult] = useState<{
    deployment: WorkflowDeployment;
    workflow: WorkflowResponse;
    inferenceUrl: string;
  } | null>(null);

  // Store flow instance when it's ready
  const onInit = (instance: ReactFlowInstance): void => {
    reactFlowInstanceRef.current = instance;
  };

  useEffect(() => {
    console.log("Current Workflow:", currentWorkflowData);
  }, [currentWorkflowData]);


  // Initialize client-side only data after mount
  useEffect(() => {
    // Generate IDs only after component has mounted on the client
    if (!workflowIdRef.current) {
      workflowIdRef.current = uuidv4();
    }
    setMounted(true);
  }, []);

  useEffect(() => {
    setIsToolEditing(selectedNode?.type === "tool");
  }, [selectedNode]);

  // Workflow state management functions
  const getCurrentWorkflowState = useCallback(() => {
    const payload = {
      name: workflowName,
      description: workflowDescription,
      tags: workflowTags,
      nodes: nodes.map((node) =>
        isAgentNodeData(node.data)
          ? {
            id: node.id,
            position: node.position,
            type: "agent" as const,
            data: {
              agent: node.data.agent,
              prompt: node.data.prompt,
              tools: node.data.tools,
              tags: node.data.tags,
            },
          }
          : {
            id: node.id,
            position: node.position,
            type: "tool" as const,
            data: {
              tool: node.data.tool,
              tags: node.data.tags,
            },
          }
      ),
      edges: edges.map((edge) => ({
        source: edge.source,
        target: edge.target,
      })),
    };
    return JSON.stringify(payload);
  }, [workflowName, workflowDescription, workflowTags, nodes, edges]);

  const updateLastSavedState = useCallback(() => {
    const currentState = getCurrentWorkflowState();
    setLastSavedState(currentState);
    setHasUnsavedChanges(false);
  }, [getCurrentWorkflowState]);

  const checkDeploymentStatus = useCallback(async () => {
    if (!workflowIdRef.current) return;

    try {
      const details = await getWorkflowDeploymentDetails(workflowIdRef.current);
      setDeploymentStatus(details);
    } catch (error) {
      // eslint-disable-next-line no-console -- Error logging is acceptable
      console.error("Error checking deployment status:", error);
      setDeploymentStatus({ isDeployed: false });
    }
  }, []);

  // Track changes to workflow state
  useEffect(() => {
    if (mounted && lastSavedState !== "") {
      // Only check after we have a baseline
      const currentState = getCurrentWorkflowState();
      const hasChanges = currentState !== lastSavedState;
      setHasUnsavedChanges(hasChanges);
    }
  }, [mounted, getCurrentWorkflowState, lastSavedState]);

  // Check deployment status when workflow ID changes
  useEffect(() => {
    if (mounted && workflowIdRef.current) {
      void checkDeploymentStatus();
    }
  }, [mounted, checkDeploymentStatus]);

  // Update saved state after workflow is loaded (when currentWorkflowData changes)
  // But only when we're actually loading a workflow, not when editing properties
  const [workflowLoadedId, setWorkflowLoadedId] = useState<string | null>(null);

  useEffect(() => {
    if (mounted && currentWorkflowData && isExistingWorkflow) {
      // Only update saved state if this is a new workflow being loaded
      if (workflowLoadedId !== currentWorkflowData.workflow_id) {
        setWorkflowLoadedId(currentWorkflowData.workflow_id);
        updateLastSavedState();
      }
    }
  }, [
    mounted,
    currentWorkflowData,
    isExistingWorkflow,
    updateLastSavedState,
    workflowLoadedId,
  ]);

  // Node operations
  const handleDeleteNode = useCallback(
    (nodeId: string) => {
      setNodes((prevNodes) => prevNodes.filter((node) => node.id !== nodeId));

      // Also remove any connected edges
      setEdges((prevEdges) =>
        prevEdges.filter(
          (edge) => edge.source !== nodeId && edge.target !== nodeId
        )
      );

      // If we just deleted the selected node, clear the selection
      if (selectedNode && selectedNode.id === nodeId) {
        setSelectedNode(null);
        setShowConfigPanel(false);
      }
    },
    [selectedNode]
  );


  const handleToolAction = useCallback((nodeId: string, action: string, _nodeData?: ToolNodeData) => {
    switch (action) {
      case "editTool": setIsToolEditing(true); break;
    }
    // console.log("Tool action!");
  }, []);

  const handleNodeAction = useCallback(
    (nodeId: string, action: string, nodeData?: AgentNodeData) => {
      // If nodeData is provided, use it directly to create a node object
      let targetNode: Node | undefined;

      if (nodeData) {
        // Create a node object from the provided data
        targetNode = {
          id: nodeId,
          type: "agent",
          position: { x: 0, y: 0 }, // Position doesn't matter for this use case
          data: nodeData,
        };
      } else {
        // Fallback: try to find in nodes array
        targetNode = nodes.find((node) => node.id === nodeId);
        if (!targetNode) {
          targetNode = nodes.find((node) => node.data.id === nodeId);
        }

        if (!targetNode) {
          return;
        }
      }

      // Check if this is a vectorizer agent
      const isVectorizer =
        targetNode.data.name === "Vectorizer Conversative Agent";

      if (isVectorizer) {
        setVectorizerAgentName(targetNode.data.name);
        setVectorizerAgentId(targetNode.id); // Use unique node ID as key
        setShowVectorizerDrawer(true);
        return;
      }

      // Ensure the node is selected and config panel is shown
      setSelectedNode(targetNode);
      // console.log("targetnode:", targetNode);
      // if (targetNode.type !== "agent") return;
      setShowConfigPanel(true);

      // Ensure the sidebar is open
      if (!sidebarRightOpen) {
        setSidebarRightOpen(true);
      }

      // Use setTimeout to ensure state updates have completed before calling panel methods
      setTimeout(() => {
        panelRef.current?.showPromptDetail();
        switch (action) {
          case "tools":
            panelRef.current?.setTab("tools");
            panelRef.current?.disableEdit();
            break;
          case "config":
            panelRef.current?.setTab("config");
            panelRef.current?.disableEdit();
            break;
          case "toolsEdit":
            panelRef.current?.setTab("tools");
            panelRef.current?.enableEdit();
            break;
          case "configEdit":
            panelRef.current?.setTab("config");
            panelRef.current?.enableEdit();
            break;
          default:
            break;
        }
      }, 100);
    },
    [nodes, sidebarRightOpen, setSidebarRightOpen, showConfigPanel]
  );

  // Handle dropping an agent onto the canvas
  const onDrop = useCallback(
    (event: React.DragEvent<HTMLDivElement>) => {
      event.preventDefault();

      if (!reactFlowWrapper.current || !reactFlowInstanceRef.current) {
        toast.error("React Flow wrapper or instance not ready");
        return;
      }

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const agentDataJson = event.dataTransfer.getData("dragData/agent");
      const toolDataJson = event.dataTransfer.getData("dragData/tool");

      if (!agentDataJson && !toolDataJson) {
        toast.error("No data received during drop");
        return;
      }


      if (agentDataJson) {
        try {
          const agentData = JSON.parse(agentDataJson) as unknown;
          if (!agentData || !isAgentResponse(agentData)) {
            throw new Error("Invalid agent data");
          }

          // Get drop position in react-flow coordinates
          const position = reactFlowInstanceRef.current.project({
            x: event.clientX - reactFlowBounds.left,
            y: event.clientY - reactFlowBounds.top,
          });

          // Create a new node with a unique ID
          const nodeId = uuidv4();
          const newNode = {
            id: nodeId,
            type: "agent",
            position,
            data: {
              id: agentData.agent_id,
              shortId: agentData.id.toString(),
              type: agentData.agent_type ?? "custom",
              name: agentData.name,
              prompt: "", // Initialize with empty prompt
              tools: agentData.functions, // ChatCompletionToolParam array
              tags: [agentData.agent_type ?? "custom"], // Initialize tags with the type
              onAction: handleNodeAction,
              onDelete: handleDeleteNode,
              onConfigure: () => {
                handleNodeSelect({
                  id: nodeId,
                  type: "agent",
                  position,
                  data: {
                    id: agentData.agent_id,
                    shortId: agentData.id.toString(),
                    type: agentData.agent_type ?? "custom",
                    name: agentData.name,
                    prompt: agentData.system_prompt.prompt || "",
                    tools: agentData.functions, // ChatCompletionToolParam array
                    tags: [agentData.agent_type ?? "custom"],
                    onAction: handleNodeAction,
                    onDelete: handleDeleteNode,
                    // eslint-disable-next-line @typescript-eslint/no-empty-function -- Will be overwritten
                    onConfigure: () => { }, // This will be overwritten
                    agent: agentData,
                    config: {
                      model: agentData.system_prompt.ai_model_name,
                      agentName: agentData.name,
                      deploymentType: "",
                      modelProvider: agentData.system_prompt.ai_model_provider,
                      outputFormat: "",
                      selectedTools: agentData.functions,
                    },
                  },
                });
              },
              agent: agentData,
              config: {
                model: agentData.system_prompt.ai_model_name,
                agentName: agentData.name,
                deploymentType: "",
                modelProvider: agentData.system_prompt.ai_model_provider,
                outputFormat: "",
                selectedTools: agentData.functions,
              },
            },
          };

          setNodes((prevNodes) => [...prevNodes, newNode]);

          // Set the newly created node as selected after a small delay
          setTimeout(() => {
            handleNodeSelect(newNode);
          }, 50);
        } catch (error) {
          toast.error("Error creating agent node");
          // console.error("Error creating agent node:", error);
        }
      } else if (toolDataJson) {


        try {
          const toolData = JSON.parse(toolDataJson) as unknown;
          // console.log("toolData:", toolData);
          if (!toolData || !isTool(toolData)) throw new Error("Invalid tool data");


          const position = reactFlowInstanceRef.current.project({
            x: event.clientX - reactFlowBounds.left,
            y: event.clientY - reactFlowBounds.top,
          });


          const newToolNode = {
            id: uuidv4(),
            type: "tool",
            position,
            data: {
              id: toolData.id.toString(),
              type: toolData.tool_type,
              name: toolData.display_name ?? toolData.name,
              description: toolData.description,
              tool: toolData,
              tags: toolData.tags,
              onAction: handleToolAction,
              onDelete: handleDeleteNode,
              onConfigure: () => { console.log("Tool", toolData); },
            }
          }

          setNodes((prevNodes) => [...prevNodes, newToolNode]);

        } catch (error) {
          if (error instanceof Error) {
            toast.error(error.message);
          } else {
            toast.error("Error creating tool node");
          }
        }
      }
    },
    [handleDeleteNode]
  );

  // Handle drag over
  const onDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
  }, []);

  // Handle drag start for agent types
  const handleDragStart = useCallback(
    (event: React.DragEvent<HTMLButtonElement>, agent?: AgentResponse, tool?: unknown) => {
      // console.log("Dragging", agent ? "agent" : tool ? "tool" : "unknown");

      if (agent) {
        event.dataTransfer.setData("dragData/agent", JSON.stringify(agent));
        event.dataTransfer.effectAllowed = "move";
      } else if (tool) {
        event.dataTransfer.setData("dragData/tool", JSON.stringify(tool));
        event.dataTransfer.effectAllowed = "move";
      }

      // Add visual feedback for dragging
      const elementClassList = event.currentTarget.classList;
      elementClassList.add("dragging");
      setTimeout(() => {
        elementClassList.remove("dragging");
      }, 100);
    }, []
  );

  // Handle node selection
  const handleNodeSelect = useCallback(
    (node: Node | null) => {
      setSelectedNode(node);
      // setShowConfigPanel(node !== null && node.type === "agent");
      setShowConfigPanel(node !== null);

      // Clear vectorizer step selection when regular agent is selected
      if (node) {
        setSelectedVectorizerStep(null);
      }

      // Close vectorizer drawer when selecting other nodes
      if (showVectorizerDrawer) {
        setShowVectorizerDrawer(false);
      }
    },
    [showVectorizerDrawer]
  );

  // Handle opening the prompt modal
  const handleOpenPromptModal = useCallback(() => {
    if (selectedNode) {
      setIsPromptModalOpen(true);
    }
  }, [selectedNode]);

  // Handle closing the prompt modal
  const handleClosePromptModal = useCallback(() => {
    setIsPromptModalOpen(false);
  }, []);

  // Handle saving the prompt
  const handleSavePrompt = useCallback(
    (
      id: string,
      name: string,
      prompt: string,
      description: string,
      tags: string[] = []
    ) => {
      // Update the node data with the new name, prompt, description and tags
      setNodes((prevNodes) =>
        prevNodes.map((node) =>
          node.id === id
            ? {
              ...node,
              data: {
                ...node.data,
                name,
                prompt,
                description,
                tags,
              },
            }
            : node
        )
      );
      setIsPromptModalOpen(false);

      // Update selectedNode if it's the node we just edited
      if (selectedNode && selectedNode.id === id) {
        setSelectedNode((prev) =>
          prev
            ? {
              ...prev,
              data: {
                ...prev.data,
                name,
                prompt,
                description,
                tags,
              },
            }
            : null
        );
      }
    },
    [selectedNode]
  );

  // Handle agent name change
  const handleAgentNameChange = useCallback(
    (nodeId: string, newName: string) => {
      if (newName.trim() === "") return; // Don't allow empty names

      // Update the node data with the new name
      setNodes((prevNodes) =>
        prevNodes.map((node) =>
          node.id === nodeId
            ? {
              ...node,
              data: {
                ...node.data,
                name: newName,
                // Make sure onDelete and onConfigure are maintained
                onDelete: node.data.onDelete,
                onConfigure: node.data.onConfigure,
              },
            }
            : node
        )
      );

      // Also update selectedNode if it's the node we just edited
      if (selectedNode && selectedNode.id === nodeId) {
        setSelectedNode((prev) =>
          prev
            ? {
              ...prev,
              data: {
                ...prev.data,
                name: newName,
              },
            }
            : null
        );
      }

      // Show a brief notification to confirm the name change (optional)
      const notification = document.createElement("div");
      notification.textContent = `Agent renamed to "${newName}"`;
      notification.style.position = "fixed";
      notification.style.bottom = "20px";
      notification.style.right = "20px";
      notification.style.backgroundColor = "#f97316";
      notification.style.color = "white";
      notification.style.padding = "10px 15px";
      notification.style.borderRadius = "4px";
      notification.style.zIndex = "9999";
      notification.style.opacity = "0";
      notification.style.transition = "opacity 0.3s ease";

      document.body.appendChild(notification);

      // Fade in
      setTimeout(() => {
        notification.style.opacity = "1";
      }, 100);

      // Remove after 3 seconds
      setTimeout(() => {
        notification.style.opacity = "0";
        setTimeout(() => {
          document.body.removeChild(notification);
        }, 300);
      }, 3000);
    },
    [selectedNode, setNodes]
  );



  function buildWorkflowPayload(name?: string, description?: string): WorkflowCreateRequest {
    const nodeById = new Map(nodes.map((node) => [node.id, node]));

    const agents = nodes.map((node) => {
      const data = node.data;

      console.log("Is agent?", isAgentNodeData(data), data);
      if (isAgentNodeData(data)) {
        return {
          node_type: "agent" as const,
          agent_id: data.agent.agent_id,
          agent_type: data.agent.agent_type as string,
          prompt: data.prompt,
          tools: data.tools,
          tags: data.tags,
          position: node.position,
        };
      }

      const tool = data.tool;
      return {
        node_type: "tool" as const,
        agent_id: tool.tool_id,
        agent_type: tool.tool_type,
        position: node.position,
        tags: data.tags,
        config: getToolConfigFromParameters(tool.parameters_schema, tool.name),
      };
    });

    const connections = edges.map((edge) => {
      const source = nodeById.get(edge.source)?.data;
      const target = nodeById.get(edge.target)?.data;

      if (!source || !target) return null;

      const sourceId = isAgentNodeData(source) ? source.agent.agent_id : source.tool.tool_id;
      const targetId = isAgentNodeData(target) ? target.agent.agent_id : target.tool.tool_id;

      if (!sourceId || !targetId) {
        console.log(`Missing agent ID for connection: ${edge.source} -> ${edge.target}`);
        return null;
      }

      return {
        source_agent_id: sourceId,
        target_agent_id: targetId,
        connection_type: mapActionTypeToConnectionType(edge.data?.actionType ?? "Action"),
      };
    }).filter((connection): connection is NonNullable<typeof connection> => connection !== null);

    return {
      name: name ?? workflowName,
      // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing -- This is starting to get annoying.
      description: description === undefined ? workflowDescription : description,
      tags: workflowTags,
      configuration: {
        agents,
        connections,
      },
    };
  };





  // Deploy workflow
  const handleDeployWorkflow = async (nameOverride?: string): Promise<void> => {
    // Check for nodes
    if (nodes.length === 0) {
      toast.error("Please add at least one agent to your workflow before deploying.");
      return;
    }

    setIsLoading(true);

    try {
      // First save the workflow if it hasn't been saved yet or has changes
      let workflowData = currentWorkflowData;

      const finalWorkflowName = nameOverride ?? workflowName;
      const workflowPayload = buildWorkflowPayload(finalWorkflowName);
      console.log("Workflow payload", workflowPayload, "unsaved changes?", hasUnsavedChanges);

      if (!workflowData) {
        // Create new workflow
        workflowData = await createWorkflowAndRefresh(workflowPayload);
        setCurrentWorkflowData(workflowData);
        setIsExistingWorkflow(true);
        workflowIdRef.current = workflowData.workflow_id;
        updateLastSavedState();
      } else if (hasUnsavedChanges) {
        // Update existing workflow
        workflowData = await updateWorkflowAndRefresh(workflowData.workflow_id, workflowPayload);
        setCurrentWorkflowData(workflowData);
        updateLastSavedState();
      }

      // Update the workflow name state if it was overridden
      if (nameOverride && nameOverride !== workflowName) {
        setWorkflowName(nameOverride);
      }

      // Deploy the workflow
      const deploymentResponse = await deployWorkflowAndRefresh(
        workflowData.workflow_id,
        {
          deployment_name: `${finalWorkflowName.toLowerCase().replace(/\s+/g, "-")}-deployment`,
          environment: "production",
          deployed_by: "user",
          runtime_config: {},
        }
      );

      // Update deployment status
      await checkDeploymentStatus();

      setIsLoading(false);

      // Show post-deployment success dialog
      const inferenceUrl = `${process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://localhost:8000"}api/workflows/${workflowData.workflow_id}/execute`;
      setDeploymentResult({
        deployment: deploymentResponse,
        workflow: workflowData,
        inferenceUrl,
      });
    } catch (error) {
      toast.error(`Error: ${(error as Error).message}`);
      setIsLoading(false);
    }
  };
  // Save workflow
  const handleSaveWorkflow = async (_workflowName?: string, _description?: string): Promise<void> => {
    if (nodes.length === 0) {
      toast.warn("Please add at least one agent to your workflow before saving.");
      return;
    }

    const workflow = buildWorkflowPayload(_workflowName, _description);

    try {
      let workflowData: WorkflowResponse;

      if (currentWorkflowData && isExistingWorkflow) {
        // Update existing workflow
        workflowData = await updateWorkflowAndRefresh(
          currentWorkflowData.workflow_id,
          workflow
        );
        setCurrentWorkflowData(workflowData);
      } else {
        // Create new workflow
        workflowData = await createWorkflowAndRefresh(workflow);
        setCurrentWorkflowData(workflowData);
        setIsExistingWorkflow(true);
        workflowIdRef.current = workflowData.workflow_id;
      }

      // Update workflow name and description if they were provided
      if (_workflowName && _workflowName !== workflowName) {
        setWorkflowName(_workflowName);
      }
      if (_description !== undefined && _description !== workflowDescription) {
        setWorkflowDescription(_description);
      }

      updateLastSavedState();
    } catch (error) {
      toast.error(`Error saving workflow: ${(error as Error).message}`);
    }
  };

  function handleClearAll(): void {
    setNodes([]);
    setEdges([]);
    setSelectedNode(null);
    setShowConfigPanel(false);
    setWorkflowName("");
    setWorkflowDescription("");
    setWorkflowTags([]);
    setCurrentWorkflowData(null);
    setIsExistingWorkflow(false);
    setHasUnsavedChanges(false);
    setLastSavedState("");
    setDeploymentStatus({ isDeployed: false });
    setDeploymentResult(null);
    setIsToolEditing(false);
  }

  // Create a new workflow
  const handleCreateNewWorkflow = (): void => {
    workflowIdRef.current = uuidv4();
    setWorkflowName("My Agent Workflow");
    setWorkflowDescription("");
    setWorkflowTags([]);
    setNodes([]);
    setEdges([]);
    setIsChatMode(false);
    // setChatMessages([]);
    setSelectedNode(null);
    setShowConfigPanel(false);
    setCurrentWorkflowData(null);
    setIsExistingWorkflow(false);
    setHasUnsavedChanges(false);
    setLastSavedState("");
    setWorkflowLoadedId(null);
    setDeploymentStatus({ isDeployed: false });
    setDeploymentResult(null);

    // Close vectorizer drawer when creating new workflow
    setShowVectorizerDrawer(false);
  };

  // Handle editing workflow properties (name, description, tags)
  const handleEditWorkflow = (
    name: string,
    description: string,
    tags: string[]
  ): void => {
    // Only update local state - no backend calls
    // Changes will be persisted when the workflow is saved/deployed via Deploy button
    setWorkflowName(name);
    setWorkflowDescription(description);
    setWorkflowTags(tags);
  };

  // Memoized callback functions to prevent re-renders
  const handleSaveWorkflowCallback = useCallback(
    async (name: string, _description: string, tags: string[]) => {
      // Update workflow name, description, and tags, then save
      setWorkflowName(name);
      setWorkflowDescription(_description);
      setWorkflowTags(tags);
      await handleSaveWorkflow(name, _description);
      updateLastSavedState();
    },
    [handleSaveWorkflow]
  );

  const handleDeployWorkflowCallback = useCallback(
    (name: string, _description: string, tags: string[]) => {
      // Update workflow name, description, and tags, then deploy
      setWorkflowName(name);
      setWorkflowDescription(_description);
      setWorkflowTags(tags);
      void handleDeployWorkflow(name);
    },
    [handleDeployWorkflow]
  );

  const handleUpdateExistingWorkflowCallback = useCallback(() => {
    // Update existing workflow and deploy
    void handleDeployWorkflow();
  }, [handleDeployWorkflow]);

  const handleCreateNewWorkflowCallback = useCallback(
    (name: string, _description: string, tags: string[]) => {
      // Reset to new workflow state and deploy with new name
      setIsExistingWorkflow(false);
      setCurrentWorkflowData(null);
      workflowIdRef.current = uuidv4();
      setWorkflowName(name);
      setWorkflowDescription(_description);
      setWorkflowTags(tags);
      // Deploy the workflow with the new name
      void handleDeployWorkflow(name);
    },
    [handleDeployWorkflow]
  );

  const handleClearDeploymentResultCallback = useCallback(() => {
    setDeploymentResult(null);
  }, []);


  function getErrorTool(): Tool {
    const now = new Date().toISOString();
    // Using Date.now() for a unique-looking ID, fulfilling the 'error_' prefix request
    const uniqueId = `error_${Date.now().toString()}_${Math.random().toString(36).substring(2, 6)}`;

    const errorSchema: ToolParametersSchema = {
      tool_name: "ErrorParameters",
      tool_description: "This tool accepts no parameters as it represents an error state.",
      properties: {}, // Minimum required property for ToolParametersSchema
      required: []
    };

    const errorTool: Tool = {
      // Error-specific fields
      id: uniqueId,
      tool_id: `internal-error-${uuidv4()}`,
      name: "Internal Error Handler",
      description: "This tool is an internal placeholder signaling that the requested tool could not be loaded, found, or is unavailable.",
      version: "0.0.1",
      tool_type: "local",
      execution_type: "internal",

      // Required structural fields
      parameters_schema: errorSchema,
      auth_required: false,

      // Status fields indicating unavailability
      is_active: false,
      is_available: false,

      // Date/Usage fields
      created_at: now,
      updated_at: now,
      usage_count: 0,
    };

    return errorTool;
  }


  // Memoized tools array to prevent re-renders
  const memoizedTools = useMemo(() => {
    return nodes.flatMap((node) => (isAgentNodeData(node.data) ? node.data.tools ?? [] : []));
  }, [nodes]);

  // Create a new empty agent on the canvas
  function handleCreateNewAgent(): void {
    if (!reactFlowWrapper.current || !reactFlowInstanceRef.current) {
      toast.error("React Flow wrapper or instance not ready");
      return;
    }

    // Create a new empty agent with default values
    const nodeId = uuidv4();
    const agentId = uuidv4();

    // Create a default empty agent data structure
    const defaultAgentData: AgentResponse = {
      agent_id: agentId,
      id: parseInt(agentId.slice(0, 8), 16), // Convert part of UUID to number
      name: "New Agent",
      description: "A new agent ready to be configured",
      agent_type: "router",
      system_prompt: {
        prompt_label: "No Prompt Selected",
        prompt: "",
        unique_label: `placeholder-${agentId.slice(0, 8)}`,
        app_name: "agent-studio",
        version: "1.0.0",
        ai_model_provider: "openai",
        ai_model_name: "gpt-4",
        tags: ["placeholder"],
        hyper_parameters: null,
        variables: null,
        id: parseInt(agentId.slice(0, 8), 16),
        pid: "placeholder", // Use placeholder ID that won't match any real prompt
        sha_hash: "",
        is_deployed: false,
        created_time: new Date().toISOString(),
        deployed_time: null,
        last_deployed: null,
      },
      functions: [],
      deployment_code: agentId.slice(0, 8),
      system_prompt_id: agentId,
      parent_agent_id: null,
      persona: null,
      routing_options: {},
      short_term_memory: false,
      long_term_memory: false,
      reasoning: false,
      input_type: ["text"],
      output_type: ["text"],
      response_type: "json",
      max_retries: 3,
      timeout: null,
      deployed: false,
      status: "active",
      priority: null,
      failure_strategies: null,
      collaboration_mode: "single",
      available_for_deployment: true,
      session_id: null,
      last_active: null,
    };

    // Position the new agent in the center of the visible canvas
    const canvasCenter = reactFlowInstanceRef.current.getViewport();
    const position = {
      x: -canvasCenter.x / canvasCenter.zoom + 300,
      y: -canvasCenter.y / canvasCenter.zoom + 200,
    };

    const newNode: Node = {
      id: nodeId,
      type: "agent",
      position,
      data: {
        id: agentId,
        shortId: agentId.slice(0, 8),
        type: "router",
        name: "New Agent",
        prompt: "",
        tools: [],
        tags: ["new"],
        onAction: handleNodeAction,
        onDelete: handleDeleteNode,
        onConfigure: () => {
          handleNodeSelect(newNode);
        },
        agent: defaultAgentData,
        config: {
          model: "gpt-4",
          agentName: "New Agent",
          deploymentType: "Elevaite",
          modelProvider: "openai",
          outputFormat: "JSON",
          selectedTools: [],
        },
      },
    };

    // Add the new node to the canvas
    setNodes((prevNodes) => [...prevNodes, newNode]);

    // Select the newly created node and open the config panel
    setTimeout(() => {
      handleNodeSelect(newNode);
    }, 50);
  }

  // Load an existing workflow
  function handleLoadWorkflow(workflowDetails: WorkflowResponse): void {
    try {
      // Set workflow metadata
      workflowIdRef.current = workflowDetails.workflow_id;
      setWorkflowName(workflowDetails.name);
      setWorkflowDescription(workflowDetails.description ?? "");
      setWorkflowTags(workflowDetails.tags ?? []);

      // Convert workflow agents to nodes
      const loadedNodes: Node[] = [];
      workflowDetails.workflow_agents.forEach((workflowAgent: WorkflowAgent) => {
        console.log("Workflow agent:", workflowAgent);
        const agent = workflowAgent.agent;
        const nodeId = workflowAgent.node_id || workflowAgent.agent_id;

        const newNode: Node = {
          id: nodeId,
          type: workflowAgent.agent.agent_type === "tool" ? "tool" : "agent",
          position: {
            x: workflowAgent.position_x ?? 100,
            y: workflowAgent.position_y ?? 100,
          },
          data:
            agent.agent_type === "tool" ?
              {
                id: nodeId,
                type: "local",
                name: agent.name,
                // eslint-disable-next-line @typescript-eslint/prefer-nullish-coalescing -- ...stupid coalescing
                description: agent.description === undefined || agent.description === null ? undefined : agent.description,
                config: {
                  tool_defaultName: workflowAgent.agent_config?.tool_name && typeof workflowAgent.agent_config.tool_name === "string" ? workflowAgent.agent_config.tool_name : "unknown_tool",
                  tool_name: workflowAgent.agent_config?.step_label && typeof workflowAgent.agent_config.step_label === "string" ? workflowAgent.agent_config.step_label : undefined,
                  tool_description: workflowAgent.agent_config?.step_description && typeof workflowAgent.agent_config.step_description === "string" ? workflowAgent.agent_config.step_description : undefined,
                  param_mapping: workflowAgent.agent_config?.param_mapping && typeof workflowAgent.agent_config.param_mapping === "object" ? workflowAgent.agent_config.param_mapping as Record<string, unknown> : undefined,
                  static_params: workflowAgent.agent_config?.static_params && typeof workflowAgent.agent_config.static_params === "object" ? workflowAgent.agent_config?.static_params as Record<string, unknown> : undefined,
                },
                onAction: handleToolAction,
                onDelete: handleDeleteNode,
                onConfigure: () => { handleNodeSelect(newNode); },
                tool: toolsContext.getToolById(agent.agent_id) ?? getErrorTool(),
              }
              :
              {
                id: nodeId,
                shortId: agent.deployment_code ?? agent.agent_id,
                type: agent.agent_type ?? "custom",
                name: agent.name,
                prompt: agent.system_prompt.prompt || "",
                tools: agent.functions, // Keep as ChatCompletionToolParam array
                tags: [agent.agent_type ?? "custom"],
                config: {
                  model: agent.system_prompt.ai_model_name,
                  agentName: agent.name,
                  deploymentType: "",
                  modelProvider: agent.system_prompt.ai_model_provider,
                  outputFormat: "",
                  selectedTools: agent.functions,
                },
                onAction: handleNodeAction,
                onDelete: handleDeleteNode,
                onConfigure: () => { handleNodeSelect(newNode); },
                agent,
              },
        };

        loadedNodes.push(newNode);
      });

      // if (workflowDetails.configuration.steps) {
      //   workflowDetails.configuration.steps.forEach(workflowStep => {
      //     const tool = toolsContext.getToolById(workflowStep.step_id);

      //   });
      // }

      // Convert workflow connections to edges
      const loadedEdges: Edge[] = [];
      if (workflowDetails.workflow_connections.length > 0) {
        workflowDetails.workflow_connections.forEach(
          (connection, index) => {
            const newEdge: Edge = {
              id: `edge-${index.toString()}`,
              source: connection.source_agent_id,
              target: connection.target_agent_id,
              animated: true,
              type: "custom",
              data: {
                actionType: mapConnectionTypeToActionType(
                  connection.connection_type
                ),
              },
            };

            loadedEdges.push(newEdge);
          }
        );
      }

      // Update state
      setNodes(loadedNodes);
      setEdges(loadedEdges);
      setIsChatMode(false);
      // setChatMessages([]);
      setSelectedNode(null);
      setShowConfigPanel(false);

      // Set workflow as existing and store workflow data
      setIsExistingWorkflow(true);
      setCurrentWorkflowData(workflowDetails);
      // Note: updateLastSavedState() will be called by useEffect after state updates

      // Close vectorizer drawer when loading workflow
      setShowVectorizerDrawer(false);

      // Check deployment status for the loaded workflow
      void checkDeploymentStatus();
    } catch (error) {
      toast.error("Error loading workflow. Please try again.");
    }
  }

  // Helper function to create a new agent in the database
  const handleCreateNewAgentInDB = async (
    configData: AgentConfigData,
    tools: ChatCompletionToolParam[],
    agentName: string
  ): Promise<void> => {
    const selectedPromptId = configData.selectedPromptId;

    if (!selectedPromptId) {
      throw new Error("A prompt must be selected to create an agent");
    }

    const agentCreateData = convertConfigToAgentCreate(
      configData,
      tools,
      agentName,
      selectedPromptId
    );

    const newAgent = await createAgentAndRefresh(agentCreateData);

    // Update the node with the new agent data from the database
    if (selectedNode) {
      setNodes((prevNodes) =>
        prevNodes.map((node) =>
          node.id === selectedNode.id
            ? {
              ...node,
              data: {
                ...node.data,
                agent: newAgent, // Update with the real agent data from DB
              },
            }
            : node
        )
      );
    }

    // Agent created successfully
  };

  // Helper function to update an existing agent in the database
  const handleUpdateExistingAgentInDB = async (configData: AgentConfigData, tools: ChatCompletionToolParam[], agentName: string): Promise<void> => {
    if (!selectedNode?.data || !isAgentNodeData(selectedNode.data)) return;
    if (!selectedNode.data.agent.agent_id) { throw new Error("No agent ID found for update"); }

    // Convert output format to valid response_type
    const getValidResponseType = (
      outputFormat?: string
    ): "json" | "yaml" | "markdown" | "HTML" | "None" => {
      if (!outputFormat) return "json";
      const format = outputFormat.toLowerCase();
      switch (format) {
        case "json": return "json";
        case "yaml": return "yaml";
        case "markdown": return "markdown";
        case "html": return "HTML";
        case "none": return "None";
        case "text": return "None";
        default: return "json";
      }
    };

    const agentUpdateData: AgentUpdate = {
      name: agentName,
      agent_type: configData.agentType,
      description: configData.description,
      functions: convertToolsToAgentFunctions(tools),
      response_type: getValidResponseType(configData.outputFormat),
      provider_type: getProviderForModel(configData.model || "gpt-4o"),
      provider_config: {
        model_name: configData.model || "gpt-4o",
        temperature: 0.7,
        max_tokens: 4096,
      },
    };

    // Include prompt update if a new prompt was selected
    if (configData.selectedPromptId) {
      agentUpdateData.system_prompt_id = configData.selectedPromptId;
    }

    const updatedAgent = await updateAgentAndRefresh(
      selectedNode.data.agent.agent_id,
      agentUpdateData
    );

    // Update the node with the updated agent data from the database
    setNodes((prevNodes) =>
      prevNodes.map((node) =>
        node.id === selectedNode.id
          ? {
            ...node,
            data: {
              ...node.data,
              agent: updatedAgent, // Update with the real agent data from DB
            },
          }
          : node
      )
    );

    // Agent updated successfully
  };

  // Handle saving the agent configuration with tools
  const handleSaveAgentConfig = async (configData: AgentConfigData): Promise<void> => {
    if (!selectedNode || !isAgentNodeData(selectedNode.data)) return;

    try {
      // If tools are provided in the configuration data, update them
      const tools = selectedNode.data.tools ?? [];

      // The name might have been updated through the inline editor
      const agentName = configData.agentName || selectedNode.data.name;

      if (configData.isNewAgent) {
        // Create a new agent in the database
        await handleCreateNewAgentInDB(configData, tools, agentName);
      } else {
        // Update existing agent in the database
        await handleUpdateExistingAgentInDB(configData, tools, agentName);
      }

      // Update the node data with the new configuration
      setNodes((prevNodes) =>
        prevNodes.map((node) => {
          if (node.id !== selectedNode.id) return node;
          if (!isAgentNodeData(node.data)) return node;
          return {
            ...node,
            data: {
              ...node.data,
              name: agentName, // Use the potentially updated name
              tools, // Update tools from configuration
              config: configData, // Store configuration in the node data
            },
          }
        })
      );

      // Show confirmation
      toast.info(`Configuration saved for ${agentName}`);
    } catch (error) {
      toast.error(`Error saving configuration: ${error instanceof Error ? error.message : "Unknown error"}`);
    }
  };

  function handleSaveToolConfig(parameters: ToolParametersSchema): void {
    const activeNode = selectedNode;
    if (!activeNode || isAgentNodeData(activeNode.data)) return;

    console.log("Node:", activeNode);
    console.log("Parameters:", parameters.properties);
    console.log("Saving stuff:", getToolConfigFromParameters(parameters));

    setNodes((previousNodes) => previousNodes.map((node) => {
      if (node.id !== activeNode.id) return node;
      if (isAgentNodeData(node.data)) return node;


      return {
        ...node,
        data: {
          ...node.data,
          name: parameters.tool_name ?? node.data.name,
          description: parameters.tool_description ?? node.data.description,
          config: getToolConfigFromParameters(parameters),
          tool: {
            ...node.data.tool,
            parameters_schema: {
              ...node.data.tool.parameters_schema,
              properties: parameters.properties,
              tool_name: parameters.tool_name ?? undefined,
              tool_description: parameters.tool_description ?? undefined,
            },
          },
        },
      };
    })
    );
    setHasUnsavedChanges(true);
  }



  function getToolConfigFromParameters(parameters?: ToolParametersSchema, toolName?: string): Record<string, unknown> {
    console.log("Parameters", parameters);
    const mapping: Record<string, unknown> = {};
    if (!parameters) return mapping;

    mapping.tool_name = parameters.tool_defaultName ?? toolName;
    if (parameters.tool_name) mapping.step_label = parameters.tool_name;
    if (parameters.tool_description) mapping.step_description = parameters.tool_description;

    const paramMapping: Record<string, unknown> = {};
    let usesResponse = false;
    for (const [key, value] of Object.entries(parameters.properties)) {
      if (value.isUsingResponse) {
        usesResponse = true;
        const v = value.value;
        paramMapping[key] = v !== undefined && String(v).trim() !== "" ? `response.${String(v)}` : undefined;
      } else {
        paramMapping[key] = value.value;
      }
    }
    mapping.param_mapping = paramMapping;

    if (usesResponse) {
      (mapping as Record<string, unknown>).input_mapping = { response: "$prev" };
    }

    console.log("Mapping:", mapping);
    return mapping;
  }



  // If not yet mounted, return a loading placeholder
  if (!mounted) {
    return (
      <div className="agent-config-form loading">
        <div className="loading-message">Loading...</div>
      </div>
    );
  }

  return (
    <>
      <HeaderBottom
        workflowName={workflowName}
        workflowDescription={workflowDescription}
        workflowTags={workflowTags}
        isLoading={isLoading}
        onSaveWorkflow={handleSaveWorkflowCallback}
        onDeployWorkflow={handleDeployWorkflowCallback}
        onClearAll={handleClearAll}
        // New props for advanced deployment flow
        isExistingWorkflow={isExistingWorkflow}
        hasUnsavedChanges={hasUnsavedChanges}
        deploymentStatus={deploymentStatus}
        currentWorkflowData={currentWorkflowData}
        tools={memoizedTools}
        onUpdateExistingWorkflow={handleUpdateExistingWorkflowCallback}
        onCreateNewWorkflow={handleCreateNewWorkflowCallback}
        // New props for deployment result handling
        deploymentResult={deploymentResult}
        onClearDeploymentResult={handleClearDeploymentResultCallback}
        // Edit workflow handler
        onEditWorkflow={handleEditWorkflow}
        showTestingSidebar={showTestingSidebar}
        setShowTestingSidebar={setShowTestingSidebar}
        isPipelineRunning={isPipelineRunning}
      />
      <ReactFlowProvider>
        <div className="agent-config-form" ref={reactFlowWrapper}>
          {/* Designer Mode */}
          {!isChatMode ? (
            <>
              {/* Designer Sidebar */}
              <DesignerSidebar
                handleDragStart={handleDragStart}
                handleCreateNewWorkflow={handleCreateNewWorkflow}
                handleLoadWorkflow={handleLoadWorkflow}
                handleCreateNewAgent={handleCreateNewAgent}
                isLoading={isLoading}
                activeTab={activeTab}
                setActiveTab={setActiveTab}
              />

              {/* Main Canvas */}
              <div className="designer-content">
                <div
                  className={`canvas-container ${showVectorizerDrawer ? "with-drawer" : ""}`}
                >
                  <DesignerCanvas
                    nodes={nodes}
                    edges={edges}
                    setNodes={setNodes}
                    setEdges={setEdges}
                    onDrop={onDrop}
                    onDragOver={onDragOver}
                    onNodeSelect={handleNodeSelect}
                    onInit={onInit}
                  />

                  {/* Vectorizer Bottom Drawer - integrated into layout */}
                  {showVectorizerDrawer ? (
                    <VectorizerBottomDrawer
                      isOpen={showVectorizerDrawer}
                      onClose={() => {
                        setShowVectorizerDrawer(false);
                        setSelectedVectorizerStep(null); // Clear selection when closing
                      }}
                      agentName={vectorizerAgentName}
                      pipeline={currentVectorizerPipeline}
                      setPipeline={updateVectorizerPipeline}
                      onStepSelect={handleVectorizerStepSelect}
                      onRunAllSteps={handleVectorizerRunAllSteps}
                      onDeploy={handleVectorizerDeploy}
                      onClone={handleVectorizerClone}
                      onWorkflowSaved={handleVectorizerWorkflowSaved}
                      isPipelineRunning={isPipelineRunning}
                    />
                  ) : null}
                </div>

                {/* Configuration Panel - shown when a node is selected OR vectorizer step is selected */}
                {showConfigPanel && selectedNode && !selectedVectorizerStep ? (
                  <div className={`config-panel-container${!sidebarRightOpen ? " shrinked" : ""}${isEditingPrompt ? " editing" : ""}`} >
                    {selectedNode.type === "agent" ?
                      <ConfigPanel
                        ref={panelRef}
                        agent={selectedNode.data as AgentNodeData}
                        agentConfig={(selectedNode.data as AgentNodeData).config}
                        agentName={selectedNode.data.name}
                        agentType={(selectedNode.data as AgentNodeData).type}
                        description={selectedNode.data.description ?? ""}
                        onEditPrompt={handleOpenPromptModal}
                        onSave={handleSaveAgentConfig}
                        onClose={() => { setShowConfigPanel(false); }}
                        onNameChange={(newName) => { handleAgentNameChange(selectedNode.id, newName); }}
                        toggleSidebar={() => { setSidebarRightOpen(!sidebarRightOpen); }}
                        sidebarOpen={sidebarRightOpen}
                        currentFunctions={(selectedNode.data as AgentNodeData).tools ?? []}
                        onFunctionsChange={(functions) => {
                          // Update the node's tools when functions change
                          setNodes((toSetNodes) =>
                            toSetNodes.map((node) =>
                              node.id === selectedNode.id
                                ? {
                                  ...node,
                                  data: { ...node.data, tools: functions },
                                }
                                : node
                            )
                          );
                        }}
                      />
                      :
                      <ToolsConfigPanel
                        toolNode={(selectedNode.data as ToolNodeData)}
                        isToolEditing={isToolEditing}
                        onToolEdit={(intent) => { setIsToolEditing(intent) }}
                        isSidebarOpen={sidebarRightOpen}
                        toggleSidebar={() => { setSidebarRightOpen(!sidebarRightOpen); }}
                        onSave={handleSaveToolConfig}
                      />
                    }
                  </div>
                ) : selectedVectorizerStep ? (
                  <div
                    className={`config-panel-container${!sidebarRightOpen ? " shrinked" : ""}`}
                  >
                    <VectorizerConfigPanel
                      selectedVectorizerStep={selectedVectorizerStep}
                      onVectorizerStepConfigChange={
                        handleVectorizerStepConfigChange
                      }
                      vectorizerStepConfigs={vectorizerStepConfigs}
                      toggleSidebar={() => {
                        setSidebarRightOpen(!sidebarRightOpen);
                      }}
                      sidebarOpen={sidebarRightOpen}
                      onClose={() => {
                        setSelectedVectorizerStep(null);
                      }}
                    />
                  </div>
                ) : null}
              </div>

              {/* Agent Configuration Modal */}
              {selectedNode && isAgentNodeData(selectedNode.data) ? (
                <AgentConfigModal
                  isOpen={isPromptModalOpen}
                  nodeData={{
                    id: selectedNode.id,
                    type: selectedNode.data.type,
                    name: selectedNode.data.name,
                    shortId: selectedNode.data.shortId,
                    prompt: selectedNode.data.prompt,
                    description: selectedNode.data.description,
                    tags: selectedNode.data.tags,
                    agent: selectedNode.data.agent,
                  }}
                  onClose={handleClosePromptModal}
                  onSave={handleSavePrompt}
                />
              ) : null}
            </>
          ) : (
            /* Chat Mode */
            <>
              {/* Chat Sidebar */}
              <ChatSidebar
                workflowName={workflowName}
                workflowId={workflowIdRef.current}
                onExitChat={() => {
                  setIsChatMode(false);
                }}
                onCreateNewWorkflow={handleCreateNewWorkflow}
                isLoading={isLoading}
              />

              {/* Chat Interface */}
              <div className="chat-content">
                <ChatInterface
                  onExitChat={() => {
                    setIsChatMode(false);
                  }}
                  onCreateNewWorkflow={handleCreateNewWorkflow}
                  workflowName={workflowName}
                  workflowId={workflowIdRef.current}
                />
              </div>
            </>
          )}
          {Boolean(showTestingSidebar) && (
            <AgentTestingPanel
              workflowId={currentTestingWorkflowId ?? currentWorkflowData?.workflow_id ?? ""}
              sessionId={currentWorkflowData?.id.toString()}
              description={workflowDescription}
            />
          )}
        </div>
      </ReactFlowProvider>
    </>
  );
}

export default AgentConfigForm;
