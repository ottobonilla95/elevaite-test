import { CommonSelect, type CommonSelectOption } from "@repo/ui/components";
import React, { useState } from "react";
import { usePrompt } from "../ui/contexts/PromptContext";
import PromptRightColToggleVisilityStatus from "./PromptRightColToggleVisilityStatus";
import { ParsersManager } from "./outputParsers/ParsersManager";

const models: CommonSelectOption[] = [
	{ value: 'GPT4o-Mini' },
	{ value: 'GPT 4 Turbo' },
	{ value: 'Claude 3.5 Sonet' },
	{ value: 'Claude 3 Opus' },
];

function PromptRightSidebarTabs(): React.ReactElement {
	const promptContext = usePrompt();
	const [activeTab, setActiveTab] = useState("tab1");
	// const [showVersionsDropdown, setShowVersionsDropdown] = useState(false);
	// const [activeItem, setActiveItem] = useState('');


	function handleModelChange(value: string): void {
		console.log("Model changed:", value);
	}


	return (
		<div className={`card ${promptContext.isRightColPromptInputsColExpanded ? 'hidden' : 'flex'} flex-1 bg-white rounded-xl`}>
			<div className="tabs-wrapper flex flex-col w-full">
				<div className="tabs flex my-1 ml-1 text-xs text-gray-500 font-medium rounded-md h-[48px]">
					<div className="tabs-inner p-1 flex flex-1">
						<button type="button" className={`tab rounded-sm p-2 flex-1${activeTab === 'tab1' ? ' tab-active text-orange-500 bg-white' : ''}`} onClick={() => { setActiveTab("tab1"); }}>
							Output
						</button>
						<button type="button" className={`tab rounded-sm p-2 flex-1${activeTab === 'tab2' ? ' tab-active text-orange-500 bg-white' : ''}`} onClick={() => { setActiveTab("tab2"); }}>
							Generated Prompt
						</button>
					</div>
					<PromptRightColToggleVisilityStatus isColExpanded={promptContext.isRightColOutputColExpanded} toggleColStatus={promptContext.setIsRightColOutputColExpanded} />
				</div>
				<div className="tab-panels flex flex-1 text-sm w-full rounded-b-xl overflow-auto">
					{activeTab === "tab1" && (
						<div className="tab-panel flex flex-col flex-grow">
							<div className="tab-content p-4 flex flex-col flex-grow items-start gap-2">

								{!promptContext.isEngineerPage ? undefined :
									<CommonSelect
										className="common-select-green"
										defaultValue="GPT4o-Mini"
										options={models}
										onSelectedValueChange={handleModelChange}
									/>
								}

								<ParsersManager display="output"/>

							</div>

							{/* <div className="details pt-4 mt-auto">
								<select className="select w-full" name="" id="">
									<option value="details">Details</option>
									<option value="option2">Option 2</option>
									<option value="option3">Option 3</option>
									<option value="option4">Option 4</option>
								</select>
							</div> */}
						</div>
					)}
					{activeTab === "tab2" && (
						<div className="tab-panel flex-col flex-grow">
							<div className="tab-content p-4 flex flex-col flex-grow items-start gap-2">
								
								<ParsersManager display="prompt"/>

								<pre className="whitespace-pre-wrap break-words text-sm font-sans">
									{promptContext.output?.prompt}
								</pre>
							</div>
						</div>
					)}
				</div>
			</div>
		</div>
	)
}
export default PromptRightSidebarTabs;