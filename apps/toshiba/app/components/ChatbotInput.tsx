"use client";
import { ChatbotIcons, CommonButton, SimpleInput } from "@repo/ui/components";
import { useState, useEffect } from "react";
import { useChat } from "../ui/contexts/ChatContext";
import { WindowGrid } from "../lib/interfaces";
import "./ChatbotInput.scss";

interface ChatbotInputProps {
    bareBones?: boolean;
    noSummarize?: boolean;
    placeholder?: string;
    inlinePrompts?: string[];
    text?: string;
}

export function ChatbotInput(props: ChatbotInputProps): JSX.Element {
    const chatContext = useChat();
    const [text, setText] = useState(props.text ?? "");
    const [messageWasSent, setMessageWasSent] = useState(false);

    // Effect to switch to active tab when a message is sent
    useEffect(() => {
        if (messageWasSent) {
            chatContext.setActiveWindowGrid(WindowGrid.active);
            setMessageWasSent(false);
        }
    }, [messageWasSent]);

    function handleTextChange(value: string): void {
        if (chatContext.isChatLoading) return;
        setText(value);
    }

    function handleSend(): void {
        if (chatContext.isChatLoading) return;
        const workingText = text;
        setText("");

        // If text is empty but we have inline prompts, use the first prompt
        if (!workingText.trim()) {
            if (props.inlinePrompts && props.inlinePrompts.length > 0) {
                chatContext.addNewUserMessageToCurrentSession(props.inlinePrompts[0]);
                setMessageWasSent(true);
                return;
            } else {
                return; // No text and no prompts, don't send anything
            }
        }

        // Normal case - we have text
        chatContext.addNewUserMessageToCurrentSession(workingText);
        setMessageWasSent(true);
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSend();
    }

    function handleSummarize(): void {
        if (chatContext.isChatLoading) return;
        chatContext.getSessionSummary();
    }

    function handlePromptClick(prompt: string): void {
        if (chatContext.isChatLoading) return;
        setText(prompt);

        chatContext.addNewUserMessageToCurrentSession(prompt);

        setMessageWasSent(true);
    }

    // console.log("asdjnjsa", props)
    // console.log("text", text)

    useEffect(() => {
        if (props.text) {
            setText(props.text);
        }
    }, [props.text]);

    return (
        <div className={[
            "chatbot-input-container",
            chatContext.isChatLoading ? "loading" : undefined,
            props.bareBones ? "bare-bones" : undefined,
        ].filter(Boolean).join(" ")}>
            <SimpleInput
                wrapperClassName="chatbot-input-field"
                // value={text && text !== "" ? text : props.text ?? ""}
                value={text}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                placeholder={chatContext.isChatLoading ? "Please wait..." : props.placeholder ? props.placeholder : "Enter text and press ENTER"}
                disabled={chatContext.isChatLoading}
                rightIcon={props.inlinePrompts ? undefined :
                    <CommonButton
                        className="chatbot-input-send-button"
                        onClick={handleSend}
                        disabled={chatContext.isChatLoading}
                    >
                        {chatContext.isChatLoading ?
                            <ChatbotIcons.SVGSpinner /> :
                            <ChatbotIcons.SVGSend />
                        }
                    </CommonButton>
                }
                bottomRightIcon={!props.inlinePrompts ? undefined :
                    <CommonButton
                        className="chatbot-input-send-button"
                        onClick={handleSend}
                        disabled={chatContext.isChatLoading}
                    >
                        {chatContext.isChatLoading ?
                            <ChatbotIcons.SVGSpinner /> :
                            <ChatbotIcons.SVGSend />
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
                    <ChatbotIcons.SVGClipboard />
                    <span>Summarize</span>
                </CommonButton>
            }
        </div>
    );
}