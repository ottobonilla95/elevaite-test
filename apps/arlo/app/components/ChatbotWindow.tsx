"use client";
import {CommonButton, LoadingBar} from "@repo/ui/components";
import { useContext, useEffect, useRef, useState } from "react";
import { ChatContext } from "../ui/contexts/ChatContext";
import { ChatMessage } from "./ChatMessage";
import "./ChatbotWindow.scss";
import { SessionSummary } from "./SessionSummary";
import { ChatbotIcons } from "@repo/ui/components";
import { SmallWindow } from "./SmallWindow";

export function ChatbotWindow(): JSX.Element {
    const chatContext = useContext(ChatContext);
    const messageListRef = useRef<HTMLDivElement | null>(null);
    const [isSummaryOpen, setIsSummaryOpen] = useState(false);
    const [enableWebSearch, setEnableWebSearch] = useState(false);
    const [isSmallWindowOpen, setIsSmallWindowOpen] = useState(false);

    useEffect(() => {
        if (chatContext.selectedSession?.messages.length && chatContext.selectedSession.messages.length > 0) {
            scrollToLastMessage();
        }
    }, [chatContext.selectedSession?.messages.length]);

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
    function handleSummarizeClick(): void {
        setIsSmallWindowOpen(true);
    }

    function handleSmallWindowClose(): void {
        setIsSmallWindowOpen(false);
    }


    return (
        <div className="chatbot-window-container">
            {isSmallWindowOpen ? <SmallWindow onClose={handleSmallWindowClose} /> : null}

            {/*{!chatContext.selectedSession?.summary ? null :*/}
            {/*    <div className={[*/}
            {/*        "session-summary-wrapper",*/}
            {/*        isSummaryOpen ? "open" : undefined,*/}
            {/*    ].filter(Boolean).join(" ")}>*/}
            {/*        <SessionSummary*/}
            {/*            sessionId={chatContext.selectedSession.id}*/}
            {/*            summary={chatContext.selectedSession.summary}*/}
            {/*            onClose={handleClose}*/}
            {/*            onDeleteSession={handleDeleteSession}*/}
            {/*        />*/}
            {/*    </div>*/}
            {/*}*/}

            <div className="chatbot-window-header">
                <span>{chatContext.selectedSession?.label}</span>
                <div className="copy-button">
                    <CommonButton
                        onClick={() => {
                            navigator.clipboard.writeText(chatContext.selectedSession?.id ?? "");
                        }}
                    >
                        <ChatbotIcons.SVGDocument/>
                        Copy Session ID
                    </CommonButton>
                </div>
                {/*<span style={{color: "gray"}}>{chatContext.selectedSession?.id}</span>*/}

                <div className="spacer"/>
                <div className="summarize-button">
                    <CommonButton
                        onClick={handleSummarizeClick}
                        title="Summarize the session."
                    >
                        <ChatbotIcons.SVGSend/>
                        Summarize
                    </CommonButton>

                </div>
            </div>


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
                    <LoadingBar/>
                    <span>{chatContext.chatLoadingMessage ? chatContext.chatLoadingMessage : "\u200B"}</span>
                </div>
            }
        </div>
    );
}
