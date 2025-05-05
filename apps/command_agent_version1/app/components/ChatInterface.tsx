"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, Bot, AlertCircle } from "lucide-react";
import "./ChatInterface.scss";
import { WorkflowAPI } from "../api/workflowApi.ts";

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
}

const ChatInterface: React.FC<ChatInterfaceProps> = ({
    onExitChat,
    onCreateNewWorkflow,
    workflowName,
    workflowId
}) => {
    const [chatMessages, setChatMessages] = useState<ChatMessage[]>([
        {
            id: Date.now(),
            text: `Workflow deployed successfully with ID: ${workflowId.substring(0, 8)}. You can now ask questions.`,
            sender: "bot"
        }
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
        if (e.key === 'Enter' && !isLoading && chatInput.trim()) {
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
            sender: "user" as const
        };

        setChatMessages(prevMessages => [...prevMessages, userMessage]);

        // Save and clear input
        const query = chatInput;
        setChatInput("");

        setIsLoading(true);

        try {
            const chatHistory = chatMessages.map((message) => ({
                actor: message.sender,
                content: message.text,
            }));

            const responseStream = await WorkflowAPI.runWorkflowStream(workflowId, query, chatHistory);
            console.log("Workflow response stream:", responseStream);
            if (!responseStream) {
                console.error("No response stream received");
                setChatMessages(prevMessages => [
                    ...prevMessages,
                    {
                        id: Date.now() + 1,
                        text: "Error: Failed to connect to the workflow",
                        sender: "bot",
                        error: true
                    }
                ]);
                return;
            }

            console.log("Workflow response stream started");

            const botMessage = {
                id: Date.now() + 1,
                text: "",
                sender: "bot" as const
            };

            // Add an empty bot message to the chat
            setChatMessages((prevMessages) => [...prevMessages, botMessage]);

            // Read and process the streamed chunks
            const decoder = new TextDecoder();
            let done = false;

            while (!done) {
                const { value, done: streamDone } = await responseStream.read();
                done = streamDone;
                const chunk = decoder.decode(value);

                setChatMessages((prevMessages) =>
                    prevMessages.map((message) =>
                        message.id === botMessage.id
                            ? { ...message, text: message.text + chunk }
                            : message
                    )
                );
            }

        } catch (error) {
            console.error("Error running workflow:", error);

            // Add error message to chat
            setChatMessages(prevMessages => [
                ...prevMessages,
                {
                    id: Date.now() + 1,
                    text: `Error: ${(error as Error).message || "Failed to process message"}`,
                    sender: "bot",
                    error: true
                }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    // Render user avatar
    const renderUserAvatar = () => {
        return (
            <div className="message-avatar">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 11C14.2091 11 16 9.20914 16 7C16 4.79086 14.2091 3 12 3C9.79086 3 8 4.79086 8 7C8 9.20914 9.79086 11 12 11Z" fill="currentColor" />
                    <path d="M12 13C8.13401 13 5 16.134 5 20V21H19V20C19 16.134 15.866 13 12 13Z" fill="currentColor" />
                </svg>
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
                            {message.sender === "user" ? renderUserAvatar() : renderBotAvatar(message.error)}
                            <div className="message-bubble">
                                {message.text}
                            </div>
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
                    {isLoading ? '...' : <Send size={18} />}
                </button>
            </div>
        </div>
    );
};

export default ChatInterface;