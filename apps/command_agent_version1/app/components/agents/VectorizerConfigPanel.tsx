"use client";

import { ChevronsLeft, ChevronsRight } from "lucide-react";
import React from "react";
import VectorizerStepConfig from "./config/VectorizerStepConfig";
import { type VectorizationStepData } from "./VectorizerBottomDrawer";
import "./ConfigPanel.scss";

interface VectorizerConfigPanelProps {
  selectedVectorizerStep: VectorizationStepData | null;
  onVectorizerStepConfigChange?: (
    stepId: string,
    config: Record<string, unknown>
  ) => void;
  vectorizerStepConfigs?: Record<string, Record<string, unknown>>;
  toggleSidebar?: () => void;
  sidebarOpen?: boolean;
  onClose?: () => void;
}

export default function VectorizerConfigPanel({
  selectedVectorizerStep,
  onVectorizerStepConfigChange,
  vectorizerStepConfigs,
  toggleSidebar,
  sidebarOpen,
  onClose,
}: VectorizerConfigPanelProps): JSX.Element {
  return (
    <div className="config-panel">
      {/* Header with minimize button */}
      <div className="config-panel-header">
        <div className="flex flex-1 items-center pr-3">
          <div className="agent-name-display">
            <div className="agent-icon flex-shrink-0">⚙️</div>
            <div className="agent-title">
              <p className="agent-name">Vectorizer Configuration</p>
              <p className="agent-description">
                {selectedVectorizerStep
                  ? `Configure ${selectedVectorizerStep.name} step`
                  : "Select a step to configure"}
              </p>
            </div>
          </div>
        </div>

        <button
          type="button"
          onClick={toggleSidebar}
          className="flex flex-shrink-0 items-center"
        >
          {sidebarOpen ? <ChevronsRight /> : <ChevronsLeft />}
        </button>
      </div>

      {/* Vectorizer Step Configuration Content */}
      <div className="nav-wrapper flex flex-col justify-between flex-1">
        <div className="nav-container">
          <VectorizerStepConfig
            stepData={selectedVectorizerStep}
            onConfigChange={onVectorizerStepConfigChange}
            existingConfig={
              selectedVectorizerStep
                ? vectorizerStepConfigs?.[selectedVectorizerStep.id]
                : undefined
            }
          />
        </div>
      </div>
    </div>
  );
}
