// HeaderBottom.tsx
"use client";

import { CommonButton } from "@repo/ui/components";
import { FileText, LayoutGrid, PenLine, Upload } from "lucide-react";
import { useState } from "react";
import type { ChatCompletionToolParam } from "../../lib/interfaces/common";
import type {
  WorkflowDeployment,
  WorkflowResponse,
} from "../../lib/interfaces/workflows";
import "./HeaderBottom.scss";
import PostDeploymentSuccessDialog from "./PostDeploymentSuccessDialog";
import PreDeploymentModal from "./PreDeploymentModal";
import UploadModal from "./UploadModal";
import WorkflowEditModal from "./WorkflowEditModal";
import WorkflowSaveModal from "./WorkflowSaveModal";

interface HeaderBottomProps {
  workflowName: string;
  workflowDescription?: string;
  workflowTags?: string[];
  isLoading: boolean;
  onSaveWorkflow: (name: string, description: string, tags: string[]) => void;
  onDeployWorkflow: (name: string, description: string, tags: string[]) => void;
  // New props for advanced deployment flow
  isExistingWorkflow: boolean;
  hasUnsavedChanges: boolean;
  deploymentStatus: {
    isDeployed: boolean;
    deployment?: WorkflowDeployment;
    inferenceUrl?: string;
  };
  currentWorkflowData?: WorkflowResponse | null;
  tools?: ChatCompletionToolParam[];
  onUpdateExistingWorkflow: () => void;
  onClearAll?: () => void;
  onCreateNewWorkflow: (
    name: string,
    description: string,
    tags: string[]
  ) => void;
  // New props for deployment result handling
  deploymentResult?: {
    deployment: WorkflowDeployment;
    workflow: WorkflowResponse;
    inferenceUrl: string;
  } | null;
  onClearDeploymentResult?: () => void;
  // New props for workflow editing
  onEditWorkflow?: (name: string, description: string, tags: string[]) => void;
  showTestingSidebar: boolean;
  setShowTestingSidebar: (showSidebar: boolean) => void;
}

