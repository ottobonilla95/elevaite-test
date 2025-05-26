import React from 'react';
import Image from 'next/image';
import { usePrompt } from '../ui/contexts/PromptContext';

const PromptRightSidebarTestingConsole = () => {
	const promptsContext = usePrompt();
	const [activeClass, setIsActiveClass] = React.useState('');

	const handleHalfExpanded = () => {
		if (activeClass === 'half-expanded' || activeClass === 'full-expanded')  {
			setIsActiveClass('');
		} else {
			setIsActiveClass('half-expanded');
		}
	}

	const handleFullExpanded = () => {
		if (activeClass === 'half-expanded' || activeClass === '')  {
			setIsActiveClass('full-expanded');
		} else {
			setIsActiveClass('');
		}
	}

	function handleFileUpload() {
		promptsContext.goToNextPage();
	}

	return (
		<div className={`bottom testing-console ${activeClass} w-full rounded-b-xl ${activeClass ? 'overflow-y-auto' : 'overflow-hidden'}`}>
			<div className="p-4 flex items-center justify-between">
				<div className="font-medium">Testing Console</div>
				<div className="flex gap-4 items-center">
					<button onClick={handleFileUpload}>
						<svg width="17" height="16" viewBox="0 0 17 16" fill="none" xmlns="http://www.w3.org/2000/svg">
							<g opacity="0.8">
								<path d="M14.4018 7.26622L8.39138 13.2766C7.02454 14.6435 4.80847 14.6435 3.44163 13.2766C2.0748 11.9098 2.0748 9.69372 3.44163 8.32688L9.45204 2.31647C10.3633 1.40525 11.8406 1.40525 12.7519 2.31647C13.6631 3.2277 13.6631 4.70508 12.7519 5.61631L6.97716 11.391C6.52155 11.8466 5.78286 11.8466 5.32725 11.391C4.87164 10.9354 4.87164 10.1967 5.32725 9.74109L10.3948 4.6735" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</g>
						</svg>
					</button>
					<button onClick={handleHalfExpanded}>
						<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
							<path d="M2.7002 12.3998H17.1002M6.5402 2.7998H13.2602C14.6043 2.7998 15.2764 2.7998 15.7898 3.06139C16.2414 3.29149 16.6085 3.65864 16.8386 4.11023C17.1002 4.62362 17.1002 5.29568 17.1002 6.6398V13.3598C17.1002 14.7039 17.1002 15.376 16.8386 15.8894C16.6085 16.341 16.2414 16.7081 15.7898 16.9382C15.2764 17.1998 14.6043 17.1998 13.2602 17.1998H6.54019C5.19607 17.1998 4.52401 17.1998 4.01062 16.9382C3.55903 16.7081 3.19188 16.341 2.96178 15.8894C2.7002 15.376 2.7002 14.7039 2.7002 13.3598V6.6398C2.7002 5.29568 2.7002 4.62362 2.96178 4.11023C3.19188 3.65864 3.55903 3.29149 4.01062 3.06139C4.52401 2.7998 5.19607 2.7998 6.5402 2.7998Z" stroke="#4D4D50" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"/>
						</svg>
					</button>
					<button onClick={handleFullExpanded}>
						{activeClass === 'full-expanded' ? (
							<svg width="18" height="18" viewBox="0 0 18 18" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M3.33333 10.4167H7.58333M7.58333 10.4167V14.6667M7.58333 10.4167L2.625 15.375M14.6667 7.58333H10.4167M10.4167 7.58333V3.33333M10.4167 7.58333L15.375 2.625" stroke="#4D4D50" stroke-width="1.4" stroke-linecap="round" stroke-linejoin="round"/>
							</svg>

						) : (
							<svg width="17" height="16" viewBox="0 0 17 16" fill="none" xmlns="http://www.w3.org/2000/svg">
								<g opacity="0.8">
									<path d="M11.1667 5.33333L14.5 2M14.5 2H11.1667M14.5 2V5.33333M5.83333 5.33333L2.5 2M2.5 2L2.5 5.33333M2.5 2L5.83333 2M5.83333 10.6667L2.5 14M2.5 14H5.83333M2.5 14L2.5 10.6667M11.1667 10.6667L14.5 14M14.5 14V10.6667M14.5 14H11.1667" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
								</g>
							</svg>
						)}
					</button>
				</div>
			</div>
			<div className="tab-links-wrapper">
				<div className="tab-links px-4 flex gap-2">
					<button className="active py-3 px-4 font-medium text-sm">Input 1</button>
					<button className="py-3 px-4 font-medium text-sm flex items-center gap-2">
						<svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
							<g opacity="0.56">
								<path d="M7.99992 3.83325V13.1666M3.33325 8.49992H12.6666" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</g>
						</svg>
						Add Input
					</button>
				</div>
				<div className="tab-link-panels overflow-y-auto">
					<div className="tab-link-panel">
						<div className="flex items-center justify-between p-4" style={{borderBottom: "1px solid #E2E8ED"}}>
							<div className="flex items-center text-sm font-medium gap-2" style={{ color: "#0000F9"}}>
								<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
									<g opacity="0.8">
										<path d="M14.1015 7.26634L8.09108 13.2768C6.72425 14.6436 4.50817 14.6436 3.14134 13.2768C1.7745 11.9099 1.7745 9.69384 3.14134 8.327L9.15174 2.3166C10.063 1.40537 11.5404 1.40537 12.4516 2.3166C13.3628 3.22782 13.3628 4.7052 12.4516 5.61643L6.67687 11.3911C6.22126 11.8467 5.48257 11.8467 5.02695 11.3911C4.57134 10.9355 4.57134 10.1968 5.02695 9.74122L10.0946 4.67362" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
									</g>
								</svg>
								invoice.pdf
							</div>
							<div className="text-sm font-medium" style={{color: '#97A3B6'}}>272.9 KB</div>
						</div>
						<div className="p-4">
							<div className="flex justify-between items-center">
								<div className="font-medium text-sm" style={{color: '#97A3B6'}}>Preview</div>
								<button onClick={() => setIsActiveClass('')}>
									<svg width="21" height="21" viewBox="0 0 21 21" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M15.5 5.5L5.5 15.5M5.5 5.5L15.5 15.5" stroke="#97A3B6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
									</svg>
								</button>
							</div>
							<div className="my-4">
								<Image className="m-auto" src="/invoice.jpg" alt="preview" width={375} height={553}/>
							</div>
							<div className="flex items-center justify-between">
								<div className="text-sm text-gray-500">Page 1 of 20</div>
								<div className="flex items-center gap-2">
									<button className="btn btn-outline gray flex items-center gap-2">
										<svg width="6" height="10" viewBox="0 0 6 10" fill="none" xmlns="http://www.w3.org/2000/svg">
											<path d="M4.44971 8.5L0.949707 5L4.44971 1.5" stroke="#4A5567" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
										</svg>
										Back
									</button>
									<button className="btn btn-outline gray flex items-center gap-2">
										Next
										<svg width="6" height="10" viewBox="0 0 6 10" fill="none" xmlns="http://www.w3.org/2000/svg">
											<path d="M0.949707 8.5L4.44971 5L0.949707 1.5" stroke="#4A5567" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round"/>
										</svg>
									</button>
								</div>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	)
}
export default PromptRightSidebarTestingConsole;