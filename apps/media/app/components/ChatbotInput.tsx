"use client";
import { ChatbotIcons, CommonButton, SimpleInput } from "@repo/ui/components";
import { useContext, useState } from "react";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./ChatbotInput.scss";




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
    function handleExport(): void {
        if (chatContext.latestResponse) {
          chatContext.handleExportTable(chatContext.latestResponse);
        } else {
          console.error("No response available for export.");
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
                onClick={handleExport}
                // disabled={chatContext.isChatLoading}
            >
                <ChatbotIcons.SVGClipboard/>
                <span>Export to CSV</span>
            </CommonButton>
        </div>
    );
}