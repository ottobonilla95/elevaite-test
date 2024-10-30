"use client";
import { ChatbotIcons, CommonButton, SimpleInput } from "@repo/ui/components";
import { useContext, useState } from "react";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./ChatbotInput.scss";
import "./MarkdownMessage.scss";

export function ChatbotInput(): JSX.Element {
    const chatContext = useContext(ChatContext);
    const [text, setText] = useState("");

    function handleTextChange(value: string): void {
        if (chatContext.isChatLoading) return;
        setText(value);
    }

    function handleSend(): void {
        if (chatContext.isChatLoading) return;
        const workingText = text;
        setText("");
        if (!workingText.trim()) return;
        chatContext.addNewUserMessageWithLastMessages(workingText)
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSend();
    }

    function handleSummarize(): void {
        if (chatContext.isChatLoading) return;
        chatContext.getSessionSummary();
    }
    async function handleExport(): Promise<void> {
        const { selectedSession } = chatContext;
        if (!selectedSession || selectedSession.messages.length === 0) return;
    
        const markdownMessages = selectedSession.messages.map(message => message.text).join("\n\n");
    
        try {
            const response = await fetch('http://localhost:8000/generate-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ markdown: markdownMessages }),
            });
    
            if (!response.ok) {
                throw new Error('Failed to generate PDF');
            }
    
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
    
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'chat_session.pdf');
    
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error exporting chat session:', error);
        }
    }
    return (
        <div className={["chatbot-input-container", chatContext.isChatLoading ? "loading" : undefined].filter(Boolean).join(" ")}>
            <SimpleInput
                wrapperClassName="chatbot-input-field"
                value={text}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                placeholder={chatContext.isChatLoading ? "Please wait..." : "Enter text and press ENTER"}
                disabled={chatContext.isChatLoading}
                rightIcon={
                    <CommonButton
                        onClick={handleSend}
                        disabled={chatContext.isChatLoading}
                    >
                        {chatContext.isChatLoading ?
                            <ChatbotIcons.SVGSpinner/> :
                            <ChatbotIcons.SVGSend/>
                        }
                    </CommonButton>                    
                }
            />

            <CommonButton
                className=".export-button"
                overrideClass
                onClick={async () => {
                    await handleExport();
                }}
            >
                <ChatbotIcons.SVGDownload/>
            </CommonButton>
        </div>
    );
}