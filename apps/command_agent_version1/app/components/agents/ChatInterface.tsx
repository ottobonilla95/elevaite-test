"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, AlertCircle, User } from "lucide-react";
import "./ChatInterface.scss";
import { executeWorkflowModern } from "../../lib/actions";
import type { NewWorkflowExecutionRequest } from "../../lib/interfaces";

interface ChatMessage {
	id: number;
	text: string;
	sender: "user" | "bot";
	error?: boolean;
}

interface ChatInterfaceProps {
	onExitChat: () => void;
	onCreateNewWorkflow: () => void;
	workflowName: string;
	workflowId: string;
	deploymentName?: string;
}

function ChatInterface({
	onExitChat,
	onCreateNewWorkflow,
	workflowName,
	workflowId,
	deploymentName,
}: ChatInterfaceProps): JSX.Element {
	const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
		{
			id: Date.now(),
			text: `Workflow deployed successfully with ID: ${workflowId.substring(0, 8)}. You can now ask questions.`,
			sender: "bot",
		},
	]);
	const [chatInput, setChatInput] = useState("");
	const [isLoading, setIsLoading] = useState(false);
	const messagesEndRef = useRef<HTMLDivElement>(null);

	// Scroll to bottom when messages change
	useEffect(() => {
		messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
	}, [chatMessages]);

	// Handle input change
	const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
		setChatInput(e.target.value);
	};

	// Handle key press (Enter)
	const handleKeyPress = (e: React.KeyboardEvent) => {
		if (e.key === "Enter" && !isLoading && chatInput.trim()) {
			handleSendMessage();
		}
	};

	// Send message
	const handleSendMessage = async () => {
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
			const executionRequest: NewWorkflowExecutionRequest = {
				query,
				chat_history: chatHistory,
				runtime_overrides: {},
			};

			// if (deploymentName) {
			// 	// Use deployment-based execution
			// 	console.log("Executing workflow by deployment:", deploymentName);
			// 	executionRequest.deployment_name = deploymentName;
			// } else {
			// 	// Use workflow ID
			// 	console.log("Executing workflow by ID:", workflowId);
			// 	executionRequest.workflow_id = workflowId;
			// }

			const result = await executeWorkflowModern(workflowId, executionRequest);

			const botMessage = {
				id: Date.now() + 1,
				text: result.response ?? "No response received",
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

	// Render user avatar
	const renderUserAvatar = () => {
		return (
			<div className="message-avatar">
				<User size={16} />
			</div>
		);
	};

	// Render bot avatar
	const renderBotAvatar = (isError = false) => {
		return (
			<div className="message-avatar">
				{isError ? <AlertCircle size={16} /> : <Bot size={16} />}
			</div>
		);
	};

	return (
		<div className="chat-interface">
			<div className="chat-messages-container">
				<div className="chat-messages">
					{chatMessages.map((message) => (
						<div
							key={message.id}
							className={`chat-message ${message.sender === "user" ? "user-message" : "bot-message"} ${message.error ? "error-message" : ""}`}
						>
							{message.sender === "user"
								? renderUserAvatar()
								: renderBotAvatar(message.error)}
							<div className="message-bubble">{message.text}</div>
						</div>
					))}
					<div ref={messagesEndRef} />
				</div>
			</div>
			<div className="chat-input-container">
				<input
					type="text"
					value={chatInput}
					onChange={handleInputChange}
					onKeyDown={handleKeyPress}
					placeholder="Type a message..."
					className="chat-input"
					disabled={isLoading}
				/>
				<button
					onClick={handleSendMessage}
					className="chat-send-button"
					disabled={isLoading || !chatInput.trim()}
				>
					{isLoading ? "..." : <Send size={18} />}
				</button>
			</div>
		</div>
	);
};

export default ChatInterface;