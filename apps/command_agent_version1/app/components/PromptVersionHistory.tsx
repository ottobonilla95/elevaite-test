import { useState } from "react";

const Version =  () => (
	<div className="px-4 py-3 rounded-xl mt-2" style={{ border: "1px solid #E2E8ED" }}>
		<div className="font-medium">Mar 20, 9:24 AM</div>
		<div className="flex items-center gap-2 mt-2">
			<div className="w-[24px] h-[24px] rounded-full bg-[#6C8271]"></div>
			<div className="font-medium text-sm text-gray-500">Anjali Rahmed</div>
		</div>
	</div>
);

const PromptVersionHistory = () => {
	const [showAllVersions, setShowAllVersions] = useState(false);

	const toggleShowAllVersions = () => {
		setShowAllVersions(!showAllVersions);
	};

	const style = showAllVersions ? { transform: "translateY(12px) rotate(180deg)" } : { transform: "translateY(12px)" };

  return (
	<div className="version-history py-4 w-full">
		<div className="flex gap-5">
			<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg" style={{transform: "translateY(12px)"}}>
				<rect width="32" height="32" rx="16" fill="#FF681F"/>
				<g opacity="0.8">
					<path d="M16 26C21.5228 26 26 21.5228 26 16C26 10.4772 21.5228 6 16 6C10.4772 6 6 10.4772 6 16C6 21.5228 10.4772 26 16 26Z" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					<path d="M12 13.6C12 13.0399 12 12.7599 12.109 12.546C12.2049 12.3578 12.3578 12.2049 12.546 12.109C12.7599 12 13.0399 12 13.6 12H18.4C18.9601 12 19.2401 12 19.454 12.109C19.6422 12.2049 19.7951 12.3578 19.891 12.546C20 12.7599 20 13.0399 20 13.6V18.4C20 18.9601 20 19.2401 19.891 19.454C19.7951 19.6422 19.6422 19.7951 19.454 19.891C19.2401 20 18.9601 20 18.4 20H13.6C13.0399 20 12.7599 20 12.546 19.891C12.3578 19.7951 12.2049 19.6422 12.109 19.454C12 19.2401 12 18.9601 12 18.4V13.6Z" stroke="white" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
				</g>
			</svg>
			<div className="card-wrapper relative">
				<div className="flex-1 font-medium text-[#FF681F] bg-[#F9FAFB] rounded-xl p-4">Current Version</div>
				<div className="card p-4 rounded-xl mt-2">
					<div className="flex items-center justify-between">
						<div className="flex items-center gap-2">
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
								<g opacity="0.64">
									<path d="M10.3333 4.00033C10.7015 4.00033 11 3.70185 11 3.33366C11 2.96547 10.7015 2.66699 10.3333 2.66699C9.96514 2.66699 9.66667 2.96547 9.66667 3.33366C9.66667 3.70185 9.96514 4.00033 10.3333 4.00033Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
									<path d="M10.3333 8.66699C10.7015 8.66699 11 8.36851 11 8.00033C11 7.63214 10.7015 7.33366 10.3333 7.33366C9.96514 7.33366 9.66667 7.63214 9.66667 8.00033C9.66667 8.36851 9.96514 8.66699 10.3333 8.66699Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
									<path d="M10.3333 13.3337C10.7015 13.3337 11 13.0352 11 12.667C11 12.2988 10.7015 12.0003 10.3333 12.0003C9.96514 12.0003 9.66667 12.2988 9.66667 12.667C9.66667 13.0352 9.96514 13.3337 10.3333 13.3337Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
									<path d="M5.66667 4.00033C6.03486 4.00033 6.33333 3.70185 6.33333 3.33366C6.33333 2.96547 6.03486 2.66699 5.66667 2.66699C5.29848 2.66699 5 2.96547 5 3.33366C5 3.70185 5.29848 4.00033 5.66667 4.00033Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
									<path d="M5.66667 8.66699C6.03486 8.66699 6.33333 8.36851 6.33333 8.00033C6.33333 7.63214 6.03486 7.33366 5.66667 7.33366C5.29848 7.33366 5 7.63214 5 8.00033C5 8.36851 5.29848 8.66699 5.66667 8.66699Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
									<path d="M5.66667 13.3337C6.03486 13.3337 6.33333 13.0352 6.33333 12.667C6.33333 12.2988 6.03486 12.0003 5.66667 12.0003C5.29848 12.0003 5 12.2988 5 12.667C5 13.0352 5.29848 13.3337 5.66667 13.3337Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
								</g>
							</svg>
							<div className="font-medium">PROMPT A - V2</div>
						</div>

						<button>
							<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
								<g opacity="0.8">
									<path d="M8.00016 8.66699C8.36835 8.66699 8.66683 8.36851 8.66683 8.00033C8.66683 7.63214 8.36835 7.33366 8.00016 7.33366C7.63197 7.33366 7.3335 7.63214 7.3335 8.00033C7.3335 8.36851 7.63197 8.66699 8.00016 8.66699Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
									<path d="M8.00016 4.00033C8.36835 4.00033 8.66683 3.70185 8.66683 3.33366C8.66683 2.96547 8.36835 2.66699 8.00016 2.66699C7.63197 2.66699 7.3335 2.96547 7.3335 3.33366C7.3335 3.70185 7.63197 4.00033 8.00016 4.00033Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
									<path d="M8.00016 13.3337C8.36835 13.3337 8.66683 13.0352 8.66683 12.667C8.66683 12.2988 8.36835 12.0003 8.00016 12.0003C7.63197 12.0003 7.3335 12.2988 7.3335 12.667C7.3335 13.0352 7.63197 13.3337 8.00016 13.3337Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
								</g>
							</svg>
						</button>
					</div>

					<hr className="my-4" />

					<div className="tags gap-2 flex flex-wrap">
						<div className="tag">GPT-4o</div>
						<div className="tag">Chat 4.50</div>
						<div className="tag">4.0 Mini</div>
					</div>

					<hr className="my-4" />

					<div className="tags gap-2 flex flex-wrap">
						<div className="tag">Max Tokens: 2500</div>
						<div className="tag">Temp: 56</div>
						<div className="tag">Hosted</div>
						<div className="tag">JSON</div>
					</div>
					<div className="mt-2 text-xs italic text-[#8494AD] flex justify-end">
						Created: March 26, <div className="separator"></div>2025
					</div>
				</div>
			</div>
		</div>

		<div className="flex gap-5 mt-4">
			<div className="w-[32px] h-[32px]">
				<button className="flex transition" onClick={toggleShowAllVersions} style={style}>
					<svg width="32" height="32" viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
						<rect width="32" height="32" rx="16" fill="#E2E8ED"/>
						<g opacity="0.8">
							<path d="M10 19L16 13L22 19" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
						</g>
					</svg>
				</button>
			</div>
			<div className="w-full">
				<div className="flex-1 font-medium bg-[#F9FAFB] rounded-xl p-4">4 autosave versions</div>
				{showAllVersions && (
					<div>
						<Version />
						<Version />
						<Version />
						<Version />
					</div>
				)}
			</div>
		</div>

	</div>
  )
}
export default PromptVersionHistory