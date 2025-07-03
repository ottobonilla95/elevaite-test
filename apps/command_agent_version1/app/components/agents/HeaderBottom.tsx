// HeaderBottom.tsx
"use client";

import React, { useState } from "react";
import { FileText } from "lucide-react";
import WorkflowSaveModal from "./WorkflowSaveModal";
import PreDeploymentDialog from "./PreDeploymentDialog";
import PostDeploymentSuccessDialog from "./PostDeploymentSuccessDialog";
import type { WorkflowDeployment, WorkflowResponse } from "../../lib/interfaces/workflows";
import type { ChatCompletionToolParam } from "../../lib/interfaces/common";
import "./HeaderBottom.scss";

interface HeaderBottomProps {
	workflowName: string;
	workflowDescription?: string;
	isLoading: boolean;
	onSaveWorkflow: (name: string, description: string) => void;
	onDeployWorkflow: (name: string, description: string) => void;
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
	onCreateNewWorkflow: () => void;
	onShowPostDeploymentSuccess?: (
		deployment: WorkflowDeployment,
		workflow: WorkflowResponse,
		inferenceUrl: string
	) => void;
}

function HeaderBottom({
	workflowName,
	workflowDescription = "Analyze and process invoice documents",
	onSaveWorkflow,
	onDeployWorkflow,
	isLoading,
	isExistingWorkflow,
	hasUnsavedChanges,
	deploymentStatus,
	currentWorkflowData,
	tools = [],
	onUpdateExistingWorkflow,
	onCreateNewWorkflow,
}: HeaderBottomProps): JSX.Element {

	const [activeBtnAction, setActiveBtnAction] = useState("workflow-creation");
	const [isModalOpen, setIsModalOpen] = useState(false);
	const [isPreDeploymentDialogOpen, setIsPreDeploymentDialogOpen] = useState(false);
	const [isPostDeploymentDialogOpen, setIsPostDeploymentDialogOpen] = useState(false);
	const [deploymentResult, setDeploymentResult] = useState<{
		deployment: WorkflowDeployment;
		workflow: WorkflowResponse;
		inferenceUrl: string;
	} | null>(null);

	// Function to handle deploy button click - starts the advanced deployment flow
	const handleDeployClick = (): void => {
		// Check if this is an existing workflow and if there are changes
		if (isExistingWorkflow) {
			// For existing workflows, check if already deployed and unchanged
			if (deploymentStatus.isDeployed && !hasUnsavedChanges) {
				// Already deployed and no changes - show success dialog directly
				if (deploymentStatus.deployment && currentWorkflowData && deploymentStatus.inferenceUrl) {
					setDeploymentResult({
						deployment: deploymentStatus.deployment,
						workflow: currentWorkflowData,
						inferenceUrl: deploymentStatus.inferenceUrl
					});
					setIsPostDeploymentDialogOpen(true);
				}
				return;
			}
			// Show pre-deployment dialog for existing workflows
			setIsPreDeploymentDialogOpen(true);
		} else {
			// For new workflows, go directly to save/deploy modal
			setIsModalOpen(true);
		}
	};

	// Function to close modals
	const handleCloseModal = (): void => {
		setIsModalOpen(false);
	};

	const handleClosePreDeploymentDialog = (): void => {
		setIsPreDeploymentDialogOpen(false);
	};

	const handleClosePostDeploymentDialog = (): void => {
		setIsPostDeploymentDialogOpen(false);
		setDeploymentResult(null);
	};

	// Handle save workflow
	const handleSave = (name: string, description: string): void => {
		onSaveWorkflow(name, description);
		setIsModalOpen(false);
	};

	// Handle deploy workflow - this will be called after successful deployment
	const handleDeploy = (name: string, description: string): void => {
		onDeployWorkflow(name, description);
		setIsModalOpen(false);
	};

	// Handle updating existing workflow
	const handleUpdateExisting = (): void => {
		setIsPreDeploymentDialogOpen(false);
		onUpdateExistingWorkflow();
	};

	// Handle creating new workflow
	const handleCreateNew = (): void => {
		setIsPreDeploymentDialogOpen(false);
		onCreateNewWorkflow();
	};

	// Function to show post-deployment success dialog
	const showPostDeploymentSuccess = (
		deployment: WorkflowDeployment,
		workflow: WorkflowResponse,
		inferenceUrl: string
	): void => {
		setDeploymentResult({ deployment, workflow, inferenceUrl });
		setIsPostDeploymentDialogOpen(true);
	};

	return (
		<div className="header-bottom">
			<div>
				<h2 className="text-sm font-semibold mb-1">{workflowName}</h2>
				<p className="text-xs font-medium text-gray-500">{workflowDescription}</p>
			</div>
			<div className="actions">
				<button className={`btn-workflow-creation${activeBtnAction === 'workflow-creation' ? ' active' : ''}`} type="button" onClick={() => { setActiveBtnAction("workflow-creation"); }}>
					<svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M8.78613 13.4455V9.34021C8.78613 9.10565 8.97625 8.91553 9.21082 8.91553H13.3161C13.5507 8.91553 13.7408 9.10565 13.7408 9.34021V13.4455C13.7408 13.6801 13.5507 13.8702 13.3161 13.8702H9.21082C8.97625 13.8702 8.78613 13.6801 8.78613 13.4455Z" stroke="#1E1E1E" strokeWidth="1.06171" />
						<path d="M1 13.4455V9.34021C1 9.10565 1.19014 8.91553 1.42469 8.91553H5.52998C5.76453 8.91553 5.95466 9.10565 5.95466 9.34021V13.4455C5.95466 13.6801 5.76453 13.8702 5.52998 13.8702H1.42469C1.19014 13.8702 1 13.6801 1 13.4455Z" stroke="#1E1E1E" strokeWidth="1.06171" />
						<path d="M8.78613 5.65962V1.55432C8.78613 1.31978 8.97625 1.12964 9.21082 1.12964H13.3161C13.5507 1.12964 13.7408 1.31978 13.7408 1.55432V5.65962C13.7408 5.89416 13.5507 6.0843 13.3161 6.0843H9.21082C8.97625 6.0843 8.78613 5.89416 8.78613 5.65962Z" stroke="#1E1E1E" strokeWidth="1.06171" />
						<path d="M1 5.65962V1.55432C1 1.31978 1.19014 1.12964 1.42469 1.12964H5.52998C5.76453 1.12964 5.95466 1.31978 5.95466 1.55432V5.65962C5.95466 5.89416 5.76453 6.0843 5.52998 6.0843H1.42469C1.19014 6.0843 1 5.89416 1 5.65962Z" stroke="#1E1E1E" strokeWidth="1.06171" />
					</svg>
				</button>
				<button className={`btn-workflow-testing${activeBtnAction === 'workflow-testing' ? ' active' : ''}`} type="button" onClick={() => { setActiveBtnAction("workflow-testing"); }}>
					<FileText size={17} />
				</button>
			</div>
			<div className="flex justify-end">
				<button type="button" className="btn btn-primary" onClick={handleDeployClick} disabled={isLoading}>
					{isLoading ? 'Deploying...' : 'Deploy'}
				</button>
			</div>

			{/* Workflow Save Modal */}
			<WorkflowSaveModal
				isOpen={isModalOpen}
				onClose={handleCloseModal}
				onSave={handleSave}
				onDeploy={handleDeploy}
				initialName={workflowName}
				initialDescription={workflowDescription}
				isLoading={isLoading}
				mode="both"
			/>

			{/* Pre-Deployment Dialog */}
			<PreDeploymentDialog
				isOpen={isPreDeploymentDialogOpen}
				onClose={handleClosePreDeploymentDialog}
				onUpdateExisting={handleUpdateExisting}
				onCreateNew={handleCreateNew}
				workflowName={workflowName}
				isExistingWorkflow={isExistingWorkflow}
				hasChanges={hasUnsavedChanges}
			/>

			{/* Post-Deployment Success Dialog */}
			{deploymentResult && (
				<PostDeploymentSuccessDialog
					isOpen={isPostDeploymentDialogOpen}
					onClose={handleClosePostDeploymentDialog}
					deployment={deploymentResult.deployment}
					workflow={deploymentResult.workflow}
					inferenceUrl={deploymentResult.inferenceUrl}
					tools={tools}
				/>
			)}
		</div>
	);
}

export default HeaderBottom;