"use client";

import { ChevronsLeft, ChevronsRight, X } from "lucide-react";
import React from "react";
import VectorizerStepConfig from "./config/VectorizerStepConfig";
import { LogsPanel } from "./config/LogsPanel";
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
 // State for step execution (shared between config and logs)
 const [isRunning, setIsRunning] = React.useState(false);
 const [progress, setProgress] = React.useState(0);
 const [showLogs, setShowLogs] = React.useState(false);
 
 // Effect to handle panel resizing when logs show/hide OR sidebar state changes
 React.useEffect(() => {
   const configContainer = document.querySelector('.config-panel-container') as HTMLElement;
   if (configContainer) {
     // Handle collapsed sidebar first
     if (!sidebarOpen) {
       // When sidebar is collapsed, force small size and hide content
       configContainer.style.width = '60px';
       configContainer.classList.add('shrinked');
       return; // Exit early, don't process logs
     } else {
       // Sidebar is open, remove collapsed class
       configContainer.classList.remove('shrinked');
     }

     // Handle logs panel expansion when sidebar is open
     if (showLogs) {
       // Expand when logs are shown
       configContainer.style.width = '1000px';
       if (configContainer.classList.contains('editing')) {
         configContainer.style.width = '950px';
       }
     } else {
       // Shrink when logs are hidden (but sidebar is still open)
       configContainer.style.width = '400px';
       if (configContainer.classList.contains('editing')) {
         configContainer.style.width = '400px';
       }
     }
   }
 }, [showLogs, sidebarOpen]); // Watch BOTH showLogs AND sidebarOpen

 // Handle closing logs panel
 const handleCloseLogs = (): void => {
   setShowLogs(false); // This will trigger the useEffect to shrink the panel
   setIsRunning(false);
   setProgress(0);
 };

 const handleRunStep = async (): Promise<void> => {
   if (!selectedVectorizerStep) return;

   console.log("Running step, showing logs panel..."); // Debug log
   
   setIsRunning(true);
   setProgress(0);
   setShowLogs(true); // This should show the logs panel

   // Simulate step execution with progress updates
   const updateProgress = () => {
     setProgress((prev) => {
       if (prev >= 100) {
         setIsRunning(false);
         return 100;
       }
       return prev + Math.random() * 15 + 5; // Random progress increment
     });
   };

   // Update progress every 500ms
   const progressInterval = setInterval(updateProgress, 500);

   // Stop after 5 seconds (simulation)
   setTimeout(() => {
     clearInterval(progressInterval);
     setProgress(100);
     setIsRunning(false);
   }, 5000);
 };

 // Don't render content when sidebar is collapsed - just the toggle button
 if (!sidebarOpen) {
   return (
     <div className="config-panel">
       <div className="config-panel-header">
         <button
           type="button"
           onClick={toggleSidebar}
           className="flex flex-shrink-0 items-center"
         >
           <ChevronsRight />
         </button>
       </div>
     </div>
   );
 }

 return (
   <div className="config-panel">
     {/* Header with minimize button - CLEANED UP */}
     <div className="config-panel-header">
       <button
         type="button"
         onClick={toggleSidebar}
         className="flex flex-shrink-0 items-center mr-3"
       >
         <ChevronsLeft />
       </button>

       <div className="flex flex-1 items-center">
         <div className="agent-title">
           <p className="agent-name">Loading Configuration</p>
           <p className="agent-description">
             {selectedVectorizerStep
               ? `Configure ${selectedVectorizerStep.name} step`
               : "Select a step to configure"}
           </p>
         </div>
       </div>
     </div>

     {/* Main Content Area with Side-by-Side Layout */}
     <div className="vectorizer-main-content">
       {/* Left Side: Configuration */}
       <div className="vectorizer-config-section">
         <VectorizerStepConfig
           stepData={selectedVectorizerStep}
           onConfigChange={onVectorizerStepConfigChange}
           existingConfig={
             selectedVectorizerStep
               ? vectorizerStepConfigs?.[selectedVectorizerStep.id]
               : undefined
           }
           onRunStep={handleRunStep}
           isRunning={isRunning}
           showLogsPanel={showLogs}
         />
       </div>

       {/* Right Side: Logs Panel - Only show when showLogs is true AND sidebar is open */}
       {showLogs && selectedVectorizerStep && (
         <div className="vectorizer-logs-section">
           <div className="logs-panel-header flex justify-between items-center">
             <h4 className="logs-panel-title">Pipeline Execution Logs</h4>
             <div className="logs-panel-actions flex gap-2">
               <button
                 type="button"
                 onClick={handleCloseLogs}
                 className="p-1 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded"
                 title="Close logs panel"
               >
                 <X size={18} />
               </button>
             </div>
           </div>
           <div className="logs-panel-content">
             <LogsPanel 
               stepType={selectedVectorizerStep.type}
               isRunning={isRunning}
               progress={progress}
             />
           </div>
         </div>
       )}
     </div>
   </div>
 );
}