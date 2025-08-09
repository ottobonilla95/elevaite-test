"use client";

import React, { useCallback, useState, useEffect } from "react";
import {
  Plus,
  GripHorizontal,
  Play,
  Rocket,
  Copy,
  X,
  FolderOpen,
  FileEdit,
  Grid3X3,
  Hash,
  Database,
  Loader2,
  Check,
} from "lucide-react";
import WorkflowSaveModal from "./WorkflowSaveModal";
import PostDeploymentSuccessDialog from "./PostDeploymentSuccessDialog";
import { PipelineExecutionLogs } from "./config/PipelineExecutionLogs";
import type {
  WorkflowDeployment,
  WorkflowResponse,
} from "../../lib/interfaces/workflows";
import type { ChatCompletionToolParam } from "../../lib/interfaces/common";
import "./VectorizerBottomDrawer.scss";

// Custom toast implementation
const toast = {
  success: (message: string) => {
    const container = getToastContainer();
    showToast(container, message, "success");
  },
  error: (message: string) => {
    const container = getToastContainer();
    showToast(container, message, "error");
  },
  info: (message: string, options?: any) => {
    const container = getToastContainer();
    showToast(container, message, "info");
  },
};

function getToastContainer(): HTMLDivElement {
  let container = document.getElementById("toast-container") as HTMLDivElement;
  if (!container) {
    container = document.createElement("div");
    container.id = "toast-container";
    container.style.cssText = `
      position: fixed;
      top: 20px;
      right: 20px;
      z-index: 10000;
      pointer-events: none;
      display: flex;
      flex-direction: column;
      gap: 8px;
    `;
    document.body.appendChild(container);
  }
  return container;
}

function showToast(
  container: HTMLDivElement,
  message: string,
  type: "success" | "error" | "info"
): void {
  const toast = document.createElement("div");

  const colors = {
    success: "#10B981",
    error: "#EF4444",
    info: "#3B82F6",
  };

  const icons = {
    success: "✓",
    error: "✕",
    info: "ℹ",
  };

  toast.style.cssText = `
    background: ${colors[type]};
    color: white;
    padding: 12px 16px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    font-family: system-ui, -apple-system, sans-serif;
    font-size: 14px;
    font-weight: 500;
    display: flex;
    align-items: center;
    gap: 8px;
    max-width: 400px;
    word-wrap: break-word;
    pointer-events: auto;
    transform: translateX(100%);
    opacity: 0;
    transition: all 0.3s ease;
  `;

  toast.innerHTML = `
    <span style="font-size: 16px;">${icons[type]}</span>
    <span>${message}</span>
  `;

  container.appendChild(toast);

  requestAnimationFrame(() => {
    toast.style.transform = "translateX(0)";
    toast.style.opacity = "1";
  });

  setTimeout(
    () => {
      toast.style.transform = "translateX(100%)";
      toast.style.opacity = "0";
      setTimeout(() => {
        if (toast.parentElement) {
          toast.parentElement.removeChild(toast);
        }
      }, 300);
    },
    type === "info" ? 5000 : 4000
  );
}

export type VectorizationStepType =
  | "load"
  | "parse"
  | "chunk"
  | "embed"
  | "store"
  | "query";

export interface VectorizationStepData {
  id: string;
  type: VectorizationStepType;
  name: string;
  description: string;
  config?: Record<string, unknown>;
  onDelete: (id: string) => void;
  onSelect?: (stepData: VectorizationStepData) => void;
}

export interface PipelineStep {
  id: string;
  type: VectorizationStepType;
  name: string;
  description: string;
  config?: Record<string, unknown>;
  status?: "pending" | "running" | "completed" | "error";
  completedAt?: Date;
}

const getStepIcon = (stepType: VectorizationStepType): React.ReactElement => {
  switch (stepType) {
    case "load":
      return <FolderOpen size={20} className="text-green-600" />;
    case "parse":
      return <FileEdit size={20} className="text-blue-600" />;
    case "chunk":
      return <Grid3X3 size={20} className="text-yellow-600" />;
    case "embed":
      return <Hash size={20} className="text-pink-500" />;
    case "store":
      return <Database size={20} className="text-purple-600" />;
    case "query":
      return <Database size={20} className="text-green-600" />;
    default:
      return <Database size={20} className="text-gray-600" />;
  }
};

