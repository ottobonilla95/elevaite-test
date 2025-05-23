import React from "react";
import "./PromptAccordion.scss";

interface PromptAccordionProps {
	title: string;
	text: string;
	active: boolean;
}

const PromptAccordion = ({ title, text, active } : PromptAccordionProps): JSX.Element => {
	const [isOpen, setIsOpen] = React.useState(!!active);
	return (
		<div className="accordion rounded-xl bg-white mb-4">
			<div className="accordion-title flex items-center justify-between">
				<button className="flex flex-1 items-center gap-2 p-4" onClick={() => setIsOpen(!isOpen)}>
					<span className="text-sm font-medium">{title}</span>
					<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
						<g opacity="0.8">
							<path d="M4 6L8 10L12 6" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
						</g>
					</svg>
				</button>
				<div className="flex gap-2 items-center p-4">
					<div className="tag">AI Assist</div>
					<button className="btn-remove-accordion">
						<svg width="17" height="16" viewBox="0 0 17 16" fill="none" xmlns="http://www.w3.org/2000/svg">
							<g opacity="0.8">
								<path d="M11.1667 4.00004V3.46671C11.1667 2.71997 11.1667 2.3466 11.0213 2.06139C10.8935 1.8105 10.6895 1.60653 10.4387 1.4787C10.1534 1.33337 9.78007 1.33337 9.03333 1.33337H7.96667C7.21993 1.33337 6.84656 1.33337 6.56135 1.4787C6.31046 1.60653 6.10649 1.8105 5.97866 2.06139C5.83333 2.3466 5.83333 2.71997 5.83333 3.46671V4.00004M7.16667 7.66671V11M9.83333 7.66671V11M2.5 4.00004H14.5M13.1667 4.00004V11.4667C13.1667 12.5868 13.1667 13.1469 12.9487 13.5747C12.7569 13.951 12.451 14.257 12.0746 14.4487C11.6468 14.6667 11.0868 14.6667 9.96667 14.6667H7.03333C5.91323 14.6667 5.35318 14.6667 4.92535 14.4487C4.54903 14.257 4.24307 13.951 4.05132 13.5747C3.83333 13.1469 3.83333 12.5868 3.83333 11.4667V4.00004" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</g>
						</svg>
					</button>
				</div>
			</div>
			{isOpen && (
				<div className="accordion-content text-sm p-4">
					{text}
				</div>
			)}
		</div>
	)
}

export default PromptAccordion