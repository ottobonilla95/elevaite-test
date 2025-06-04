import React, { useEffect } from "react";
import PromptAccordion from "./PromptAccordion";
import PromptRightSidebarTabs from "./PromptRightSidebarTabs";
import PromptRightSidebarTestingConsole from "./PromptRightSidebarTestingConsole";
import { LoadingKeys, usePrompt } from "../ui/contexts/PromptContext";
import { PromptInput } from "./PromptInput";
import PromptLoading from "./PromptLoading";
import PromptRightColToggleVisilityStatus from "./PromptRightColToggleVisilityStatus";

const tabs = [
	{
		id: "tab1",
		title: "User Instructions",
		text: "Extract data based on {{table_header}}, {{line_items}}, and return {{expected_output}}.",
		active: true
	},
	{
		id: "tab2",
		title: "Table Header",
		text: "{header / Customer / Product /Quantity / Invoice Amoun...",
		active: false
	},
	{
		id: "tab3",
		title: "Table Header",
		text: "Line Item 1: ...",
		active: false
	},
	{
		id: "tab4",
		title: "Table Header",
		text: "Line Item 1: ...",
		active: false
	},

]

function PromptRightSidebar() {
	const promptContext = usePrompt();

	function handleAddPromptInput(): void {
		promptContext.addPromptInput();
	}

	function handleReset(): void {
		console.log("Reset!");
		promptContext.handleReset();
	}

	function handleRun(): void {
		promptContext.run();
	}

	function handleDeploy(): void {
		promptContext.deploy();
	}

	return (
		<div className="prompt-col prompt-right flex-1 flex flex-col rounded-2xl bg-white overflow-y-auto">
			<div className="btn-wrapper bg-white px-4 py-3 gap-3 flex items-center justify-between">
				<div><span className="font-medium">Invoice Extractor</span> <span className="text-[#E2E8ED]">|</span> <span className="text-sm">Extracts informetion from documents such as invoice, CSOWs, etc.</span></div>
				{/* <button type="button" onClick={() => promptContext.setIsRightColExpanded(!promptContext.isRightColExpanded)}>
					{
					promptContext.isRightColExpanded
					?
					<svg width="14" height="12" viewBox="0 0 14 12" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M1 11L6 6L1 1M8 11L13 6L8 1" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
					</svg>
					:
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<g opacity="0.8">
							<path d="M18 17L13 12L18 7M11 17L6 12L11 7" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
						</g>
					</svg>
					}
				</button> */}
				<div className="flex items-center gap-3">
					<button
						className="btn btn-outline btn-small flex items-center justify-center gap-1 disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-gray-100 disabled:hover:text-gray-400 px-0"
						onClick={handleReset}
						disabled={promptContext.loading[LoadingKeys.Resetting]}
					>
						<span>Reset</span>
						{promptContext.loading[LoadingKeys.Resetting] && (
							<PromptLoading className="center" width={20} height={20} />
						)}
					</button>
					<button
						className="btn btn-outline btn-small flex items-center justify-center gap-1 disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-gray-100 disabled:hover:text-gray-400 px-0"
						onClick={handleDeploy}
						disabled={promptContext.loading[LoadingKeys.Deploying]}
					>
						<span>Deploy</span>
						{promptContext.loading[LoadingKeys.Deploying] && (
							<PromptLoading className="center" width={20} height={20} />
						)}
					</button>
					<button
						className="btn btn-primary btn-small flex items-center justify-center gap-1 disabled:bg-gray-100 disabled:text-gray-400 disabled:hover:bg-gray-100 disabled:hover:text-gray-400 px-0"
						onClick={handleRun}
						disabled={promptContext.loading[LoadingKeys.Running]}
					>
						<span>Run</span>
						{promptContext.loading[LoadingKeys.Running] && (
							<PromptLoading className="center" width={20} height={20} />
						)}
						<svg
							width="12"
							height="14"
							viewBox="0 0 12 14"
							fill="none"
							xmlns="http://www.w3.org/2000/svg"
							className="transition-colors duration-200 fill-white group-hover:fill-[#FF681F] disabled:fill-gray-400"
						>
							<path
								fill="currentColor" fillRule="evenodd" clipRule="evenodd"
								d="M3.33758 0.868244C3.34555 0.873558 3.35354 0.878889 3.36156 0.884236L10.3941 5.57256C10.5975 5.70819 10.7862 5.83394 10.9311 5.9508C11.0823 6.07276 11.2606 6.24188 11.3632 6.48928C11.4988 6.81628 11.4988 7.18379 11.3632 7.5108C11.2606 7.7582 11.0823 7.92732 10.9311 8.04927C10.7862 8.16613 10.5976 8.29187 10.3941 8.4275L3.3376 13.1318C3.08888 13.2977 2.86523 13.4468 2.67545 13.5496C2.48554 13.6525 2.22486 13.7702 1.92061 13.752C1.53145 13.7288 1.17194 13.5364 0.936737 13.2254C0.752855 12.9824 0.706114 12.7002 0.686406 12.4851C0.666711 12.2702 0.666729 12.0014 0.666749 11.7024L0.666751 2.32646C0.666751 2.31682 0.66675 2.30721 0.666749 2.29763C0.666729 1.9987 0.666711 1.7299 0.686406 1.51495C0.706114 1.29985 0.752855 1.01772 0.936737 0.774642C1.17194 0.463723 1.53145 0.271323 1.92061 0.248087C2.22486 0.22992 2.48554 0.347528 2.67545 0.450447C2.86522 0.553292 3.08886 0.70241 3.33758 0.868244Z"
							/>
						</svg>
					</button>
				</div>
			</div>
			<div className="flex flex-1 gap-2 p-2 h-full min-h-0">
				<div className={`card relative ${promptContext.isRightColOutputColExpanded ? 'hidden' : 'flex'} flex-col flex-1 bg-white rounded-xl`}>
					<div className="top-wrapper overflow-auto flex flex-col">
						<div className="top flex items-center justify-between py-4 pl-4 h-[48px]">
							<div className="flex items-center gap-2">
								<div className="text-sm font-medium bg-white sticky top-0 z-10">Prompt Inputs</div>
								<button onClick={handleAddPromptInput}>
									<svg width="17" height="16" viewBox="0 0 17 16" fill="none" xmlns="http://www.w3.org/2000/svg">
										<g opacity="0.8">
											<path d="M8.49992 3.33337V12.6667M3.83325 8.00004H13.1666" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
										</g>
									</svg>
								</button>
							</div>
							<PromptRightColToggleVisilityStatus isColExpanded={promptContext.isRightColPromptInputsColExpanded} toggleColStatus={promptContext.setIsRightColPromptInputsColExpanded} />
						</div>
						<div className="middle flex-1 p-4">
							<div className="accordions">
								{promptContext.promptInputs.map(item => <PromptInput key={item.id} {...item} />)}
							</div>
						</div>
					</div>
					<PromptRightSidebarTestingConsole />
				</div>
				<PromptRightSidebarTabs />
			</div>
		</div>
	)
}
export default PromptRightSidebar;