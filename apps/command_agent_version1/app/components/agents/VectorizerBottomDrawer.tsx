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
} from "lucide-react";
import WorkflowSaveModal from "./WorkflowSaveModal";
import PostDeploymentSuccessDialog from "./PostDeploymentSuccessDialog";
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
      return "Load documents from various sources";
    case "parse":
      return "Extract text from documents";
    case "chunk":
      return "Split text into manageable chunks";
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

  return (
    <div
      className={`linear-pipeline-step ${isSelected ? "selected" : ""}`}
      onClick={handleStepClick}
      onKeyDown={handleKeyDown}
      role="button"
      tabIndex={0}
      aria-label={`Select ${step.name} step`}
    >
      <div className="step-content">
        <div className="step-header-centered">
          <span className="step-icon">{getStepIcon(step.type)}</span>
          <span className="step-name">{step.name}</span>
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
    <div className="add-step-container">
      <div className="connector-line" />
      <div className="add-step-button-wrapper">
        <button
          className="add-step-button"
          onClick={() => {
            setShowDropdown(!showDropdown);
          }}
          type="button"
          aria-label="Add pipeline step"
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
  // FIXED: Add callback with generated workflow ID
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

  useEffect(() => {
    if (isOpen && pipeline.length === 0) {
      const loadStep: PipelineStep = {
        id: `load-${Date.now().toString()}`,
        type: "load",
        name: getStepName("load"),
        description: getStepDescription("load"),
        config: {},
      };
      setPipeline([loadStep]);
      setSelectedStepId(loadStep.id);

      if (onStepSelect) {
        onStepSelect({
          id: loadStep.id,
          type: loadStep.type,
          name: loadStep.name,
          description: loadStep.description,
          config: loadStep.config,
          onDelete: () => {
            handleDeleteStep(loadStep.id);
          },
          onSelect: handleStepSelect,
        });
      }
    }
  }, [isOpen, pipeline.length]);

  const handleAddStep = useCallback(
    (stepType: VectorizationStepType, insertIndex?: number) => {
      const newStep: PipelineStep = {
        id: `${stepType}-${Date.now().toString()}`,
        type: stepType,
        name: getStepName(stepType),
        description: getStepDescription(stepType),
        config: {},
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
      // Generate a mock workflow ID for frontend testing
      const mockWorkflowId = `workflow-${Date.now().toString(36)}`;

      // TODO: Replace with actual API call when backend is ready
      // const result = await saveVectorizerWorkflow({ name, description, tags, pipeline });

      // Simulate saving workflow
      await new Promise((resolve) => setTimeout(resolve, 1500));

      setShowSaveModal(false);

      // Show success toast
      toast.success(`Vectorizer workflow "${name}" saved successfully! 🎉`);

      // CLEAR ALL STATES AND CLOSE DRAWER
      setPipeline([]);
      setSelectedStepId(null);
      if (onStepSelect) {
        onStepSelect(null);
      }
      onClose();

      // Call the callback with the generated workflow ID
      if (onWorkflowSaved) {
        onWorkflowSaved(mockWorkflowId);
      }

      // Show the notification banner after a short delay
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
              onClick={() => onRunAllSteps?.()}
              className="px-3 py-1.5 bg-brand-primary hover:bg-orange-600 text-white text-sm font-medium rounded border border-brand-primary transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              type="button"
              disabled={isPipelineRunning}
            >
              {isPipelineRunning ? (
                <Loader2 size={14} className="inline mr-1 animate-spin" />
              ) : (
                <Play size={14} className="inline mr-1" />
              )}
              {isPipelineRunning ? "Running..." : "Run All Steps"}
            </button>
          </div>
        </div>

        {/* Drawer Content */}
        <div className="drawer-content">
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
              overflowX: "auto",
              overflowY: "auto",
              width: "100%",
              height: "100%",
            }}
          >
            <div
              className="pipeline-container"
              style={{
                transform: `translate(${canvasOffset.x.toString()}px, ${canvasOffset.y.toString()}px)`,
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