const getStepName = (stepType: VectorizationStepType): string => {
  switch (stepType) {
    case "load":
      return "Load Data";
    case "parse":
      return "Parse";
    case "chunk":
      return "Chunk";
    case "embed":
      return "Embed";
    case "store":
      return "Vector Store";
    case "query":
      return "Query";
    default:
      return "Unknown";
  }
};

const getStepDescription = (stepType: VectorizationStepType): string => {
  switch (stepType) {
    case "load":
      return "Load docs from sources";
    case "parse":
      return "Extract text from documents";
    case "chunk":
      return "Split text into chunks";
    case "embed":
      return "Generate vector embeddings";
    case "store":
      return "Save vectors to database";
    case "query":
      return "Search and retrieve vectors";
    default:
      return "Configure step";
  }
};

// Create default pipeline with all steps
const createDefaultPipeline = (): PipelineStep[] => {
  const stepTypes: VectorizationStepType[] = [
    "load",
    "parse",
    "chunk",
    "embed",
    "store",
  ];

  return stepTypes.map((stepType, index) => ({
    id: `${stepType}-${Date.now().toString()}-${index}`,
    type: stepType,
    name: getStepName(stepType),
    description: getStepDescription(stepType),
    config: {},
    status: "pending",
  }));
};

// Linear Pipeline Step Component
function LinearPipelineStep({
  step,
  isSelected,
  onSelect,
  onDelete,
  canDelete,
}: {
  step: PipelineStep;
  isSelected: boolean;
  onSelect: (step: PipelineStep) => void;
  onDelete: (stepId: string) => void;
  canDelete: boolean;
}): JSX.Element {
  const handleStepClick = (e: React.MouseEvent): void => {
    e.stopPropagation();
    onSelect(step);
  };

  const handleKeyDown = (e: React.KeyboardEvent): void => {
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      e.stopPropagation();
      onSelect(step);
    }
  };

  const getStatusColor = () => {
    switch (step.status) {
      case "completed":
        return "#10B981"; // Green
      case "running":
        return "#F59E0B"; // Orange
      case "error":
        return "#EF4444"; // Red
      default:
        return "#E5E7EB"; // Gray
    }
  };

  const getStatusIcon = () => {
    if (step.status === "completed") {
      return (
        <div
          style={{
            position: "absolute",
            top: "6px",
            right: "6px",
            backgroundColor: "#10B981",
            borderRadius: "50%",
            width: "24px",
            height: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "white",
            fontSize: "14px",
            fontWeight: "bold",
            zIndex: 15,
            boxShadow: "0 2px 6px rgba(16, 185, 129, 0.4)",
            border: "2px solid white",
          }}
        >
          <Check size={14} strokeWidth={3} />
        </div>
      );
    }

    if (step.status === "running") {
      return (
        <div
          style={{
            position: "absolute",
            top: "6px",
            right: "6px",
            backgroundColor: "#F59E0B",
            borderRadius: "50%",
            width: "24px",
            height: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "white",
            fontSize: "12px",
            zIndex: 15,
            boxShadow: "0 2px 6px rgba(245, 158, 11, 0.4)",
            border: "2px solid white",
            animation: "pulse 1.5s infinite",
          }}
        >
          <div
            style={{
              width: "10px",
              height: "10px",
              backgroundColor: "white",
              borderRadius: "50%",
              animation: "pulse 1s infinite alternate",
            }}
          />
        </div>
      );
    }

    if (step.status === "error") {
      return (
        <div
          style={{
            position: "absolute",
            top: "6px",
            right: "6px",
            backgroundColor: "#EF4444",
            borderRadius: "50%",
            width: "24px",
            height: "24px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "white",
            fontSize: "14px",
            fontWeight: "bold",
            zIndex: 15,
            boxShadow: "0 2px 6px rgba(239, 68, 68, 0.4)",
            border: "2px solid white",
          }}
        >
          <X size={14} strokeWidth={3} />
        </div>
      );
    }

    return null;
  };

  return (
    <div
      className={`linear-pipeline-step ${isSelected ? "selected" : ""}`}
      onClick={handleStepClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`Select ${step.name} step`}
      style={{
        position: "relative",
        background: isSelected ? "#fff7ed" : "white",
        border: `2px solid ${step.status === "completed" ? "#10B981" : isSelected ? "#f97316" : "#e5e7eb"}`,
        borderRadius: "12px",
        padding: "16px",
        width: "140px",
        height: "100px",
        cursor: "pointer",
        transition: "all 0.2s ease",
        boxShadow: isSelected
          ? "0 4px 12px rgba(249, 115, 22, 0.25)"
          : step.status === "completed"
            ? "0 4px 12px rgba(16, 185, 129, 0.25)"
            : "0 1px 3px rgba(0, 0, 0, 0.1)",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <style>
        {`
          @keyframes pulse {
            0% {
              opacity: 1;
              transform: scale(1);
            }
            50% {
              opacity: 0.7;
              transform: scale(1.05);
            }
            100% {
              opacity: 1;
              transform: scale(1);
            }
          }
        `}
      </style>

      {getStatusIcon()}

      <div
        className="step-content"
        style={{
          textAlign: "center",
          width: "100%",
          height: "100%",
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
        }}
      >
        <div
          className="step-header-centered"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <span className="step-icon">{getStepIcon(step.type)}</span>
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
            }}
          >
            <span
              className="step-name"
              style={{
                fontSize: "14px",
                fontWeight: "600",
                color:
                  step.status === "completed"
                    ? "#059669"
                    : isSelected
                      ? "#ea580c"
                      : "#1f2937",
                lineHeight: "1.2",
                textAlign: "center",
              }}
            >
              {step.name}
            </span>
            {getStepDescription(step.type) && (
              <span
                className="step-description"
                style={{
                  fontSize: "12px",
                  color:
                    step.status === "completed"
                      ? "#047857"
                      : isSelected
                        ? "#9a3412"
                        : "#6b7280",
                  marginTop: "2px",
                  lineHeight: "1.2",
                  textAlign: "center",
                  maxWidth: "100%",
                  overflow: "hidden",
                  textOverflow: "ellipsis",
                  whiteSpace: "nowrap",
                }}
              >
                {getStepDescription(step.type)}
              </span>
            )}
          </div>
        </div>

        {canDelete && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete(step.id);
            }}
            className="delete-button"
            type="button"
            aria-label={`Delete ${step.name} step`}
            style={{
              position: "absolute",
              top: "-8px",
              right: "-8px",
              backgroundColor: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "50%",
              width: "20px",
              height: "20px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              cursor: "pointer",
              color: "#6b7280",
              fontSize: "12px",
              zIndex: 10,
            }}
          >
            <X size={12} />
          </button>
        )}
      </div>
    </div>
  );
}

