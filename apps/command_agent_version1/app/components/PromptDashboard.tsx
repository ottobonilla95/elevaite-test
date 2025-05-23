import "./PromptDashboard.scss";
import PromptLeftSidebar from "./PromptLeftSidebar";
import PromptRightSidebar from "./PromptRightSidebar";

const PromptDashboard = () => {
  return (
	<div className="prompt-dashboard p-4 gap-4 flex w-full">
		<PromptLeftSidebar />
		<PromptRightSidebar />
	</div>
  )
}

export default PromptDashboard;