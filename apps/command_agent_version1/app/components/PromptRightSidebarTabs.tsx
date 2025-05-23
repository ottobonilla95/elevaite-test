import { useState } from "react";

const PromptRightSidebarTabs = () => {
	const [activeTab, setActiveTab] = useState("tab1");

	return (
		<div className="card flex flex-1 bg-white rounded-xl">
			<div className="tabs-wrapper flex flex-col w-full">
				<div className="tabs flex m-1 p-1 text-xs text-gray-500 font-medium rounded-md">
					<button className={`tab rounded-sm p-2 flex-1${ 'tab1' == activeTab ? ' tab-active text-orange-500 bg-white' : '' }`} onClick={() => setActiveTab("tab1")}>
						Output
					</button>
					<button className={`tab rounded-sm p-2 flex-1${ 'tab2' == activeTab ? ' tab-active text-orange-500 bg-white' : '' }`} onClick={() => setActiveTab("tab2")}>
						Generated Prompt
					</button>
				</div>
				<div className="tab-panels flex flex-1 text-sm p-4 mt-1 w-full rounded-xl">
					{activeTab === "tab1" && (
						<div className="tab-panel flex flex-col">
							<div className="tab-content">
								Platea amet vulputate augue aenean vel. Sed lorem phasellus consectetur feugiat. Lobortis hac viverra mollis quis amet lacus pulvinar vitae. Sodales vitae vestibulum quis nascetur pellentesque.
							</div>

							<div className="details pt-4 mt-auto">
								<select className="select w-full" name="" id="">
									<option value="details">Details</option>
									<option value="option2">Option 2</option>
									<option value="option3">Option 3</option>
									<option value="option4">Option 4</option>
								</select>
							</div>
						</div>
					)}
					{activeTab === "tab2" && (
						<div className="tab-panel">
							Another Content here
						</div>
					)}
				</div>
			</div>
		</div>
	)
}
export default PromptRightSidebarTabs;