"use client";
import {ChatbotIcons, CommonButton, SimpleTextarea} from "@repo/ui/components";
import {useContext, useEffect, useState} from "react";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./WelcomeChatbotInput.scss";
import "./MarkdownMessage.scss";
// import { jsPDF } from "jspdf";
// import { marked } from "marked";
// import html2canvas from "html2canvas";


export function WelcomeChatbotInput(): JSX.Element {
    const chatContext = useContext(ChatContext);
    const [text, setText] = useState("");

    function handleTextChange(value: string): void {
        if (chatContext.isChatLoading) return;
        setText(value);
    }


    function handleSend(): void {
        if (chatContext.isChatLoading) return;
        if (!chatContext.selectedSession) return;
        const workingText = text;
        if (!workingText.trim()) return;
        chatContext.addNewUserMessageWithLastMessages(text);
        setText("");
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSend();
    }


    return (
        <div className={["chatbot-welcome-input-container", chatContext.isChatLoading ? "loading" : undefined].filter(Boolean).join(" ")}>
            <SimpleTextarea
                wrapperClassName="chatbot-welcome-input-container chatbot-welcome-input-field"
                value={text}
                inputMode={"text"}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                style={{ height: "100%" }}
                placeholder={chatContext.isChatLoading ? "Please wait..." : "Paste chat and press ENTER"}
                disabled={chatContext.isChatLoading || chatContext.isFeedbackBoxOpen}
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

        </div>
    );
}