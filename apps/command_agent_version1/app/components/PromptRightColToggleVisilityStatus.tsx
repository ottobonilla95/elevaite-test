interface PromptRightColToggleVisilityStatusProps {
	isColExpanded: boolean;
	toggleColStatus: (isExpanded: boolean) => void
}

const PromptRightColToggleVisilityStatus = ({isColExpanded, toggleColStatus}: PromptRightColToggleVisilityStatusProps): JSX.Element => {
  return (
	<div className="w-[48px] flex items-center justify-center bg-white rounded-xl">
		<button onClick={() => toggleColStatus(!isColExpanded)}>
			{isColExpanded ? (
				<svg width="17" height="48" viewBox="0 0 17 48" fill="none" xmlns="http://www.w3.org/2000/svg">
					<path d="M2.83333 25.4167H7.08333M7.08333 25.4167V29.6667M7.08333 25.4167L2.125 30.375M14.1667 22.5833H9.91667M9.91667 22.5833V18.3333M9.91667 22.5833L14.875 17.625" stroke="#4D4D50" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
				</svg>
			) : (
				<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
					<g opacity="0.8">
						<path d="M10.6667 5.33333L14 2M14 2H10.6667M14 2V5.33333M5.33333 5.33333L2 2M2 2L2 5.33333M2 2L5.33333 2M5.33333 10.6667L2 14M2 14H5.33333M2 14L2 10.6667M10.6667 10.6667L14 14M14 14V10.6667M14 14H10.6667" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</g>
				</svg>
			)}
		</button>
	</div>
  )
}
export default PromptRightColToggleVisilityStatus