// Add Step Button Component
function AddStepButton({
  onAddStep,
  insertIndex,
}: {
  onAddStep: (stepType: VectorizationStepType, insertIndex?: number) => void;
  insertIndex?: number;
}): JSX.Element {
  const [showDropdown, setShowDropdown] = useState(false);

  const availableStepTypes: VectorizationStepType[] = [
    "load",
    "parse",
    "chunk",
    "embed",
    "store",
  ];

  const handleAddStep = (stepType: VectorizationStepType): void => {
    onAddStep(stepType, insertIndex);
    setShowDropdown(false);
  };

  return (
    <div
      className="add-step-container"
      style={{
        position: "relative",
        display: "flex",
        alignItems: "center",
        margin: "0 16px",
      }}
    >
      <div
        className="connector-line"
        style={{
          position: "absolute",
          width: "60px",
          height: "2px",
          backgroundColor: "#e5e7eb",
          zIndex: 1,
        }}
      />
      <div
        className="add-step-button-wrapper"
        style={{ position: "relative", zIndex: 2 }}
      >
        <button
          className="add-step-button"
          onClick={() => {
            setShowDropdown(!showDropdown);
          }}
          type="button"
          aria-label="Add pipeline step"
          style={{
            width: "32px",
            height: "32px",
            borderRadius: "50%",
            background: "#f97316",
            border: "2px solid white",
            color: "white",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            cursor: "pointer",
            transition: "all 0.2s ease",
            boxShadow: "0 1px 3px rgba(0, 0, 0, 0.1)",
          }}
        >
          <Plus size={16} />
        </button>

        {showDropdown && (
          <div
            className="step-dropdown"
            style={{
              maxHeight: "300px",
              overflowY: "auto",
              zIndex: 1000,
              position: "absolute",
              top: "100%",
              left: "50%",
              transform: "translateX(-50%)",
              marginTop: "0.5rem",
              backgroundColor: "white",
              border: "1px solid #e5e7eb",
              borderRadius: "8px",
              boxShadow: "0 10px 15px -3px rgba(0, 0, 0, 0.1)",
              minWidth: "200px",
            }}
          >
            {availableStepTypes.map((stepType) => (
              <button
                key={stepType}
                className="step-option"
                onClick={() => handleAddStep(stepType)}
                type="button"
                style={{
                  display: "flex",
                  alignItems: "center",
                  width: "100%",
                  padding: "12px",
                  border: "none",
                  backgroundColor: "transparent",
                  cursor: "pointer",
                }}
              >
                <span
                  className="step-option-icon"
                  style={{ marginRight: "12px" }}
                >
                  {getStepIcon(stepType)}
                </span>
                <div className="step-option-info">
                  <span
                    className="step-option-name"
                    style={{ display: "block", fontWeight: "500" }}
                  >
                    {getStepName(stepType)}
                  </span>
                  <span
                    className="step-option-description"
                    style={{
                      display: "block",
                      fontSize: "12px",
                      color: "#6b7280",
                    }}
                  >
                    {getStepDescription(stepType)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

interface VectorizerBottomDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  agentName: string;
  pipeline: PipelineStep[];
  setPipeline: React.Dispatch<React.SetStateAction<PipelineStep[]>>;
  onStepSelect?: (stepData: VectorizationStepData | null) => void;
  onRunAllSteps?: () => void;
  onDeploy?: () => void;
  onClone?: () => void;
  onWorkflowSaved?: (workflowId: string) => void;
  isPipelineRunning?: boolean;
}

export default function VectorizerBottomDrawer({
  isOpen,
  onClose,
  agentName,
  pipeline,
  setPipeline,
  onStepSelect,
  onRunAllSteps,
  onDeploy,
  onClone,
  onWorkflowSaved,
  isPipelineRunning = false,
}: VectorizerBottomDrawerProps): JSX.Element | null {
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 });

  // Modal states
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [showSuccessDialog, setShowSuccessDialog] = useState(false);
  const [deploymentResult, setDeploymentResult] = useState<{
    deployment: WorkflowDeployment;
    workflow: WorkflowResponse;
    inferenceUrl: string;
  } | null>(null);

  // Pipeline execution states
  const [showPipelineLogs, setShowPipelineLogs] = useState(false);
  const [isExecutingPipeline, setIsExecutingPipeline] = useState(false);

  // Initialize with default pipeline when drawer opens
  useEffect(() => {
    if (isOpen && pipeline.length === 0) {
      const defaultPipeline = createDefaultPipeline();
      setPipeline(defaultPipeline);

      // Select the first step by default
      setSelectedStepId(defaultPipeline[0].id);

      if (onStepSelect) {
        onStepSelect({
          id: defaultPipeline[0].id,
          type: defaultPipeline[0].type,
          name: defaultPipeline[0].name,
          description: defaultPipeline[0].description,
          config: defaultPipeline[0].config,
          onDelete: () => {
            handleDeleteStep(defaultPipeline[0].id);
          },
          onSelect: handleStepSelect,
        });
      }
    }
  }, [isOpen]);

  // Auto-reset button when all steps are completed
  useEffect(() => {
    const allStepsCompleted = pipeline.every(
      (step) => step.status === "completed"
    );
    const hasSteps = pipeline.length > 0;

    if (
      allStepsCompleted &&
      hasSteps &&
      (isPipelineRunning || isExecutingPipeline)
    ) {
      console.log("🔧 All steps completed, auto-resetting button state");

      // Small delay to ensure completion animations finish
      setTimeout(() => {
        setIsExecutingPipeline(false);

        // Also trigger parent component reset if running
        if (typeof (window as any).pipelineCompletionHandler === "function") {
          (window as any).pipelineCompletionHandler();
        }
      }, 1500); // 1.5 second delay to let completion animations show
    }
  }, [pipeline, isPipelineRunning, isExecutingPipeline]);

  // Expose button reset function globally for parent component
  useEffect(() => {
    (window as any).resetVectorizerButton = () => {
      console.log("🔧 Manual button reset triggered");
      setIsExecutingPipeline(false);
    };

    return () => {
      delete (window as any).resetVectorizerButton;
    };
  }, []);

  // Custom run all steps function that syncs with backend
  const handleRunAllSteps = useCallback(async () => {
    try {
      console.log("Running all vectorizer steps for pipeline:", pipeline);

      if (pipeline.length === 0) {
        toast.error(
          "No pipeline steps configured. Please add steps before running."
        );
        return;
      }

      // Show the pipeline logs panel
      setShowPipelineLogs(true);
      setIsExecutingPipeline(true);

      // Reset all step statuses to pending
      setPipeline((prev) =>
        prev.map((step) => ({ ...step, status: "pending" as const }))
      );

      toast.info("Pipeline execution started. Watch the steps complete!", {
        duration: 3000,
      });

      // Use the external onRunAllSteps if provided (connects to real backend)
      if (onRunAllSteps) {
        await onRunAllSteps();
        return;
      }

      // Fallback: simulate execution for demo purposes
      const currentPipeline = pipeline;

      // Execute each step with a delay to show progress
      for (let i = 0; i < currentPipeline.length; i++) {
        const currentStep = currentPipeline[i];

        // Set current step to running
        setPipeline((prev) =>
          prev.map((step) =>
            step.id === currentStep.id
              ? { ...step, status: "running" as const }
              : step
          )
        );

        // Simulate step execution time (1.5-3 seconds per step)
        const executionTime = 1500 + Math.random() * 1500;
        await new Promise((resolve) => setTimeout(resolve, executionTime));

        // Set current step to completed
        setPipeline((prev) =>
          prev.map((step) =>
            step.id === currentStep.id
              ? {
                  ...step,
                  status: "completed" as const,
                  completedAt: new Date(),
                }
              : step
          )
        );

        toast.success(`${currentStep.name} step completed successfully!`);
      }

      setIsExecutingPipeline(false);
      toast.success("🎉 All pipeline steps completed successfully!");
    } catch (error) {
      console.error("Failed to execute vectorization pipeline:", error);
      toast.error(
        `Failed to execute pipeline: ${error instanceof Error ? error.message : "Unknown error"}`
      );
      setIsExecutingPipeline(false);

      // Mark current running step as error
      setPipeline((prev) =>
        prev.map((step) =>
          step.status === "running"
            ? { ...step, status: "error" as const }
            : step
        )
      );
    }
  }, [pipeline, onRunAllSteps]);

  // Function to update step status from external source (backend)
  const updateStepStatus = useCallback(
    (
      stepType: string,
      status: "pending" | "running" | "completed" | "error"
    ) => {
      setPipeline((prev) =>
        prev.map((step) =>
          step.type === stepType
            ? {
                ...step,
                status,
                completedAt:
                  status === "completed" ? new Date() : step.completedAt,
              }
            : step
        )
      );

      if (status === "completed") {
        toast.success(
          `${getStepName(stepType as VectorizationStepType)} step completed successfully!`
        );
      }
    },
    []
  );

  // Expose updateStepStatus for parent component to call
  useEffect(() => {
    // Store reference to updateStepStatus in a way parent can access it
    (window as any).updateVectorizerStepStatus = updateStepStatus;

    return () => {
      delete (window as any).updateVectorizerStepStatus;
    };
  }, [updateStepStatus]);

  const handlePipelineComplete = useCallback(() => {
    setIsExecutingPipeline(false);
    toast.success("Pipeline execution completed successfully!");
  }, []);

  const handleAddStep = useCallback(
    (stepType: VectorizationStepType, insertIndex?: number) => {
      const newStep: PipelineStep = {
        id: `${stepType}-${Date.now().toString()}`,
        type: stepType,
        name: getStepName(stepType),
        description: getStepDescription(stepType),
        config: {},
        status: "pending",
      };

      setPipeline((prev) => {
        if (insertIndex !== undefined) {
          const newPipeline = [...prev];

          if (stepType === "store") {
            const withoutStore = newPipeline.filter(
              (step) => step.type !== "store"
            );
            return [...withoutStore, newStep];
          }

          const storeIndex = newPipeline.findIndex(
            (step) => step.type === "store"
          );
          if (storeIndex !== -1 && insertIndex > storeIndex) {
            newPipeline.splice(storeIndex, 0, newStep);
          } else {
            newPipeline.splice(insertIndex, 0, newStep);
          }
          return newPipeline;
        }

        const storeIndex = prev.findIndex((step) => step.type === "store");
        if (stepType === "store") {
          const withoutStore = prev.filter((step) => step.type !== "store");
          return [...withoutStore, newStep];
        } else if (storeIndex !== -1) {
          const newPipeline = [...prev];
          newPipeline.splice(storeIndex, 0, newStep);
          return newPipeline;
        } else {
          return [...prev, newStep];
        }
      });

      setSelectedStepId(newStep.id);

      if (onStepSelect) {
        onStepSelect({
          id: newStep.id,
          type: newStep.type,
          name: newStep.name,
          description: newStep.description,
          config: newStep.config,
          onDelete: () => {
            handleDeleteStep(newStep.id);
          },
          onSelect: handleStepSelect,
        });
      }
    },
    [onStepSelect]
  );

  const handleDeleteStep = useCallback(
    (stepId: string) => {
      const stepToDelete = pipeline.find((step) => step.id === stepId);

      if (stepToDelete?.type === "load" && pipeline.length === 1) {
        toast.error(
          "Cannot delete the last remaining Load step. The pipeline must have at least one step."
        );
        return;
      }

      setPipeline((prev) => prev.filter((step) => step.id !== stepId));

      if (selectedStepId === stepId) {
        setSelectedStepId(null);
        if (onStepSelect) {
          onStepSelect(null);
        }
      }
    },
    [selectedStepId, onStepSelect, pipeline]
  );

  const handleStepSelect = useCallback(
    (step: PipelineStep) => {
      setSelectedStepId(step.id);
      if (onStepSelect) {
        onStepSelect({
          id: step.id,
          type: step.type,
          name: step.name,
          description: step.description,
          config: step.config,
          onDelete: () => {
            handleDeleteStep(step.id);
          },
          onSelect: handleStepSelect,
        });
      }
    },
    [onStepSelect, handleDeleteStep]
  );

  const handleSaveWorkflow = (): void => {
    setShowSaveModal(true);
  };

  const handleSaveModalSubmit = async (
    name: string,
    description: string,
    tags: string[]
  ): Promise<void> => {
    setIsLoading(true);
    try {
      const mockWorkflowId = `workflow-${Date.now().toString(36)}`;

      await new Promise((resolve) => setTimeout(resolve, 1500));

      setShowSaveModal(false);

      toast.success(`Vectorizer workflow "${name}" saved successfully! 🎉`);

      setPipeline([]);
      setSelectedStepId(null);
      if (onStepSelect) {
        onStepSelect(null);
      }
      onClose();

      if (onWorkflowSaved) {
        onWorkflowSaved(mockWorkflowId);
      }

      setTimeout(() => {
        toast.info(
          "Your knowledge bases are available to use now! Test it in the testing tab."
        );
      }, 500);
    } catch (error) {
      console.error("Error saving workflow:", error);
      toast.error("Failed to save workflow. Please try again.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleCanvasMouseDown = useCallback((e: React.MouseEvent) => {
    const target = e.target as Element;
    if (
      target.closest(".linear-pipeline-step") ??
      target.closest(".add-step-container")
    ) {
      return;
    }

    setIsDragging(true);
    setDragStart({ x: e.clientX, y: e.clientY });
    e.preventDefault();
  }, []);

  const handleCanvasMouseMove = useCallback(
    (e: React.MouseEvent) => {
      if (!isDragging) return;

      const deltaX = e.clientX - dragStart.x;
      const deltaY = e.clientY - dragStart.y;

      setCanvasOffset((prev) => ({
        x: prev.x + deltaX,
        y: prev.y + deltaY,
      }));

      setDragStart({ x: e.clientX, y: e.clientY });
    },
    [isDragging, dragStart]
  );

  const handleCanvasMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleCanvasMouseLeave = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent): void => {
      const target = event.target as Element;
      if (!target.closest(".add-step-container")) {
        const dropdowns = document.querySelectorAll(".step-dropdown");
        if (dropdowns.length > 0) {
          setTimeout(() => {
            const stillOpenDropdowns =
              document.querySelectorAll(".step-dropdown");
            stillOpenDropdowns.forEach((dropdown) => {
              (dropdown as HTMLElement).style.display = "none";
            });
          }, 100);
        }
      }
    };

    if (isOpen) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen]);

  if (!isOpen) return null;

  return (
    <>
      <div className="vectorizer-bottom-drawer">
        {/* Drag Handle */}
        <div className="drag-handle">
          <GripHorizontal className="text-gray-800" size={20} />
        </div>

        {/* Drawer Header */}
        <div className="drawer-header">
          <div className="flex flex-col gap-1">
            <h3 className="font-semibold text-gray-800">
              Subflow: {agentName}
            </h3>
            <p className="text-sm text-gray-600">Transform unstructured data</p>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-3 py-1.5 bg-white hover:bg-orange-50 text-brand-primary text-sm font-medium rounded border border-brand-primary transition-colors"
              type="button"
            >
              <X size={14} className="inline mr-1" />
              Cancel
            </button>
            <button
              onClick={() => onClone?.()}
              className="px-3 py-1.5 bg-white hover:bg-orange-50 text-brand-primary text-sm font-medium rounded border border-brand-primary transition-colors"
              type="button"
            >
              <Copy size={14} className="inline mr-1" />
              Clone
            </button>
            <button
              onClick={handleSaveWorkflow}
              className="px-3 py-1.5 bg-brand-primary hover:bg-orange-600 text-white text-sm font-medium rounded border border-brand-primary transition-colors"
              type="button"
              disabled={isLoading}
            >
              <Rocket size={14} className="inline mr-1" />
              {isLoading ? "Saving..." : "Save"}
            </button>
            <button
              onClick={handleRunAllSteps}
              className="px-3 py-1.5 bg-brand-primary hover:bg-orange-600 text-white text-sm font-medium rounded border border-brand-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              type="button"
              disabled={isPipelineRunning || isExecutingPipeline}
            >
              {isPipelineRunning || isExecutingPipeline ? (
                <Loader2 size={14} className="inline mr-1 animate-spin" />
              ) : (
                <Play size={14} className="inline mr-1" />
              )}
              {isPipelineRunning || isExecutingPipeline
                ? "Running..."
                : "Run All Steps"}
            </button>
          </div>
        </div>

        {/* Drawer Content */}
        <div
          className="drawer-content"
          style={{ display: "flex", height: "100%" }}
        >
          {/* Left side: Pipeline Canvas */}
          <div
            className={`linear-pipeline-canvas ${isDragging ? "dragging" : ""}`}
            onMouseDown={handleCanvasMouseDown}
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
            onMouseLeave={handleCanvasMouseLeave}
            role="button"
            aria-label="Interactive pipeline canvas"
            tabIndex={0}
            style={{
              flex: showPipelineLogs ? "1" : "none",
              width: showPipelineLogs ? "50%" : "100%",
              overflowX: "auto",
              overflowY: "auto",
              background: "#f9fafb",
              cursor: isDragging ? "grabbing" : "grab",
              transition: "width 0.3s ease",
            }}
          >
            <div
              className="pipeline-container"
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0",
                height: "100%",
                width: "max-content",
                minWidth: "100%",
                padding: "32px",
                transform: `translate(${canvasOffset.x.toString()}px, ${canvasOffset.y.toString()}px)`,
                transition: isDragging ? "none" : "transform 0.1s ease-out",
              }}
            >
              {pipeline.map((step, index) => {
                const isStoreStep = step.type === "store";
                const canDeleteStep = !(
                  step.type === "load" && pipeline.length === 1
                );

                return (
                  <React.Fragment key={step.id}>
                    <LinearPipelineStep
                      step={step}
                      isSelected={selectedStepId === step.id}
                      onSelect={handleStepSelect}
                      onDelete={handleDeleteStep}
                      canDelete={canDeleteStep}
                    />
                    {!isStoreStep && (
                      <AddStepButton
                        onAddStep={handleAddStep}
                        insertIndex={index + 1}
                      />
                    )}
                  </React.Fragment>
                );
              })}

              {pipeline.length === 0 && (
                <AddStepButton onAddStep={handleAddStep} />
              )}
            </div>
          </div>

          {/* Right side: Pipeline Execution Logs */}
          {showPipelineLogs && (
            <div
              className="pipeline-logs-section"
              style={{
                flex: "1",
                width: "50%",
                borderLeft: "1px solid #e5e7eb",
                background: "white",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div
                className="logs-header"
                style={{
                  padding: "16px",
                  borderBottom: "1px solid #e5e7eb",
                  background: "#f8fafc",
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                }}
              >
                <h4
                  style={{
                    fontSize: "14px",
                    fontWeight: "600",
                    color: "#374151",
                    margin: "0",
                  }}
                >
                  Pipeline Execution Logs
                </h4>
                <button
                  onClick={() => setShowPipelineLogs(false)}
                  style={{
                    padding: "4px",
                    background: "transparent",
                    border: "none",
                    color: "#6b7280",
                    cursor: "pointer",
                    borderRadius: "4px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                  onMouseEnter={(e) => {
                    (e.target as HTMLElement).style.background = "#f3f4f6";
                  }}
                  onMouseLeave={(e) => {
                    (e.target as HTMLElement).style.background = "transparent";
                  }}
                  type="button"
                >
                  <X size={16} />
                </button>
              </div>
              <div style={{ flex: "1", overflow: "hidden" }}>
                <PipelineExecutionLogs
                  steps={pipeline}
                  isRunning={isExecutingPipeline || isPipelineRunning}
                  onComplete={handlePipelineComplete}
                />
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Save Modal */}
      <WorkflowSaveModal
        isOpen={showSaveModal}
        onClose={() => setShowSaveModal(false)}
        onSave={handleSaveModalSubmit}
        onDeploy={handleSaveModalSubmit}
        initialName={`${agentName} Vectorizer Pipeline`}
        initialDescription="Automated pipeline for document processing and vectorization"
        initialTags={["vectorizer", "pipeline", "automation"]}
        isLoading={isLoading}
        mode="save"
      />

      {/* Success Dialog */}
      {showSuccessDialog && deploymentResult && (
        <PostDeploymentSuccessDialog
          isOpen={showSuccessDialog}
          onClose={() => {
            setShowSuccessDialog(false);
            setDeploymentResult(null);
          }}
          deployment={deploymentResult.deployment}
          workflow={deploymentResult.workflow}
          inferenceUrl={deploymentResult.inferenceUrl}
          tools={[]}
        />
      )}
    </>
  );
}
