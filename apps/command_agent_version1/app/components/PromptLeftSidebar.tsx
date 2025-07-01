import { useState } from "react";
import { usePrompt } from "../ui/contexts/PromptContext";
import PromptForm from "./PromptNewForm";
import PromptNewForm from "./PromptNewForm";
import PromptVersionHistory from "./PromptVersionHistory";

const PromptLeftSidebar = () => {
	const promptContext = usePrompt();
	const [activeTab, setActiveTab] = useState("tab1");

	return (
		<div className={`prompt-col prompt-left p-2 flex-col rounded-2xl bg-white overflow-y-auto${promptContext.isRightColExpanded ? ' hidden' : ' flex'}`}>
			<div className="tabs-wrapper flex items-center justify-between">
				<div className="tabs flex m-1 p-1 text-xs text-gray-500 font-medium rounded-lg whitespace-nowrap bg-[#F1F4F8]" style={{ border: "1px solid #E6EBF0" }}>
					<button className={`tab rounded-sm px-4 py-1 flex-1${'tab1' === activeTab ? ' tab-active text-orange-500 bg-white' : ''}`} onClick={() => setActiveTab("tab1")}>
						Prompt
					</button>
					<button className={`tab rounded-sm px-4 py-1 flex-1${'tab2' === activeTab ? ' tab-active text-orange-500 bg-white' : ''}`} onClick={() => setActiveTab("tab2")}>
						Version History
					</button>
				</div>
			</div>
			<div className="tab-panels px-4 rounded-lg mt-2 flex-1 flex">
				{activeTab === "tab1" && (
					<div className="tab-panel flex flex-1 w-full">
						<PromptNewForm />
					</div>
				)}
				{activeTab === "tab2" && (
					<div className="tab-panel flex flex-1 w-full">
						<PromptVersionHistory />
					</div>
				)}
			</div>
		</div>
	)
}
export default PromptLeftSidebar