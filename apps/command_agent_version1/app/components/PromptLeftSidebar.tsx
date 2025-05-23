import { useState } from "react";

const PromptLeftSidebar = () => {
  	const [activeTab, setActiveTab] = useState("tab1");
	const [sidebarOpen, setSidebarOpen] = useState(true);

	return (
		<div className={`prompt-col prompt-left p-2 flex flex-col rounded-2xl bg-white overflow-y-auto${!sidebarOpen ? ' shrinked' : ''}`}>
			<div className="tabs-wrapper flex items-center justify-between">
				<div className="tabs flex m-1 p-1 text-xs text-gray-500 font-medium rounded-lg whitespace-nowrap">
					<button className={`tab rounded-sm px-4 py-1 flex-1${ 'tab1' == activeTab ? ' tab-active text-orange-500 bg-white' : '' }`} onClick={() => setActiveTab("tab1")}>
						Prompts
					</button>
					<button className={`tab rounded-sm px-4 py-1 flex-1${ 'tab2' == activeTab ? ' tab-active text-orange-500 bg-white' : '' }`} onClick={() => setActiveTab("tab2")}>
						Version History
					</button>
				</div>

				<button type="button" onClick={() => setSidebarOpen(!sidebarOpen)}>
					{
					sidebarOpen
					?
					<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
						<g opacity="0.8">
							<path d="M18 17L13 12L18 7M11 17L6 12L11 7" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
						</g>
					</svg>
					:
					<svg width="14" height="12" viewBox="0 0 14 12" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M1 11L6 6L1 1M8 11L13 6L8 1" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
					}
				</button>
			</div>
			<div className="tab-panels px-4 rounded-lg mt-2 flex-1">
				{activeTab === "tab1" && (
					<div className="tab-panel">
						<div className="part py-4">
							<div className="actions-wrapper flex items-center justify-between">
								<div className="flex gap-2 font-medium items-center">
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
										<g opacity="0.64">
											<path d="M10.3333 3.99996C10.7015 3.99996 11 3.70148 11 3.33329C11 2.9651 10.7015 2.66663 10.3333 2.66663C9.96514 2.66663 9.66667 2.9651 9.66667 3.33329C9.66667 3.70148 9.96514 3.99996 10.3333 3.99996Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
											<path d="M10.3333 8.66663C10.7015 8.66663 11 8.36815 11 7.99996C11 7.63177 10.7015 7.33329 10.3333 7.33329C9.96514 7.33329 9.66667 7.63177 9.66667 7.99996C9.66667 8.36815 9.96514 8.66663 10.3333 8.66663Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
											<path d="M10.3333 13.3333C10.7015 13.3333 11 13.0348 11 12.6666C11 12.2984 10.7015 12 10.3333 12C9.96514 12 9.66667 12.2984 9.66667 12.6666C9.66667 13.0348 9.96514 13.3333 10.3333 13.3333Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
											<path d="M5.66667 3.99996C6.03486 3.99996 6.33333 3.70148 6.33333 3.33329C6.33333 2.9651 6.03486 2.66663 5.66667 2.66663C5.29848 2.66663 5 2.9651 5 3.33329C5 3.70148 5.29848 3.99996 5.66667 3.99996Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
											<path d="M5.66667 8.66663C6.03486 8.66663 6.33333 8.36815 6.33333 7.99996C6.33333 7.63177 6.03486 7.33329 5.66667 7.33329C5.29848 7.33329 5 7.63177 5 7.99996C5 8.36815 5.29848 8.66663 5.66667 8.66663Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
											<path d="M5.66667 13.3333C6.03486 13.3333 6.33333 13.0348 6.33333 12.6666C6.33333 12.2984 6.03486 12 5.66667 12C5.29848 12 5 12.2984 5 12.6666C5 13.0348 5.29848 13.3333 5.66667 13.3333Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
										</g>
									</svg>
									Invoice Extractor
								</div>

								<div className="flex items-center gap-3">
									<button>
										<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
											<path d="M16.4001 17H6.60012C6.26875 17 6.00012 16.7314 6.00012 16.4001V6.60012C6.00012 6.26875 6.26875 6.00012 6.60012 6.00012H16.4001C16.7314 6.00012 17 6.26875 17 6.60012V16.4001C17 16.7314 16.7314 17 16.4001 17Z" stroke="#4D4D50" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
											<path d="M11.9999 5.99997V1.6C11.9999 1.26863 11.7313 1 11.3999 1H1.6C1.26863 1 1 1.26863 1 1.6V11.3999C1 11.7313 1.26863 11.9999 1.6 11.9999H5.99997" stroke="#4D4D50" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
										</svg>
									</button>
									<button>
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
											<g opacity="0.8" clip-path="url(#clip0_1120_5351)">
												<path d="M14 14H8.66664M1.66663 14.3334L5.36614 12.9105C5.60277 12.8195 5.72108 12.774 5.83177 12.7146C5.93009 12.6618 6.02383 12.6009 6.11199 12.5324C6.21124 12.4554 6.30088 12.3658 6.48015 12.1865L14 4.66671C14.7364 3.93033 14.7364 2.73642 14 2.00004C13.2636 1.26366 12.0697 1.26366 11.3333 2.00004L3.81348 9.51985C3.63421 9.69912 3.54457 9.78876 3.46755 9.88801C3.39914 9.97617 3.33823 10.0699 3.28545 10.1682C3.22603 10.2789 3.18053 10.3972 3.08951 10.6339L1.66663 14.3334ZM1.66663 14.3334L3.03871 10.766C3.13689 10.5107 3.18598 10.3831 3.27019 10.3246C3.34377 10.2735 3.43483 10.2542 3.52282 10.271C3.62351 10.2902 3.72021 10.3869 3.91361 10.5803L5.41967 12.0864C5.61307 12.2798 5.70977 12.3765 5.729 12.4772C5.74581 12.5652 5.72648 12.6562 5.67539 12.7298C5.61692 12.814 5.48928 12.8631 5.23401 12.9613L1.66663 14.3334Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
											</g>
											<defs>
												<clipPath id="clip0_1120_5351">
													<rect width="16" height="16" fill="white"/>
												</clipPath>
											</defs>
										</svg>
									</button>
									<button>
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
											<g opacity="0.8">
												<path d="M10.6667 4.00004V3.46671C10.6667 2.71997 10.6667 2.3466 10.5213 2.06139C10.3935 1.8105 10.1895 1.60653 9.93865 1.4787C9.65344 1.33337 9.28007 1.33337 8.53333 1.33337H7.46667C6.71993 1.33337 6.34656 1.33337 6.06135 1.4787C5.81046 1.60653 5.60649 1.8105 5.47866 2.06139C5.33333 2.3466 5.33333 2.71997 5.33333 3.46671V4.00004M6.66667 7.66671V11M9.33333 7.66671V11M2 4.00004H14M12.6667 4.00004V11.4667C12.6667 12.5868 12.6667 13.1469 12.4487 13.5747C12.2569 13.951 11.951 14.257 11.5746 14.4487C11.1468 14.6667 10.5868 14.6667 9.46667 14.6667H6.53333C5.41323 14.6667 4.85318 14.6667 4.42535 14.4487C4.04903 14.257 3.74307 13.951 3.55132 13.5747C3.33333 13.1469 3.33333 12.5868 3.33333 11.4667V4.00004" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
											</g>
										</svg>
									</button>
									<button>
										<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
											<g opacity="0.8">
												<path d="M8.00004 8.66663C8.36823 8.66663 8.66671 8.36815 8.66671 7.99996C8.66671 7.63177 8.36823 7.33329 8.00004 7.33329C7.63185 7.33329 7.33337 7.63177 7.33337 7.99996C7.33337 8.36815 7.63185 8.66663 8.00004 8.66663Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
												<path d="M8.00004 3.99996C8.36823 3.99996 8.66671 3.70148 8.66671 3.33329C8.66671 2.9651 8.36823 2.66663 8.00004 2.66663C7.63185 2.66663 7.33337 2.9651 7.33337 3.33329C7.33337 3.70148 7.63185 3.99996 8.00004 3.99996Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
												<path d="M8.00004 13.3333C8.36823 13.3333 8.66671 13.0348 8.66671 12.6666C8.66671 12.2984 8.36823 12 8.00004 12C7.63185 12 7.33337 12.2984 7.33337 12.6666C7.33337 13.0348 7.63185 13.3333 8.00004 13.3333Z" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
											</g>
										</svg>
									</button>
								</div>
							</div>
							<div className="my-4">
								Extracts informetion from documents such as invoice, CSOWs, etc.
							</div>
							<div className="tags flex flex-wrap gap-3">
								<div className="tag">Extraction</div>
								<div className="tag">Single Prompt</div>
							</div>
						</div>
						<div className="part py-4">
							<div className="text-xs font-medium mb-3">Model</div>
							<div className="tags flex flex-wrap gap-3">
								<div className="tag">GPT-4o</div>
							</div>
						</div>
						<div className="part py-4">
							<div className="text-xs font-medium mb-3">Parameters</div>
							<div className="tags flex flex-wrap gap-3">
								<div className="tag">Max Tokens: 2,500</div>
								<div className="tag">Temp: 56</div>
								<div className="tag">Hosted</div>
								<div className="tag">JSON</div>
							</div>
						</div>

					</div>
				)}
				{activeTab === "tab2" && (
					<div className="tab-panel">
						<div className="part py-4">Content</div>
					</div>
				)}
			</div>
		</div>
	)
}
export default PromptLeftSidebar