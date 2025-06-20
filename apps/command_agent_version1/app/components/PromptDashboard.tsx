import { usePrompt } from "../ui/contexts/PromptContext";
import "./PromptDashboard.scss";
import PromptLeftSidebar from "./PromptLeftSidebar";
import PromptRightSidebar from "./PromptRightSidebar";
import PromptRightSidebarEngineer from "./PromptRightSidebarEngineer";

const PromptDashboard = () => {
  const promptContext = usePrompt();
  return (
	<div className="prompt-dashboard p-4 gap-4 flex w-full">
		<PromptLeftSidebar />
		{promptContext.isEngineerPage ? (
			<PromptRightSidebarEngineer />
		) : (
			<PromptRightSidebar />
		)}
	</div>
  )
}

export default PromptDashboard;