import { useState } from "react";
import { LoadingKeys, usePrompt } from "../ui/contexts/PromptContext";
import PromptLoading from "./PromptLoading";
import PromptRightColToggleVisilityStatus from "./PromptRightColToggleVisilityStatus";
import { CommonSelect, CommonSelectOption } from "@repo/ui/components";

const models: CommonSelectOption[] = [
	{ value: 'GPT4o-Mini' },
	{ value: 'GPT 4 Turbo' },
	{ value: 'Claude 3.5 Sonet' },
	{ value: 'Claude 3 Opus' },
];

const PromptRightSidebarTabs = () => {
	const promptContext = usePrompt();
	const [activeTab, setActiveTab] = useState("tab1");
	const [showVersionsDropdown, setShowVersionsDropdown] = useState(false);
	const [activeItem, setActiveItem] = useState('');

	return (
		<div className={`card ${promptContext.isRightColPromptInputsColExpanded ? 'hidden' : 'flex'} flex-1 bg-white rounded-xl`}>
			<div className="tabs-wrapper flex flex-col w-full">
				<div className="tabs flex my-1 ml-1 text-xs text-gray-500 font-medium rounded-md h-[48px]">
					<div className="tabs-inner p-1 flex flex-1">
						<button className={`tab rounded-sm p-2 flex-1${'tab1' === activeTab ? ' tab-active text-orange-500 bg-white' : ''}`} onClick={() => setActiveTab("tab1")}>
							Output
						</button>
						<button className={`tab rounded-sm p-2 flex-1${'tab2' === activeTab ? ' tab-active text-orange-500 bg-white' : ''}`} onClick={() => setActiveTab("tab2")}>
							Generated Prompt
						</button>
					</div>
					<PromptRightColToggleVisilityStatus isColExpanded={promptContext.isRightColOutputColExpanded} toggleColStatus={promptContext.setIsRightColOutputColExpanded} />
				</div>
				<div className="tab-panels flex flex-1 text-sm w-full rounded-b-xl overflow-auto">
					{activeTab === "tab1" && (
						<div className="tab-panel flex flex-col flex-grow">
							<div className="tab-content p-4">

								<CommonSelect
									className="common-select-green"
									defaultValue="GPT4o-Mini"
									options={models}
									onSelectedValueChange={(value) => console.log(value)}
								/>

								{promptContext.output && (
									<div className="flex items-center gap-2 mb-4">
										<label className="flex items-center gap-2" htmlFor="json">
											<input id="json" type="checkbox" onChange={promptContext.turnToJSON} />
											JSON
										</label>
										{promptContext.loading[LoadingKeys.ConvertingToJSON] && (
											<PromptLoading className="no-offset m-0" width={20} height={20} />
										)}
									</div>
								)}

								<pre className="whitespace-pre-wrap break-words mb-4 text-sm font-sans">
									{promptContext.jsonOutput}
									{!promptContext.jsonOutput && JSON.stringify(promptContext.output?.result)}
								</pre>
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
							<div className="tab-content p-4">

								{promptContext.outputVersions.length > 0 && promptContext.outputVersions && (
									<div className="flex justify-end">
										<div className="dropdown-wrapper relative">
											<button onClick={() => setShowVersionsDropdown(!showVersionsDropdown)}>
												<svg width="17" height="17" viewBox="0 0 17 17" fill="none" xmlns="http://www.w3.org/2000/svg">
													<g clipPath="url(#clip0_1492_7596)">
														<path d="M8.59991 4.1999V8.3999L11.3999 9.7999M15.5999 8.3999C15.5999 12.2659 12.4659 15.3999 8.59991 15.3999C4.73392 15.3999 1.59991 12.2659 1.59991 8.3999C1.59991 4.53391 4.73392 1.3999 8.59991 1.3999C12.4659 1.3999 15.5999 4.53391 15.5999 8.3999Z" stroke="#6C8271" strokeWidth="1.4" stroke-linecap="round" stroke-linejoin="round" />
													</g>
													<defs>
														<clipPath id="clip0_1492_7596">
															<rect width="16.8" height="16.8" fill="white" transform="translate(0.200012)" />
														</clipPath>
													</defs>
												</svg>
											</button>
											{showVersionsDropdown && (
												<div className="dropdown absolute">
													{promptContext.outputVersions.map((version) => (
														<button className={activeItem === version.id ? "active" : ""} key={version.id} onClick={() => {
															setActiveItem(String(version.id));
															setShowVersionsDropdown(false);
															promptContext.setJsonOutput('');
															promptContext.setOutput(version);
														}}>{version.id}</button>
													))}
												</div>
											)}
										</div>
									</div>
								)}

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