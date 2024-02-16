"use client";
import { ChatbotIcons, CommonButton, SimpleInput } from "@repo/ui/components";
import { useState } from "react";
import "./ChatbotInput.scss";

interface ChatbotInputProps {

}

export function ChatbotInput(props: ChatbotInputProps): JSX.Element {
    const [text, setText] = useState("");


    function handleTextChange(value: string): void {        
        setText(value);
    }

    function handleSend(): void {
        if (!text) return;
        setText("");
        console.log("Sending:", text);
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSend();
    }

    function handleSummarize(): void {
        console.log("Handling summarize");
    }


    return (
        <div className="chatbot-input-container">
            <SimpleInput
                wrapperClassName="chatbot-input-field"
                value={text}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                placeholder="Enter text and press ENTER"
                rightIcon={
                    <CommonButton
                        onClick={handleSend}
                    >
                        <ChatbotIcons.SVGSend/>
                    </CommonButton>                    
                }
            />

            <CommonButton
                className="summarize-button"
                overrideClass={true}
                onClick={handleSummarize}
            >
                <ChatbotIcons.SVGClipboard/>
                <span>Summarize</span>
            </CommonButton>
        </div>
    );
}