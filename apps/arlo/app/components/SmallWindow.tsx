import React, { useState, useEffect, useContext, useRef } from "react";
import "./SmallWindow.scss";
import { ChatbotIcons, CommonButton} from "@repo/ui/components";
import { ChatContext } from "../ui/contexts/ChatContext.tsx";

interface SmallWindowProps {
    onClose: () => void;
}



export function SmallWindow({ onClose }: SmallWindowProps): JSX.Element {
    const chatContext = useContext(ChatContext);
    const [inputValue, setInputValue] = useState("");
    const [messages, setMessages] = useState<string[]>([]);
    const [showCopyButton, setShowCopyButton] = useState(false);
    const [editableSummary, setEditableSummary] = useState("");
    // const inputRef = useRef<HTMLInputElement>(null);
    const inputRef = useRef<HTMLTextAreaElement>(null);
    const summaryRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (chatContext.recentSummary && chatContext.recentSummary !== "Loading summary...") {
            setShowCopyButton(true);
            setEditableSummary(chatContext.recentSummary);
        }
    }, [chatContext.recentSummary]);

    useEffect(() => {
        if (inputRef.current) {
            inputRef.current.focus();
        }
    }, []);

    useEffect(() => {
        const textarea = inputRef.current;
        if (!textarea) return;

        const adjustHeight = () => {
            textarea.style.height = 'auto';
            textarea.style.height = `${textarea.scrollHeight}px`;
        };

        // Adjust on input change
        textarea.addEventListener('input', adjustHeight);

        // Initial adjustment
        adjustHeight();

        return () => {
            textarea.removeEventListener('input', adjustHeight);
        };
    }, [inputValue]);

    function handleSend(): void{
        if (inputValue.trim()) {
            setShowCopyButton(false);
            chatContext.summarizeSession(inputValue);
            setMessages([...messages, inputValue]);
            setInputValue("");
        }
    }

    function handleSummaryVote(number: number): void {
        if (chatContext.recentSummary)
        {chatContext.voteOnSummary(number);}

}


    function handleSummarizeSession(): void {
        if (chatContext.selectedSession?.messages.length === 0) return;
        const fullChat = chatContext.selectedSession?.messages.map((message) => message.text).join("\n\n");
        if (!fullChat) return;
        setShowCopyButton(false);
        setInputValue("");
        chatContext.setRecentSummaryVote(0);
        chatContext.summarizeSession(fullChat);
    }

    useEffect(() => {
        const handleKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                handleClose();
            }
        };

        document.addEventListener("keydown", handleKeyDown);
        return () => {
            document.removeEventListener("keydown", handleKeyDown);
        };
    }, []);

    const handleCopy = () => {
        const summary = editableSummary ? editableSummary.replace(/<br\s*\/?>/gi, '\n') : "";
        void navigator.clipboard.writeText(summary);
    };

    const handleClose = () => {
        setInputValue("");
        setMessages([]);
        setShowCopyButton(false);
        chatContext.setRecentSummaryVote(0);
        chatContext.setRecentSummary(undefined)
        onClose();
    };

    return (
        <div className="small-window-overlay">
            <div className="small-window-container">

                <CommonButton className="close-button" onClick={handleClose}>
                    <ChatbotIcons.SVGClose/>
                </CommonButton>
                <div className="output-header">
                    {showCopyButton && (
                        <CommonButton
                            className="copy-button"
                            onClick={handleCopy}
                        >
                            <ChatbotIcons.SVGDocument/>
                            Copy
                        </CommonButton>
                    )}
                </div>

                <div className="content">
                    <div className="input-container">
                        <textarea
                            value={inputValue}
                            onChange={(e) => { setInputValue(e.target.value); }}
                            onKeyDown={(e) => {
                                if (e.key === "Enter" && !e.shiftKey) {
                                    e.preventDefault();
                                    handleSend();
                                }
                            }}
                            placeholder="Paste Chat here to summarize"
                            ref={inputRef}
                            className="expandable-input"
                            rows={1}
                        />
                        <div className="button-container">
                            <CommonButton className="summary-button new"
                                          onClick={handleSend}>Summarize Pasted Chat
                                <ChatbotIcons.SVGDocument/>
                            </CommonButton>
                            <CommonButton className="summary-button new"
                                          onClick={handleSummarizeSession}>Summarize Current Session
                                <ChatbotIcons.SVGMessage/>
                            </CommonButton>
                        </div>
                    </div>
                    <div className="output-box">
                        <div className="output-text-box">


                            {chatContext.recentSummary === "Loading summary..." && (
                                <span className="spinner-bar">
                                <ChatbotIcons.SVGSpinner/>
                            </span>
                            )}
                            {chatContext.recentSummary !== "Loading summary..." && (
                                <div
                                    ref={summaryRef}
                                    contentEditable={false}
                                    className={`summary editable-summary scrollable-output ${!editableSummary ? 'default-text' : ''}`}
                                    dangerouslySetInnerHTML={{__html: editableSummary || "Summary will show up here"}}
                                    onBlur={(e) => {
                                        setEditableSummary(e.currentTarget.innerHTML);
                                    }}
                                />

                            )}


                        </div>
                        <div className="button-container">
                            <div className="voting-buttons">
                                <CommonButton
                                    className={chatContext.recentSummaryVote === 1 ? "active" : ""}
                                    onClick={() => {
                                        handleSummaryVote(1);
                                    }}>
                                    <ChatbotIcons.SVGThumbs type={"up"}/>
                                    {chatContext.recentSummaryVote === 1 ? "Upvoted" : "Upvote"}
                                </CommonButton>
                                <CommonButton
                                    className={chatContext.recentSummaryVote === -1 ? "active" : ""}
                                    onClick={() => {
                                        handleSummaryVote(-1);
                                    }}>
                                    <ChatbotIcons.SVGThumbs type={"down"}/>
                                    {chatContext.recentSummaryVote === -1 ? "Downvoted" : "Downvote"}
                                </CommonButton>
                            </div>
                            </div>

                        </div>

                    </div>
                </div>
        </div>
    );
}