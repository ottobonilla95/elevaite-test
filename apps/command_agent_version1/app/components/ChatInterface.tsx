// ChatInterface.tsx
"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, MessageSquare } from "lucide-react";
import "./ChatInterface.scss";

interface ChatMessage {
    id: number;
    text: string;
    sender: "user" | "bot";
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
            text: "Workflow deployed successfully. You can now ask questions.",
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
            // Simulate API call
            await new Promise(resolve => setTimeout(resolve, 1500));

            // Generate a bot response based on the query
            let botResponse = "";

            if (query.toLowerCase().includes("help")) {
                botResponse = "I can help you with information about your workflow, answer questions, and process data through the agents you've configured.";
            } else if (query.toLowerCase().includes("how")) {
                botResponse = "This agent workflow is designed to route your questions to specialized agents that can search the web, access APIs, or analyze data based on your needs.";
            } else {
                botResponse = `I've processed your query: "${query}". Based on the workflow configuration, I've routed this to the appropriate agent and found some relevant information for you. Would you like me to elaborate further on any specific aspect?`;
            }

            // Add bot response to chat
            const botMessage = {
                id: Date.now() + 1,
                text: botResponse,
                sender: "bot" as const
            };

            setChatMessages(prevMessages => [...prevMessages, botMessage]);
        } catch (error) {
            console.error("Error running workflow:", error);

            // Add error message to chat
            setChatMessages(prevMessages => [
                ...prevMessages,
                {
                    id: Date.now() + 1,
                    text: `Error: ${(error as Error).message || "Failed to process message"}`,
                    sender: "bot" as const
                }
            ]);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="chat-interface">
            <div className="chat-messages-container">
                {chatMessages.length === 0 ? (
                    <div className="empty-chat">
                        <div className="empty-chat-icon">
                            <MessageSquare size={24} />
                        </div>
                        <h3 className="empty-chat-title">Start a conversation</h3>
                        <p className="empty-chat-description">
                            Ask a question to begin using your deployed agent flow.
                        </p>
                    </div>
                ) : (
                    <div className="chat-messages">
                        {chatMessages.map((message) => (
                            <div
                                key={message.id}
                                className={`chat-message ${message.sender === "user" ? "user-message" : "bot-message"}`}
                            >
                                {message.text}
                            </div>
                        ))}
                        <div ref={messagesEndRef} />
                    </div>
                )}
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