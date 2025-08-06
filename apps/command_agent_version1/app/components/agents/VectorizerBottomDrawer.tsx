"use client";

import React, { useCallback, useState, useEffect } from "react";
import { X, ChevronDown, ChevronUp, Plus } from "lucide-react";
import "./VectorizerBottomDrawer.scss";

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

const getStepIcon = (stepType: VectorizationStepType): string => {
  switch (stepType) {
    case "load":
      return "📁";
    case "parse":
      return "📄";
    case "chunk":
      return "✂️";
    case "embed":
      return "🔢";
    case "store":
      return "💾";
    case "query":
      return "🔍";
    default:
      return "⚙️";
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
      return "Store";
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
}: {
  step: PipelineStep;
  isSelected: boolean;
  onSelect: (step: PipelineStep) => void;
  onDelete: (stepId: string) => void;
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

        {/* Delete button */}
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete(step.id);
          }}
          className="delete-button"
          type="button"
          aria-label={`Delete ${step.name} step`}
        >
          <X size={14} />
        </button>
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
    "query",
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

        {showDropdown ? (
          <div className="step-dropdown">
            {availableStepTypes.map((stepType) => (
              <button
                key={stepType}
                className="step-option"
                onClick={() => {
                  handleAddStep(stepType);
                }}
                type="button"
              >
                <span className="step-option-icon">
                  {getStepIcon(stepType)}
                </span>
                <div className="step-option-info">
                  <span className="step-option-name">
                    {getStepName(stepType)}
                  </span>
                  <span className="step-option-description">
                    {getStepDescription(stepType)}
                  </span>
                </div>
              </button>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

interface VectorizerBottomDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  agentName: string;
  onMinimizedChange?: (minimized: boolean) => void;
  pipeline: PipelineStep[];
  setPipeline: React.Dispatch<React.SetStateAction<PipelineStep[]>>;
  onStepSelect?: (stepData: VectorizationStepData | null) => void;
}

export default function VectorizerBottomDrawer({
  isOpen,
  onClose,
  agentName,
  onMinimizedChange,
  pipeline,
  setPipeline,
  onStepSelect,
}: VectorizerBottomDrawerProps): JSX.Element | null {
  const [isMinimized, setIsMinimized] = useState(false);
  const [selectedStepId, setSelectedStepId] = useState<string | null>(null);

  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [canvasOffset, setCanvasOffset] = useState({ x: 0, y: 0 });

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
          // Insert at specific index
          const newPipeline = [...prev];
          newPipeline.splice(insertIndex, 0, newStep);
          return newPipeline;
        }
        return [...prev, newStep];
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
      setPipeline((prev) => prev.filter((step) => step.id !== stepId));

      // Clear selection if deleted step was selected
      if (selectedStepId === stepId) {
        setSelectedStepId(null);
        if (onStepSelect) {
          onStepSelect(null);
        }
      }
    },
    [selectedStepId, onStepSelect]
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

    // Prevent text selection during drag
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
          // Trigger a small delay to allow the dropdown to close naturally
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

    if (isOpen && !isMinimized) {
      document.addEventListener("mousedown", handleClickOutside);
    }

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [isOpen, isMinimized]);

  if (!isOpen) return null;

  return (
    <div
      className={`vectorizer-bottom-drawer ${isMinimized ? "minimized" : ""}`}
    >
      {/* Drawer Header */}
      <div className="drawer-header">
        <div className="flex items-center gap-3">
          <span className="text-lg">🔢</span>
          <h3 className="font-semibold text-gray-800">
            Vectorizer: {agentName}
          </h3>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => {
              const newMinimized = !isMinimized;
              setIsMinimized(newMinimized);
              onMinimizedChange?.(newMinimized);
            }}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            type="button"
          >
            {isMinimized ? <ChevronUp size={20} /> : <ChevronDown size={20} />}
          </button>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
            type="button"
          >
            <X size={20} />
          </button>
        </div>
      </div>

      {/* Drawer Content */}
      {!isMinimized && (
        <div className="drawer-content">
          {/* Linear Pipeline Canvas */}
          <div
            className={`linear-pipeline-canvas ${isDragging ? "dragging" : ""}`}
            onMouseDown={handleCanvasMouseDown}
            onMouseMove={handleCanvasMouseMove}
            onMouseUp={handleCanvasMouseUp}
            onMouseLeave={handleCanvasMouseLeave}
            role="button"
            aria-label="Interactive pipeline canvas - use arrow keys to pan or drag with mouse"
            tabIndex={0}
            aria-pressed="false"
            onKeyDown={(e) => {
              // Handle keyboard navigation for accessibility
              if (
                e.key === "ArrowLeft" ||
                e.key === "ArrowRight" ||
                e.key === "ArrowUp" ||
                e.key === "ArrowDown"
              ) {
                e.preventDefault();
                const step = 10;
                const deltaX =
                  e.key === "ArrowLeft"
                    ? -step
                    : e.key === "ArrowRight"
                      ? step
                      : 0;
                const deltaY =
                  e.key === "ArrowUp"
                    ? -step
                    : e.key === "ArrowDown"
                      ? step
                      : 0;
                setCanvasOffset((prev) => ({
                  x: prev.x + deltaX,
                  y: prev.y + deltaY,
                }));
              }
            }}
          >
            <div
              className="pipeline-container"
              style={{
                transform: `translate(${canvasOffset.x.toString()}px, ${canvasOffset.y.toString()}px)`,
              }}
            >
              {pipeline.map((step, index) => (
                <React.Fragment key={step.id}>
                  <LinearPipelineStep
                    step={step}
                    isSelected={selectedStepId === step.id}
                    onSelect={handleStepSelect}
                    onDelete={handleDeleteStep}
                  />
                  {/* Always show add button after each step for insertion */}
                  <AddStepButton
                    onAddStep={handleAddStep}
                    insertIndex={index + 1}
                  />
                </React.Fragment>
              ))}

              {/* Show initial add button if no steps exist */}
              {pipeline.length === 0 && (
                <AddStepButton onAddStep={handleAddStep} />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
