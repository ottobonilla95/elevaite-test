import React, { useState } from "react";
import { usePrompt } from "@/ui/contexts/PromptContext";
import PromptRightColToggleVisilityStatus from "@/components/PromptRightColToggleVisilityStatus";
import { PromptInputEngineer } from "@/components/PromptInputEngineer";
import PromptRightSidebarTestingConsole from "@/components/PromptRightSidebarTestingConsole";
import PromptRightSidebarTabs from "@/components/PromptRightSidebarTabs";
import PromptDetailActionButtons from "./PromptDetailActionButtons";
import PromptInputVariableEngineer from "@/components/PromptInputVariableEngineer";
import "app/components/PromptDashboard.scss"

function PromptDetailTestingConsole() {
	const [activeTab, setActiveTab] = useState("tab1"); //variables
	const promptContext = usePrompt();

	function handleAddPromptInput(): void {
		if ("tab2" === activeTab) {
			promptContext.addPromptInputVariableEngineer();
		} else {
			promptContext.addPromptInput();
		}
	}

	return (
		<div className="w-full flex flex-col">
			<div className="prompt-col prompt-right flex-1 flex flex-col rounded-2xl bg-white overflow-y-auto">
				<div className="flex flex-1 gap-2 p-2 h-full min-h-0">
					<div className={`card relative ${promptContext.isRightColOutputColExpanded ? 'hidden' : 'flex'} flex-col flex-1 bg-white rounded-xl`}>
						{/*start*/}
						<div className="top-wrapper rounded-xl overflow-auto bg-[#F8FAFC]">
						<div className="tabs-wrapper flex flex-col w-full bg-white">
							<div className="tabs flex my-1 ml-1 text-xs text-gray-500 font-medium h-[48px]">
								<div className="tabs-inner p-1 flex flex-1">
									<button className={`tab rounded-sm p-2 flex-1${ 'tab1' == activeTab ? ' tab-active text-orange-500 bg-white' : '' }`} onClick={() => setActiveTab("tab1")}>
										Prompt Inputs
									</button>
									<button className={`tab rounded-sm p-2 flex-1${ 'tab2' == activeTab ? ' tab-active text-orange-500 bg-white' : '' }`} onClick={() => setActiveTab("tab2")}>
										Variables
									</button>
								</div>
								<div className="flex items-center ml-4">
									<button onClick={handleAddPromptInput}>
										<svg width="17" height="16" viewBox="0 0 17 16" fill="none" xmlns="http://www.w3.org/2000/svg">
											<g opacity="0.8">
												<path d="M8.49992 3.33337V12.6667M3.83325 8.00004H13.1666" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
											</g>
										</svg>
									</button>
									<PromptRightColToggleVisilityStatus isColExpanded={promptContext.isRightColPromptInputsColExpanded} toggleColStatus={promptContext.setIsRightColPromptInputsColExpanded} />
								</div>
							</div>
							<div className="tab-panels flex flex-1 text-sm w-full rounded-b-xl">
								{activeTab === "tab1" && (
									<div className="tab-panel flex flex-col flex-grow">
										<div className="tab-content p-4">
											{promptContext.promptInputs.map(item => <PromptInputEngineer key={item.id} {...item} /> )}
										</div>
									</div>
								)}
								{activeTab === "tab2" && (
									<div className="tab-panel flex-col flex-grow">
										<div className="tab-content p-4">
											{promptContext.promptInputVariablesEngineer.length > 0 && promptContext.promptInputVariablesEngineer.map((variable) => <PromptInputVariableEngineer key={variable.id} {...variable} />)}
										</div>
									</div>
								)}
							</div>
						</div>
						</div>
						{/*end*/}
						<PromptRightSidebarTestingConsole />
					</div>
					<PromptRightSidebarTabs />
				</div>
			</div>
			<PromptDetailActionButtons />
		</div>
	)
}
export default PromptDetailTestingConsole;