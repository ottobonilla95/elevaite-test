import { CommonModal } from "@repo/ui/components";
import { useState } from "react";

interface AgentWorkflowDetailsModalProps {
  onClose: () => void;
}

const AnalysisCol = () => {
	const [showDetails, setShowDetails] = useState(false);
	return (
		<div className="col rounded-md p-4" style={{ border: '1px solid #E2E8ED'}}>
			<button className="flex items-center justify-between gap-2 w-full text-left pl-3" style={{ borderLeft: '3px solid #FD681F'}} onClick={() => setShowDetails(!showDetails)}>
				<div>
					<div className="text-sm font-medium">Sentiment Analyzer</div>
					<div className="text-xs font-medium opacity-75">Extracts data</div>
				</div>

				<svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
					<g opacity="0.8">
						<path d="M4 6.5L8 10.5L12 6.5" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</g>
				</svg>
			</button>

			{showDetails && (
				<div className="mt-4">
					<div className="text-sm font-medium mb-2 flex flex-wrap gap-1">
						<div className="opacity-75">Input Tokens: </div>
						<div>8,192</div>
					</div>
					<div className="text-sm font-medium mb-2 flex flex-wrap gap-1">
						<div className="opacity-75">Output Tokens: </div>
						<div>2,167</div>
					</div>
					<div className="text-sm font-medium mb-2 flex flex-wrap gap-1">
						<div className="opacity-75">Cost: </div>
						<div>$2.45</div>
					</div>
					<div className="text-sm font-medium mb-2 flex flex-wrap gap-1">
						<div className="opacity-75">Execution Time: </div>
						<div className="tag-blue">1.8s</div>
					</div>
					<div className="text-sm font-medium mb-2 flex flex-wrap gap-1">
						<div className="opacity-75">Confidence Score: </div>
						<div className="tag-blue">85% (High Accuracy)</div>
					</div>
				</div>
			)}
		</div>
	)
}

const AgentWorkflowDetailsModal = ({ onClose }: AgentWorkflowDetailsModalProps) => {
  return (
	<CommonModal className="agent-workflow-details-modal">
		<div className="bg-white py-4 px-5 rounded-lg w-[600px]">
			<div className="flex items-center justify-between mb-5">
				<h2 className="text-lg font-medium">Agent Workflow Details</h2>
				<button onClick={onClose}>
					<svg width="20" height="21" viewBox="0 0 20 21" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M15 5.5L5 15.5M5 5.5L15 15.5" stroke="#97A3B6" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</button>
			</div>
			<div className="blocks">
				<div className="block py-3 px-4 rounded-lg mb-3" style={{ border: '1px solid #E2E8ED'}}>
					<div className="flex items-center justify-between mb-4">
						<div className="font-medium text-sm opacity-75">Overall Workflow Summary</div>
						<button>
							<svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
								<g opacity="0.8">
									<path d="M4 6.5L8 10.5L12 6.5" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
								</g>
							</svg>
						</button>
					</div>
					<div className="px-3">
						<div className="flex items-center justify-between gap-2 text-sm mb-4">
							<div><strong>Run ID: </strong>#WF-20250401-001</div>
							<div className="italic">April 1, 2025, 10:15 AM</div>
						</div>
						<div className="flex items-center justify-between gap-2 text-sm mb-4">
							<div><strong>Total Input Tokens: </strong>8,192</div>
							<div><strong>Total Output Tokens: </strong>2.167</div>
						</div>
						<div className="flex items-center justify-between gap-2 text-sm mb-4">
							<div><strong>Total Charges: </strong> $2.45</div>
							<div><strong>Execution Time: </strong><div className="tag-blue">7.8s</div></div>
						</div>
						<div className="flex items-center justify-between gap-2 text-sm">
							<div><strong>Self-Scoring</strong></div>
							<div className="tag-blue">85% (High Accuracy)</div>
						</div>
					</div>
				</div>

				<div className="block py-3 px-4 rounded-lg" style={{ border: '1px solid #E2E8ED'}}>
					<div className="flex items-center justify-between mb-4">
						<div className="font-bold text-sm opacity-75">Agent 1: Sentiment Processing Agent</div>
						<button>
							<svg width="16" height="17" viewBox="0 0 16 17" fill="none" xmlns="http://www.w3.org/2000/svg">
								<g opacity="0.8">
									<path d="M4 6.5L8 10.5L12 6.5" stroke="#212124" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
								</g>
							</svg>
						</button>
					</div>
					<div className="px-3">
						<div className="text-sm mb-4">
							<div>Tasks Executed: <strong>Analyzed call transcripts for sentiment.</strong></div>
						</div>
						<div className="flex items-center justify-between gap-2 text-sm mb-4">
							<div>Total Cost: <strong>$1.10</strong></div>
							<div>Time Taken: <div className="tag-blue">7.8s</div></div>
						</div>
						<div className="flex items-center justify-between gap-2 text-sm">
							<div>Performance Score:</div>
							<div className="tag-blue">90% (Very Efficient)</div>
						</div>
					</div>
				</div>

			</div>

			<div className="mt-3 bg-[#F8FAFC] text-xs p-2 rounded-sm">
				<div className="flex items-center justify-between">
					<div>Input</div>
					<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M7 5L10.5 1.5M10.5 1.5H7.5M10.5 1.5V4.5M5 7L1.5 10.5M1.5 10.5H4.5M1.5 10.5L1.5 7.5" stroke="black" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</div>
				<div className="mt-2">Raw Invoice Text</div>
			</div>

			<div className="mt-3 bg-[#F8FAFC] text-xs p-2 rounded-sm">
				<div className="flex items-center justify-between">
					<div>Output</div>
					<svg width="12" height="12" viewBox="0 0 12 12" fill="none" xmlns="http://www.w3.org/2000/svg">
						<path d="M7 5L10.5 1.5M10.5 1.5H7.5M10.5 1.5V4.5M5 7L1.5 10.5M1.5 10.5H4.5M1.5 10.5L1.5 7.5" stroke="black" stroke-linecap="round" stroke-linejoin="round"/>
					</svg>
				</div>
				<div className="mt-2">{'{"total": "$325.00"}'}</div>
			</div>

			<div className="cols grid grid-cols-2 gap-4 mt-3">
				<AnalysisCol />
				<AnalysisCol />
			</div>

		</div>
	</CommonModal>
  )
}
export default AgentWorkflowDetailsModal