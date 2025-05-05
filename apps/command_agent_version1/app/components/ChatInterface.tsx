// ChatInterface.tsx
"use client";

import React, { useState, useRef, useEffect } from "react";
import { Send, MessageSquare } from "lucide-react";
import "./ChatInterface.scss";
import { WorkflowAPI } from "../api/workflowApi.ts";

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
            // const response = await WorkflowAPI.runWorkflow(workflowId, query);
            // console.log("Workflow response:", response);
            // const botMessage = {
            //     id: Date.now() + 1,
            //     text: response.response,
            //     sender: "bot" as const
            // };
            // setChatMessages(prevMessages => [...prevMessages, botMessage]);
            const chatHistory = chatMessages.map((message) => ({
                actor: message.sender,
                content: message.text,
            }));

            const responseStream = await WorkflowAPI.runWorkflowStream(workflowId, query, chatHistory);
            console.log("Workflow response stream:", responseStream);
            if (!responseStream) {
                console.error("No response stream received");
                return;
            }

            console.log("Workflow response stream started");

            const botMessage = {
                id: Date.now() + 1,
                text: "",
                sender: "bot" as const,
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