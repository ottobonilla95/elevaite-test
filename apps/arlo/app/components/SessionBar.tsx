"use client"
import { ChatbotIcons, CommonButton } from "@repo/ui/components";
import {useContext, useState} from "react";
import type { SessionObject } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./SessionBar.scss";
import { GenAiBot } from "./GenAiBot";







export function SessionBar(): JSX.Element {
    const chatContext = useContext(ChatContext);

    function handleNewSession(): void {
        chatContext.addNewSession();
    }

    function handleClearAll(): void {
        chatContext.clearAllSessions();
    }

    function handleSessionClick(sessionId: string): void {
        chatContext.setSelectedSession(sessionId);
    }

    //  function handleToggleChange(): void {
    //     setEnableWebSearch(!enableWebSearch);
    // }



    return (
        <div className="session-bar-container">
            <GenAiBot/>


            <div className="session-bar-main">

                <CommonButton
                    className="session-button new"
                    onClick={handleNewSession}
                >
                    <ChatbotIcons.SVGAdd/>
                    <span>New Session</span>
                </CommonButton>
                <CommonButton
                    className="session-button clear"
                    onClick={handleClearAll}
                >
                    <ChatbotIcons.SVGClear/>
                    <span>Clear All</span>
                </CommonButton>
        {/*<div className="chatbot-window-footer">*/}
        {/*  <label>*/}
        {/*    Enable web search*/}
        {/*    <input*/}
        {/*      type="checkbox"*/}
        {/*      checked={chatContext.enableWebSearch}*/}
        {/*      onChange={handleToggleChange}*/}
        {/*    />*/}
        {/*  </label>*/}
        {/*</div>*/}



                <div className="spacer"/>


                <div className="session-list-container">

                    <div className="session-list-header">
                        <ChatbotIcons.SVGSessions/>
                        <span>Sessions</span>
                    </div>


                    <div className="session-list-scroller">
                        <div className="session-list-contents">
                            {chatContext.sessions.map(item =>
                                <SessionListItem
                                    key={item.id}
                                    onClick={handleSessionClick}
                                    selectedSessionId={chatContext.selectedSession?.id}
                                    {...item}
                                />
                            )}
                        </div>
                    </div>

                </div>


            </div>

        </div>
    );
}


function SessionListItem(props: SessionObject & {
    onClick: (id: string) => void,
    selectedSessionId?: string
}): JSX.Element {
    return (
        <CommonButton
            onClick={() => {
                props.onClick(props.id);
            }}
            className={[
                "session-list-item",
                props.selectedSessionId && props.selectedSessionId === props.id ? "active" : undefined,
            ].filter(Boolean).join(" ")}
            overrideClass
        >
            <ChatbotIcons.SVGMessage/>
            <span title={props.label}>{props.label}</span>
        </CommonButton>
    );
}