function HeaderBottom({
  workflowName,
  workflowDescription = "",
  workflowTags = [],
  onSaveWorkflow,
  onDeployWorkflow,
  onClearAll,
  isLoading,
  isExistingWorkflow,
  hasUnsavedChanges,
  deploymentStatus: _deploymentStatus,
  tools = [],
  onUpdateExistingWorkflow,
  onCreateNewWorkflow,
  deploymentResult,
  onClearDeploymentResult,
  onEditWorkflow,
  setShowTestingSidebar,
}: HeaderBottomProps): JSX.Element {
  const [activeBtnAction, setActiveBtnAction] = useState("workflow-creation");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isPreDeploymentDialogOpen, setIsPreDeploymentDialogOpen] =
    useState(false);
  const [isCreatingNewWorkflow, setIsCreatingNewWorkflow] = useState(false);
  const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);

  function handleClearAll(): void {
    setShowTestingSidebar(false);
    if (onClearAll) onClearAll();
  }

  function handleUploadClick(): void {
    setIsUploadModalOpen(true);
  }

  // Function to handle deploy button click - starts the advanced deployment flow
  const handleDeployClick = (): void => {
    // Debug logging
    console.log("🚀 Deploy button clicked!");
    console.log("📊 Deploy state:", {
      isExistingWorkflow,
      hasUnsavedChanges,
      workflowName,
      workflowDescription,
      workflowTags,
    });

    // Check if this is an existing workflow and if there are changes
    if (isExistingWorkflow) {
      // If there are unsaved changes, show the pre-deployment dialog to choose save vs save-as
      if (hasUnsavedChanges) {
        setIsPreDeploymentDialogOpen(true);
      } else {
        // No unsaved changes - deploy directly
        onUpdateExistingWorkflow();
      }
    } else {
      // For new workflows, go directly to save/deploy modal
      setIsModalOpen(true);
    }
  };

  // Function to close modals
  const handleCloseModal = (): void => {
    setIsModalOpen(false);
    setIsCreatingNewWorkflow(false);
  };

  const handleClosePreDeploymentDialog = (): void => {
    setIsPreDeploymentDialogOpen(false);
  };

  // Handle save workflow
  const handleSave = (
    name: string,
    description: string,
    tags: string[]
  ): void => {
    if (isCreatingNewWorkflow) {
      // We're creating a new workflow, so call the create new handler with the new name
      onCreateNewWorkflow(name, description, tags);
    } else {
      // Regular save workflow
      onSaveWorkflow(name, description, tags);
    }
    setIsModalOpen(false);
    setIsCreatingNewWorkflow(false);
  };

  // Handle deploy workflow - this will be called after successful deployment
  const handleDeploy = (
    name: string,
    description: string,
    tags: string[]
  ): void => {
    if (isCreatingNewWorkflow) {
      // We're creating a new workflow, so call the create new handler with the new name
      onCreateNewWorkflow(name, description, tags);
    } else {
      // Regular deploy workflow
      onDeployWorkflow(name, description, tags);
    }
    setIsModalOpen(false);
    setIsCreatingNewWorkflow(false);
  };

  // Handle updating existing workflow
  const handleUpdateExisting = (): void => {
    setIsPreDeploymentDialogOpen(false);
    onUpdateExistingWorkflow();
  };

  // Handle creating new workflow - open save modal for new workflow
  const handleCreateNew = (): void => {
    setIsPreDeploymentDialogOpen(false);
    setIsCreatingNewWorkflow(true);
    // Open the save modal to let user specify new workflow name and description
    setIsModalOpen(true);
  };

  // Handle edit workflow button click
  const handleEditClick = (): void => {
    setIsEditModalOpen(true);
  };

  // Handle edit modal close
  const handleCloseEditModal = (): void => {
    setIsEditModalOpen(false);
  };

  // Handle edit workflow save
  const handleEditSave = (
    name: string,
    description: string,
    tags: string[]
  ): void => {
    if (onEditWorkflow) {
      onEditWorkflow(name, description, tags);
    }
    setIsEditModalOpen(false);
  };

  // Determine display name and description
  const displayName = workflowName || "Unsaved Workflow";
  const displayDescription = workflowDescription || "";
  const isUnsaved = !workflowName;

  return (
    <div className="header-bottom">
      <button
        type="button"
        className="flex items-center gap-2"
        onClick={handleEditClick}
      >
        <PenLine size={16} />
        <div>
          <h2
            className={`text-sm font-semibold mb-1 ${isUnsaved ? "text-gray-400" : ""}`}
          >
            {displayName}
          </h2>
          <p className="text-xs font-medium text-gray-500">
            {displayDescription}
          </p>
        </div>
      </button>
      <div className="actions">
        <button
          className={`btn-workflow-creation${activeBtnAction === "workflow-creation" ? " active" : ""}`}
          type="button"
          onClick={() => {
            setShowTestingSidebar(false);
            setActiveBtnAction("workflow-creation");
          }}
        >
          <LayoutGrid size={16} />
        </button>
        <button
          className={`btn-workflow-testing${activeBtnAction === "workflow-testing" ? " active" : ""}`}
          type="button"
          onClick={() => {
            setShowTestingSidebar(true);
            setActiveBtnAction("workflow-testing");
          }}
        >
          <FileText size={17} />
        </button>
      </div>
      <div className="flex justify-end gap-2">
        <CommonButton
          className="action-button secondary"
          onClick={handleUploadClick}
        >
          <Upload size={16} />
          Upload
        </CommonButton>
        {Boolean(onClearAll) && (
          <CommonButton
            className="action-button secondary"
            onClick={handleClearAll}
          >
            Clear All
          </CommonButton>
        )}
        <CommonButton
          className="action-button"
          onClick={handleDeployClick}
          disabled={isLoading}
        >
          {isLoading ? "Deploying..." : "Deploy"}
        </CommonButton>
      </div>

      {/* Workflow Save Modal */}
      <WorkflowSaveModal
        isOpen={isModalOpen}
        onClose={handleCloseModal}
        onSave={handleSave}
        onDeploy={handleDeploy}
        initialName={
          isCreatingNewWorkflow ? `${workflowName} (Copy)` : workflowName
        }
        initialDescription={workflowDescription}
        initialTags={workflowTags}
        isLoading={isLoading}
        mode="both"
        isCreatingNew={isCreatingNewWorkflow}
      />

      {/* Pre-Deployment Modal */}
      <PreDeploymentModal
        isOpen={isPreDeploymentDialogOpen}
        onClose={handleClosePreDeploymentDialog}
        onUpdateExisting={handleUpdateExisting}
        onCreateNew={handleCreateNew}
        workflowName={workflowName}
        isExistingWorkflow={isExistingWorkflow}
        hasChanges={hasUnsavedChanges}
      />

      {/* Workflow Edit Modal */}
      <WorkflowEditModal
        isOpen={isEditModalOpen}
        onClose={handleCloseEditModal}
        onSave={handleEditSave}
        initialName={workflowName}
        initialDescription={workflowDescription}
        initialTags={workflowTags}
        isLoading={isLoading}
      />

      {/* Post-Deployment Success Dialog */}
      {deploymentResult && onClearDeploymentResult ? (
        <PostDeploymentSuccessDialog
          isOpen
          onClose={onClearDeploymentResult}
          deployment={deploymentResult.deployment}
          workflow={deploymentResult.workflow}
          inferenceUrl={deploymentResult.inferenceUrl}
          tools={tools}
        />
      ) : null}

      {/* Upload Modal */}
      <UploadModal
        isOpen={isUploadModalOpen}
        onClose={() => setIsUploadModalOpen(false)}
      />
    </div>
  );
}

export default HeaderBottom;
