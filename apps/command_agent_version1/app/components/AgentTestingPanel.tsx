import { AlertCircle, Bot, User } from "lucide-react";
import React, { useEffect, useRef, useState } from "react";
import { executeWorkflowModern } from "../lib/actions";
import { useWorkflows } from "../ui/contexts/WorkflowsContext";
import "./AgentTestingPanel.scss";
import { AgentTestingParser } from "./AgentTestingParser";
import AgentWorkflowDetailsModal from "./AgentWorkflowDetailsModal";
import { type ChatMessage } from "./type";
import { ChatbotIcons } from "@repo/ui/components";

const rows = [
	{
		id: 1,
		heading: 'Context',
		value: '8,192 Tokens'
	},
	{
		id: 2,
		heading: 'Input Pricing',
		value: '$30.00 / 1M Tokens'
	},
	{
		id: 3,
		heading: 'Output Pricing',
		value: '$60.00 / 1M Tokens'
	},
	{
		id: 4,
		heading: 'Hallucination Risk',
		tag: 'Low'
	},
	{
		id: 5,
		heading: 'Latency',
		tag: 'Normal (2.3s)'
	},
	{
		id: 6,
		heading: 'Overall Score',
		tag: '8/10'
	},
]

function AgentTestingPanel({ workflowId } : { workflowId: string }): React.ReactElement {
	const chatEndRef = useRef<HTMLDivElement | null>(null);
	const { expandChat, setExpandChat } = useWorkflows();
	const [showAgentWorkflowModal, setShowAgentWorkflowModal] = useState(false);
	const [showAgentWorkflowDetails, setShowAgentWorkflowDetails] = useState(true);
	const [chatInput, setChatInput] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
		{
			id: Date.now(),
			text: workflowId ? `Workflow deployed successfully with ID: ${workflowId.substring(0, 8)}. You can now ask questions.` :
								"No workflow detected. Please select a workflow from the left panel.",
			sender: "bot",
		},
	]);

	useEffect(() => {
		if (chatMessages.length === 1) {
			setChatMessages([
				{
					id: Date.now(),
					text: workflowId ? `Workflow deployed successfully with ID: ${workflowId.substring(0, 8)}. You can now ask questions.` :
										"No workflow detected. Please select a workflow from the left panel.",
					sender: "bot",
				},
			]);
		}
	}, [workflowId]);

	useEffect(() => {
		if (chatEndRef.current) {
			chatEndRef.current.scrollIntoView({ behavior: "smooth" });
		}
	}, [chatMessages]);



	function handleInputChange (event: React.ChangeEvent<HTMLInputElement>): void {
		setChatInput(event.target.value);
	};

	function handleKeyPress(e: React.KeyboardEvent): void {
		if (e.key === "Enter" && !isLoading && chatInput.trim()) {
			void handleSendMessage();
		}
	};

	async function handleSendMessage(): Promise<void> {
		if (!chatInput.trim()) return;

		// Add user message to chat
		const userMessage = {
			id: Date.now(),
			text: chatInput,
			sender: "user" as const,
		};

		setChatMessages((prevMessages) => [...prevMessages, userMessage]);

		// Save and clear input
		const query = chatInput;
		setChatInput("");
		setIsLoading(true);

		try {
			const chatHistory = chatMessages.map((message) => ({
				actor: message.sender,
				content: message.text,
			}));

			// Create execution request
			const executionRequest = {
				query,
				chat_history: chatHistory,
				runtime_overrides: {},
			};

			const result = await executeWorkflowModern(workflowId, executionRequest);

			let responseText = "No response received";

			if (result?.response) {
				try {
					const parsedResponse = JSON.parse(result.response);
					responseText = parsedResponse.content || "No content found";
				} catch (parseError) {
					console.error("Failed to parse response JSON:", parseError);
					responseText = result.response || "No response received";
				}
			}

			const botMessage = {
				id: Date.now() + 1,
				text: responseText,
				sender: "bot" as const,
			};

			setChatMessages((prevMessages) => [...prevMessages, botMessage]);
		} catch (error) {
			console.error("Error running workflow:", error);

			// Add error message to chat
			setChatMessages((prevMessages) => [
				...prevMessages,
				{
					id: Date.now() + 1,
					text: `Error: ${(error as Error).message || "Failed to process message"}`,
					sender: "bot",
					error: true,
				},
			]);
		} finally {
			setIsLoading(false);
		}
	};

	const renderUserAvatar = () => {
		return (
			<div className="message-avatar rounded-full shrink-0 bg-[#FF681F]">
				<User size={16} />
			</div>
		);
	};

	// Render bot avatar
	const renderBotAvatar = (isError = false) => {
		return (
			<div className="message-avatar rounded-full shrink-0 bg-[#FF681F]">
				{isError ? <AlertCircle size={16} /> : <Bot size={16} />}
			</div>
		);
	};

	const formatTime = (timestamp: number) => {
		const date = new Date(timestamp);
		return date.toLocaleTimeString('en-US', {
			hour: '2-digit',
			minute: '2-digit',
			hour12: true
		});
	};


	return (
		<>
			<div className={`agent-testing-panel absolute top-4 right-4 bg-white z-10 flex flex-col gap-3 rounded-xl p-2${expandChat ? ' is-expanded' : ''}`}>
				<div className="top flex-1 rounded-lg flex flex-col justify-between overflow-auto" style={{ border: '1px solid #E2E8ED' }}>
					<div>
						<div className="flex items-center justify-between py-2 px-6 sticky top-0 z-10 bg-white" style={{ borderBottom: '1px solid #E2E8ED' }}>
							<div className="font-bold">Testing Workflow</div>
							<button onClick={() => { setExpandChat(!expandChat); }} type="button">
								{expandChat ? (
									<svg width="17" height="18" viewBox="0 0 17 18" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M2.83773 10.417H7.08773M7.08773 10.417V14.667M7.08773 10.417L2.12939 15.3753M14.1711 7.58364H9.92106M9.92106 7.58364V3.33364M9.92106 7.58364L14.8794 2.62531" stroke="#4D4D50" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
										<path d="M2.83773 10.417H7.08773M7.08773 10.417V14.667M7.08773 10.417L2.12939 15.3753M14.1711 7.58364H9.92106M9.92106 7.58364V3.33364M9.92106 7.58364L14.8794 2.62531" stroke="#4D4D50" strokeWidth="1.4" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								) : (
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
										<g opacity="0.8">
											<path d="M10.6667 5.33333L14 2M14 2H10.6667M14 2V5.33333M5.33333 5.33333L2 2M2 2L2 5.33333M2 2L5.33333 2M5.33333 10.6667L2 14M2 14H5.33333M2 14L2 10.6667M10.6667 10.6667L14 14M14 14V10.6667M14 14H10.6667" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
											<path d="M10.6667 5.33333L14 2M14 2H10.6667M14 2V5.33333M5.33333 5.33333L2 2M2 2L2 5.33333M2 2L5.33333 2M5.33333 10.6667L2 14M2 14H5.33333M2 14L2 10.6667M10.6667 10.6667L14 14M14 14V10.6667M14 14H10.6667" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										</g>
									</svg>
								)}
							</button>
						</div>

						<div className="chat-bubbles my-4 px-6">
							{chatMessages.map((message) => (
								<div key={message.id} className={`chat-bubble rounded-lg bg-[#F8FAFC] flex items-center gap-4 p-4 ${message.sender === "user" ? "user-message" : "bot-message"} ${message.error ? "error-message" : ""}`}>
									{message.sender === "user"
										? renderUserAvatar()
										: renderBotAvatar(message.error)}
									<div>
										<div className={`text-xs text-[#FF681F] ${message.sender === "user" ? "user-time" : "bot-time"}`}>
											{formatTime(message.id)}
										</div>
										<div className="text-sm text-[#212124] opacity-75">
											<AgentTestingParser message={message.text}/>
										</div>
									</div>
								</div>
							))}							
							<div ref={chatEndRef} />
						</div>
					</div>

					{/* <div className="my-4 px-6 sticky bg-white bottom-4 z-1">
						<div className="details rounded-xl" style={{ border: '1px solid #E2E8ED' }}>
							<div className="flex items-center justify-between py-2 px-4" style={showAgentWorkflowDetails ? { borderBottom: '1px solid #E2E8ED' } : undefined}>
								<div className="font-medium text-sm">CoPilot</div>
								<button onClick={() => { setShowAgentWorkflowDetails(!showAgentWorkflowDetails); }} type="button">
									<svg width="16" height="16" viewBox="0 0 16 16" fill="none" xmlns="http://www.w3.org/2000/svg">
										<g opacity="0.8">
											<path d="M4 6L8 10L12 6" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										</g>
									</svg>
								</button>
							</div>
							{Boolean(showAgentWorkflowDetails) && (
								<div className="p-4">
									{rows.map(row => (
										<div key={row.id} className="flex items-center justify-between py-1 mb-3">
											<div className="font-medium text-sm opacity-75">
												{row.heading}
											</div>
											{Boolean(row.value) && (
												<div className="font-medium text-sm">
													{row.value}
												</div>
											)}
											{Boolean(row.tag) && (
												<div className="tag-blue">
													{row.tag}
												</div>
											)}
										</div>
									))}
									<button className="font-medium text-xs text-[#FF681F]" onClick={() => { setShowAgentWorkflowModal(true); }} type="button">
										See Full Workflow Details
									</button>
								</div>
							)}
						</div>
					</div> */}
				</div>

				{!workflowId ? undefined :
					<div className="bottom p-6 rounded-md bg-[#F8FAFC]" style={{ border: '1px solid #E2E8ED' }}>
						<div className="relative">
							<input type="text" className="h-[48px] w-full rounded-lg" value={chatInput}
								placeholder={isLoading ? "Working, please wait..." : "Type message here"}
								onChange={handleInputChange} onKeyDown={handleKeyPress} />
							<div className="actions flex items-center gap-2 absolute right-6 top-1/2 -translate-y-1/2">
								{/* <button type="button">
									<svg width="11" height="18" viewBox="0 0 11 18" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M9.31548 3.64493L9.67967 12.8244C9.72434 13.949 9.3204 15.0452 8.55677 15.8719C7.79314 16.6987 6.73236 17.1882 5.60778 17.2328C4.48324 17.2774 3.38701 16.8735 2.56027 16.1098C1.73353 15.3462 1.24405 14.2854 1.19941 13.1608L0.835202 3.98139C0.805476 3.23167 1.07478 2.50085 1.58384 1.94972C2.09295 1.39854 2.80014 1.07219 3.54981 1.04248C4.29954 1.01272 5.03037 1.28199 5.58152 1.79107C6.13268 2.30016 6.459 3.00737 6.48873 3.75709L6.84814 12.9417C6.86302 13.3166 6.72835 13.682 6.47381 13.9576C6.21927 14.2331 5.86569 14.3963 5.49083 14.4112C5.11597 14.4261 4.75061 14.2915 4.47499 14.0369C4.19943 13.7823 4.03626 13.4287 4.02137 13.0539L3.6901 4.57843" stroke="#FF681F" strokeWidth="1.06028" strokeLinecap="round" strokeLinejoin="round"/>
										<path d="M9.31548 3.64493L9.67967 12.8244C9.72434 13.949 9.3204 15.0452 8.55677 15.8719C7.79314 16.6987 6.73236 17.1882 5.60778 17.2328C4.48324 17.2774 3.38701 16.8735 2.56027 16.1098C1.73353 15.3462 1.24405 14.2854 1.19941 13.1608L0.835202 3.98139C0.805476 3.23167 1.07478 2.50085 1.58384 1.94972C2.09295 1.39854 2.80014 1.07219 3.54981 1.04248C4.29954 1.01272 5.03037 1.28199 5.58152 1.79107C6.13268 2.30016 6.459 3.00737 6.48873 3.75709L6.84814 12.9417C6.86302 13.3166 6.72835 13.682 6.47381 13.9576C6.21927 14.2331 5.86569 14.3963 5.49083 14.4112C5.11597 14.4261 4.75061 14.2915 4.47499 14.0369C4.19943 13.7823 4.03626 13.4287 4.02137 13.0539L3.6901 4.57843" stroke="#FF681F" strokeWidth="1.06028" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								</button> */}
								<button className={["send-button", isLoading ? "loading" : undefined].filter(Boolean).join(" ")} onClick={handleSendMessage} disabled={isLoading || !chatInput.trim()} type="button">
									{isLoading ?
										<ChatbotIcons.SVGSpinner/> :
										<ChatbotIcons.SVGSend/>
									}
								</button>
							</div>
						</div>
					</div>
				}
			</div>

			{Boolean(showAgentWorkflowModal) && (
				<AgentWorkflowDetailsModal onClose={() => { setShowAgentWorkflowModal(false); }}  />
			)}
		</>
  	)
}
export default AgentTestingPanel