import { Expand, Minimize } from "lucide-react";

interface PromptRightColToggleVisilityStatusProps {
	isColExpanded: boolean;
	toggleColStatus: (isExpanded: boolean) => void
}

const PromptRightColToggleVisilityStatus = ({ isColExpanded, toggleColStatus }: PromptRightColToggleVisilityStatusProps): JSX.Element => {
	return (
		<div className="w-[48px] flex items-center justify-center bg-white rounded-xl">
			<button type="button" onClick={() => { toggleColStatus(!isColExpanded); }}>
				{isColExpanded ? <Minimize size={17} /> : <Expand size={17} />}
			</button>
		</div>
	)
}
export default PromptRightColToggleVisilityStatus