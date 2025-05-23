// DesignerSidebar.tsx
"use client";

import React from "react";
import "./HeaderBottom.scss";

interface HeaderBottomProps {
    workflowName: string;
    workflowDescription?: string;
	isLoading: boolean;
	handleDeployWorkflow: () => void;
}

const HeaderBottom: React.FC<HeaderBottomProps> = ({
    workflowName,
    workflowDescription = "Analyze and process invoice documents",
	handleDeployWorkflow, // Added save workflow function
    isLoading,
}) => {

	const [activeBtnAction, setActiveBtnAction] = React.useState("workflow-creation");

	return (
         <div className="header-bottom">
			<div>
				<h2 className="text-sm font-semibold mb-1">{workflowName}</h2>
				<p className="text-xs font-medium text-gray-500">{workflowDescription}</p>
			</div>
			<div className="actions">
				<button className={`btn-workflow-creation${activeBtnAction === 'workflow-creation' ? ' active' : ''}`} type="button" onClick={() => setActiveBtnAction("workflow-creation")}>
					<svg width="15" height="15" viewBox="0 0 15 15" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M8.78613 13.4455V9.34021C8.78613 9.10565 8.97625 8.91553 9.21082 8.91553H13.3161C13.5507 8.91553 13.7408 9.10565 13.7408 9.34021V13.4455C13.7408 13.6801 13.5507 13.8702 13.3161 13.8702H9.21082C8.97625 13.8702 8.78613 13.6801 8.78613 13.4455Z" stroke="#1E1E1E" stroke-width="1.06171"/>
						<path d="M1 13.4455V9.34021C1 9.10565 1.19014 8.91553 1.42469 8.91553H5.52998C5.76453 8.91553 5.95466 9.10565 5.95466 9.34021V13.4455C5.95466 13.6801 5.76453 13.8702 5.52998 13.8702H1.42469C1.19014 13.8702 1 13.6801 1 13.4455Z" stroke="#1E1E1E" stroke-width="1.06171"/>
						<path d="M8.78613 5.65962V1.55432C8.78613 1.31978 8.97625 1.12964 9.21082 1.12964H13.3161C13.5507 1.12964 13.7408 1.31978 13.7408 1.55432V5.65962C13.7408 5.89416 13.5507 6.0843 13.3161 6.0843H9.21082C8.97625 6.0843 8.78613 5.89416 8.78613 5.65962Z" stroke="#1E1E1E" stroke-width="1.06171"/>
						<path d="M1 5.65962V1.55432C1 1.31978 1.19014 1.12964 1.42469 1.12964H5.52998C5.76453 1.12964 5.95466 1.31978 5.95466 1.55432V5.65962C5.95466 5.89416 5.76453 6.0843 5.52998 6.0843H1.42469C1.19014 6.0843 1 5.89416 1 5.65962Z" stroke="#1E1E1E" stroke-width="1.06171"/>
					</svg>
				</button>
				<button className={`btn-workflow-testing${activeBtnAction === 'workflow-testing' ? ' active' : ''}`} type="button" onClick={() => setActiveBtnAction("workflow-testing")}>
					<svg width="17" height="19" viewBox="0 0 17 19" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M14.6695 9.48291V4.17099C14.6695 4.03578 14.6158 3.90611 14.5202 3.81049L11.8449 1.13517C11.7493 1.03955 11.6196 0.98584 11.4844 0.98584H1.58404C1.30248 0.98584 1.07422 1.2141 1.07422 1.49566V17.4702C1.07422 17.7518 1.30248 17.98 1.58404 17.98H7.02217" stroke="#1E1E1E" stroke-width="1.27456" stroke-linecap="round" stroke-linejoin="round"/>
						<path d="M4.47266 7.78311H11.2703M4.47266 4.38428H7.87148M4.47266 11.1819H7.02178" stroke="#1E1E1E" stroke-width="1.27456" stroke-linecap="round" stroke-linejoin="round"/>
						<path d="M12.9308 13.6803L13.7805 12.8306C14.1526 12.4585 14.7559 12.4585 15.128 12.8306C15.5001 13.2027 15.5001 13.806 15.128 14.178L14.2783 15.0278M12.9308 13.6803L10.3892 16.2218C10.2619 16.3492 10.1783 16.5138 10.1506 16.6917L9.94434 18.0142L11.2667 17.8081C11.4447 17.7803 11.6093 17.6967 11.7366 17.5693L14.2783 15.0278M12.9308 13.6803L14.2783 15.0278" stroke="#1E1E1E" stroke-width="1.27456" stroke-linecap="round" stroke-linejoin="round"/>
						<path d="M11.271 0.98584V3.87484C11.271 4.15641 11.4992 4.38467 11.7808 4.38467H14.6698" stroke="#1E1E1E" stroke-width="1.27456" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</button>
			</div>
			<div className="flex justify-end">
				<button type="button" className="btn btn-primary" onClick={handleDeployWorkflow} disabled={isLoading}>
					  {isLoading ? 'Deploying...' : 'Deploy'}
				</button>
			</div>
		</div>
    );
};

export default HeaderBottom;