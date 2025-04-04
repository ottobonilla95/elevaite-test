"use client";
import { ChatbotIcons, CommonButton, SimpleInput } from "@repo/ui/components";
import { useState } from "react";
import { useChat } from "../ui/contexts/ChatContext";
import "./ChatbotInput.scss";



interface ChatbotInputProps {
    bareBones?: boolean;
    noSummarize?: boolean;
    placeholder?: string;
    inlinePrompts?: string[];
}


export function ChatbotInput(props: ChatbotInputProps): JSX.Element {
    const chatContext = useChat();
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
        chatContext.addNewUserMessageToCurrentSession(workingText);
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSend();
    }

    function handleSummarize(): void {
        if (chatContext.isChatLoading) return;
        chatContext.getSessionSummary();
    }


    return (
        <div className={[
                "chatbot-input-container",
                chatContext.isChatLoading ? "loading" : undefined,
                props.bareBones ? "bare-bones" : undefined,
            ].filter(Boolean).join(" ")}>
            <SimpleInput
                wrapperClassName="chatbot-input-field"
                value={text}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                placeholder={chatContext.isChatLoading ? "Please wait..." : props.placeholder ? props.placeholder : "Enter text and press ENTER"}
                disabled={chatContext.isChatLoading}
                bottomRightIcon={
                    <CommonButton
                        className="chatbot-input-send-button"
                        onClick={handleSend}
                        disabled={chatContext.isChatLoading}
                    >
                        {chatContext.isChatLoading ?
                            <ChatbotIcons.SVGSpinner/> :
                            <ChatbotIcons.SVGSend/>
                        }
                    </CommonButton>                    
                }
                inlinePrompts={props.inlinePrompts}
            />

            {props.noSummarize ? undefined :
                <CommonButton
                    className="summarize-button"
                    overrideClass
                    onClick={handleSummarize}
                    disabled={chatContext.isChatLoading}
                >
                    <ChatbotIcons.SVGClipboard/>
                    <span>Summarize</span>
                </CommonButton>
            }
        </div>
    );
}