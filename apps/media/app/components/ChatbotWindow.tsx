"use client";
import { LoadingBar } from "@repo/ui/components";
import { useContext, useEffect, useRef, useState } from "react";
import { ChatContext } from "../ui/contexts/ChatContext";
import { ChatMessage } from "./ChatMessage";
import "./ChatbotWindow.scss";
import { SessionSummary } from "./SessionSummary";

export function ChatbotWindow(): JSX.Element {
    const chatContext = useContext(ChatContext);
    const messageListRef = useRef<HTMLDivElement | null>(null);
    const [isSummaryOpen, setIsSummaryOpen] = useState(false);

    // useEffect(() => {
    //     if (chatContext.selectedSession?.messages.length && chatContext.selectedSession.messages.length > 0) {
    //         scrollToLastMessage();
    //     }
    // }, [chatContext.selectedSession?.messages.length]);

    useEffect(() => {
        if (chatContext.selectedSession?.summary?.isExpectingDisplay) {
            setIsSummaryOpen(true);
            chatContext.removeExpectedDisplayFromSelectedSessionSummary();
        }
    }, [chatContext.selectedSession?.summary?.isExpectingDisplay]);


    function scrollToLastMessage(): void {
        if (!messageListRef.current) return;
        messageListRef.current.scrollIntoView({ behavior: "smooth", block: "end", inline: "nearest" });
    }

    function handleClose(): void {
        setIsSummaryOpen(false);
    }

    function handleDeleteSession(sessionId: string): void {
        chatContext.deleteSessionById(sessionId);
        handleClose();
    }

    return (
        <div className="chatbot-window-container">

            {!chatContext.selectedSession?.summary ? null :
                <div className={[
                    "session-summary-wrapper",
                    isSummaryOpen ? "open" : undefined,
                ].filter(Boolean).join(" ")}>
                    <SessionSummary 
                        sessionId={chatContext.selectedSession.id}
                        summary={chatContext.selectedSession.summary}
                        onClose={handleClose}
                        onDeleteSession={handleDeleteSession}
                    />
                </div>
            }

            {/* <div className="chatbot-window-header">
                <span>{chatContext.selectedSession?.label}</span>
            </div> */}

            <div className="chatbot-window-scroller">
                <div className="chatbot-window-message-list" ref={messageListRef}>
                    {chatContext.selectedSession?.messages.length === 0 ? null :
                        chatContext.selectedSession?.messages.map(message => 
                            <ChatMessage key={message.id} {...message} />
                        )
                    }
                </div>
            </div>

            {!chatContext.isChatLoading ? null : 
                <div className="chatbot-window-loader">
                    <LoadingBar />
                    <span>{chatContext.chatLoadingMessage ? chatContext.chatLoadingMessage : "\u200B"}</span>
                </div>
            }
        </div>
    );
}
