import { useRef, useState, useEffect } from 'react';
import { LoadingKeys, usePrompt } from '../ui/contexts/PromptContext';
import PromptFileUploadModal from './PromptFileUploadModal';
import PromptLoading from './PromptLoading';
import PromptRightSidebarTestingConsoleNavigation from './PromptRightSidebarTestingConsoleNavigation';
import { PromptTestingConsoleInputTab } from '../lib/interfaces';
import { SimpleTextarea } from '@repo/ui/components';


const PromptRightSidebarTestingConsole = () => {
	const promptsContext = usePrompt();
	const [height, setHeight] = useState(64);
	const resizing = useRef(false);
	const [isPagesDropdownVisible, setIsPagesDropdownVisible] = useState(false);
	const [tabs, setTabs] = useState<PromptTestingConsoleInputTab[]>([{ id: 1, value: '' }]);
	const [activeTab, setActiveTab] = useState(0);

	const handleMouseDown = (e: React.MouseEvent) => {
		resizing.current = true;
		document.body.style.cursor = 'ns-resize';
	};

	const handleMouseMove = (e: MouseEvent) => {
		if (resizing.current) {
			const windowHeight = window.innerHeight;
			const newHeight = windowHeight - e.clientY;
			setHeight(Math.max(64, Math.min(newHeight, windowHeight - 210)));
		}
	};

	const handleMouseUp = () => {
		resizing.current = false;
		document.body.style.cursor = '';
	};

	const handleAddTab = () => {
		const newTab: PromptTestingConsoleInputTab = { id: tabs.length + 1, value: '' };
		setTabs([...tabs, newTab]);
		setActiveTab(tabs.length);
	}

	const handleTabValueChange = (index: number, newValue: string) => {
        setTabs(prev => prev.map((tab, i) => i === index ? { ...tab, value: newValue } : tab));
    };

	useEffect(() => {
		window.addEventListener('mousemove', handleMouseMove);
		window.addEventListener('mouseup', handleMouseUp);
		return () => {
			window.removeEventListener('mousemove', handleMouseMove);
			window.removeEventListener('mouseup', handleMouseUp);
		};
	});

	return (
		<div className={`bottom testing-console ${promptsContext.testingConsoleActiveClass} w-full rounded-b-xl overflow-y-auto`} style={{ height: `${height}px` }}>
			<div className="draggable w-full sticky top-0 left-0 z-20 h-[6px] bg-[#e5e7eb] cursor-ns-resize" onMouseDown={handleMouseDown} />
			<div className="p-4 flex items-center justify-between bg-white sticky top-0 z-10">
				<div className="font-medium select-none">Testing Console</div>
				<div className="flex gap-4 items-center">
					<button onClick={() => promptsContext.setShowFileUploadModal(true)}>
						<svg width="17" height="16" viewBox="0 0 17 16" fill="none" xmlns="http://www.w3.org/2000/svg">
							<g opacity="0.8">
								<path d="M14.4018 7.26622L8.39138 13.2766C7.02454 14.6435 4.80847 14.6435 3.44163 13.2766C2.0748 11.9098 2.0748 9.69372 3.44163 8.32688L9.45204 2.31647C10.3633 1.40525 11.8406 1.40525 12.7519 2.31647C13.6631 3.2277 13.6631 4.70508 12.7519 5.61631L6.97716 11.391C6.52155 11.8466 5.78286 11.8466 5.32725 11.391C4.87164 10.9354 4.87164 10.1967 5.32725 9.74109L10.3948 4.6735" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
							</g>
						</svg>
					</button>
				</div>
			</div>
			<div className="tab-links-wrapper">
				<div className="tab-links px-4 flex gap-2">
					{tabs.map((tab, index) => (
						<button
							key={tab.id}
							className={`font-medium text-sm px-4 py-3 ${activeTab === index ? "active" : ""}`}
							onClick={() => setActiveTab(index)}
						>
							Input {tab.id}
						</button>
					))}
					<button className="font-medium text-sm px-4 py-3 flex items-center gap-2" onClick={handleAddTab}>
						<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
							<g opacity="0.56">
								<path d="M8.00016 3.33301V12.6663M3.3335 7.99967H12.6668" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
							</g>
						</svg>
						Add input
					</button>
				</div>
				<div className="tab-link-panels overflow-y-auto">
					{tabs.map((tab, index) => (
						<div key={tab.id} className={`tab-link-panel ${activeTab === index ? "active" : ""}`} style={{ display: activeTab === index ? "block" : "none" }}>
							{!promptsContext.file && (
								<div className="prompt-input-container prompt-textarea-container p-[5px] no-margin">
									<SimpleTextarea style={{ height: `${height - 122}px` }} className="textarea-in-tab" useCommonStyling value={tab.value} onChange={value => handleTabValueChange(index, value)} placeholder='{ "video_url": "https://example.com/tutorial.mp4" }'/>
								</div>
							)}
							{promptsContext.file && (
								<>
									<div className="flex items-center justify-between p-4" style={{ borderBottom: "1px solid #E2E8ED" }}>
										<div className="flex items-center text-sm font-medium gap-2" style={{ color: "#0000F9" }}>
											<svg className="flex-shrink-0" width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
												<g opacity="0.8">
													<path d="M14.1015 7.26634L8.09108 13.2768C6.72425 14.6436 4.50817 14.6436 3.14134 13.2768C1.7745 11.9099 1.7745 9.69384 3.14134 8.327L9.15174 2.3166C10.063 1.40537 11.5404 1.40537 12.4516 2.3166C13.3628 3.22782 13.3628 4.7052 12.4516 5.61643L6.67687 11.3911C6.22126 11.8467 5.48257 11.8467 5.02695 11.3911C4.57134 10.9355 4.57134 10.1968 5.02695 9.74122L10.0946 4.67362" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
												</g>
											</svg>
											<span className="break-words" style={{ wordBreak: "break-word" }}>
												{promptsContext.file?.name || 'No file uploaded'}
											</span>
										</div>
										<div className="text-sm font-medium flex-shrink-0" style={{ color: '#97A3B6' }}>
											{promptsContext.file ? `${(promptsContext.file.size / (1024 * 1024)).toFixed(2)} MB` : 'No file size'}
										</div>
									</div>
									<PromptRightSidebarTestingConsoleNavigation />

									<div className="p-4">
										<div className="flex items-center">
											<div className="font-medium text-sm" style={{ color: '#97A3B6' }}>Preview</div>
										</div>
										<div className="my-4">
											{promptsContext.invoiceImage && (
												<img className="m-auto" src={`data:content/type;base64,${promptsContext.invoiceImage}`} alt="" />
											)}
										</div>
									</div>
								</>
							)}
						</div>
					))}
				</div>
			</div>
			{promptsContext.showFileUploadModal && (
				<PromptFileUploadModal />
			)}
		</div>
	)
}
export default PromptRightSidebarTestingConsole;