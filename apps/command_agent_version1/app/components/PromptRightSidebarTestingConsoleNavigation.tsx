import { useState } from "react";
import { LoadingKeys, usePrompt } from "../ui/contexts/PromptContext";
import PromptLoading from "./PromptLoading";

interface SingleCheckboxProps {
	page: number;
	title?: string;
	checkedPages: number[],
	onChange: (page: number, checked: boolean) => void;
}

function SingleCheckbox({ title, page, checkedPages, onChange }: SingleCheckboxProps): JSX.Element {
	const [showVersions, setShowVersions] = useState(false);

	return (
		<div className="custom-checkbox flex flex-wrap items-center justify-between" key={page}>
			<label className={title}>
				<input
					type="checkbox"
					checked={checkedPages.includes(page)}
					onChange={e => { onChange(page, e.target.checked); }}
				/>
				<span>{title ? title : `Page ${page}`}</span>
			</label>
			<div className="versions">
				<button onClick={() => { setShowVersions(v => !v); }} className="versions-label flex items-center gap-2" type="button">
					<span>4 versions</span>
					<svg width="20" height="20" viewBox="0 0 20 20" fill="none" xmlns="http://www.w3.org/2000/svg">
						<g opacity="0.56">
							<path d="M5.42004 7.57007L10.28 12.4301L15.14 7.57007" stroke="#212124" strokeWidth="1.215" strokeLinecap="round" strokeLinejoin="round" />
						</g>
					</svg>
				</button>
			</div>
			<div className={`${!showVersions ? 'hidden' : ''} versions-wrapper w-full pt-2 pl-5`}>
				<div className="version flex items-center gap-2 py-2 px-4 rounded-md text-xs">
					<span className="font-medium">v1</span><span className="divider block w-[7px] h-[7px] rounded-full bg-[#D9D9D9]" />June 3, 2025<span className="divider block w-[7px] h-[7px] rounded-full bg-[#D9D9D9]" /> 09:53
				</div>
				<div className="version flex items-center gap-2 py-2 px-4 rounded-md text-xs">
					<span className="font-medium">v2</span><span className="divider block w-[7px] h-[7px] rounded-full bg-[#D9D9D9]" />June 4, 2025<span className="divider block w-[7px] h-[7px] rounded-full bg-[#D9D9D9]" /> 10:15
				</div>
				<div className="version flex items-center gap-2 py-2 px-4 rounded-md text-xs">
					<span className="font-medium">v3</span><span className="divider block w-[7px] h-[7px] rounded-full bg-[#D9D9D9]" />June 5, 2025<span className="divider block w-[7px] h-[7px] rounded-full bg-[#D9D9D9]" /> 11:00
				</div>
				<div className="version flex items-center gap-2 py-2 px-4 rounded-md text-xs">
					<span className="font-medium">v4</span><span className="divider block w-[7px] h-[7px] rounded-full bg-[#D9D9D9]" />June 6, 2025<span className="divider block w-[7px] h-[7px] rounded-full bg-[#D9D9D9]" /> 12:30
				</div>
			</div>
		</div>
	)
}

function PromptRightSidebarTestingConsoleNavigation(): JSX.Element {
	const promptsContext = usePrompt();
	const numPages = promptsContext.invoiceNumPages ?? 0;
	const allPages = Array.from({ length: numPages }, (_, i) => i + 1);
	const [checkedPages, setCheckedPages] = useState<number[]>([]);
	const [isPagesDropdownVisible, setIsPagesDropdownVisible] = useState(false);

	const handleNextPage = async () => {
		const data = await promptsContext.goToNextPage(true);
		console.log(data)
		if (data) {
			promptsContext.setInvoiceImage(data.image);
		}
	}

	const handlePrevPage = async () => {
		const data = await promptsContext.goToPrevPage(true);
		console.log(data)
		if (data) {
			promptsContext.setInvoiceImage(data.image);
		}
	}

	const handlePageChange = () => { setIsPagesDropdownVisible(!isPagesDropdownVisible); };

	const handleSelectAll = (e: React.ChangeEvent<HTMLInputElement>) => {
		const checked = e.target.checked;
		if (checked) {
			setCheckedPages(allPages);
		} else {
			setCheckedPages([]);
		}
	}

	const handleCheckboxChange = (page: number, checked: boolean) => {
		setCheckedPages(prev =>
			checked ? [...prev, page] : prev.filter(p => p !== page)
		);
	};

	return (
		<>
			{promptsContext.invoiceNumPages && promptsContext.invoiceNumPages > 1 ? <div className="p-4 mt-4">
				<div className="flex justify-between">
					<div className="relative">
						<button onClick={handlePageChange} className="current-page flex justify-between items-center rounded-md px-3 py-2 text-sm w-[300px]" type="button">
							{`page ${promptsContext.currentPage}`}
							<svg width="14" height="14" viewBox="0 0 14 14" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M3.5 5.25L7 8.75L10.5 5.25" stroke="#4A5567" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
							</svg>
						</button>
						{isPagesDropdownVisible ? <div className="custom-checkboxes rounded-lg bg-white w-[300px] mt-1">
							<div className="custom-checkbox">
								<label htmlFor="all">
									<input
										checked={checkedPages.length > 0 && checkedPages.length === allPages.length}
										onChange={handleSelectAll}
										id="all"
										type="checkbox" />
									<span>Select All</span>
								</label>
							</div>
							{allPages.map(page => (
								<SingleCheckbox page={page} checkedPages={checkedPages} onChange={handleCheckboxChange} key={page.toString()} />
							))}
							<SingleCheckbox title="All Pages" page={checkedPages.length} checkedPages={checkedPages} onChange={handleCheckboxChange} />
							{checkedPages.length > 0 && (
								<div className="py-2 px-3">
									<button onClick={() => { promptsContext.actionRunOnSelectedPages(checkedPages); }} className="btn btn-primary w-full">Run Selected({checkedPages.length})</button>
								</div>
							)}
						</div> : null}
					</div>
					<div className="navigation-arrows flex items-center gap-2 relative" style={{ top: '3px' }}>
						{promptsContext.loading[LoadingKeys.ChangingPage] ? <PromptLoading className="no-offset" width={25} height={25} /> : null}
						{promptsContext.currentPage && promptsContext.currentPage > 1 ? <button className="btn btn-outline gray w-[38px] h-[32px]" onClick={handlePrevPage} disabled={promptsContext.loading[LoadingKeys.ChangingPage]} type="button">
							<svg width="6" height="10" viewBox="0 0 6 10" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M4.44971 8.5L0.949707 5L4.44971 1.5" stroke="#4A5567" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
							</svg>
						</button> : null}
						{promptsContext.currentPage && promptsContext.currentPage < promptsContext.invoiceNumPages ? <button className="btn btn-outline gray w-[38px] h-[32px]" onClick={handleNextPage} disabled={promptsContext.loading[LoadingKeys.ChangingPage]} type="button">
							<svg width="6" height="10" viewBox="0 0 6 10" fill="none" xmlns="http://www.w3.org/2000/svg">
								<path d="M0.949707 8.5L4.44971 5L0.949707 1.5" stroke="#4A5567" strokeWidth="1.2" strokeLinecap="round" strokeLinejoin="round" />
							</svg>
						</button> : null}
					</div>
				</div>
			</div> : null}
		</>
	)
}
export default PromptRightSidebarTestingConsoleNavigation