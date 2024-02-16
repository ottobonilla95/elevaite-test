"use client"
import { ChatbotIcons, CommonButton } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { GenAIBot } from "./GenAIBot";
import "./SessionBar.scss";
import { getTestSessionsList } from "../lib/testData";
import { SessionListItem } from "../lib/interfaces";








interface SessionBarProps {

}

export function SessionBar(props: SessionBarProps): JSX.Element {
    const [sessionList, setSessionList] = useState<SessionListItem[]>();


    useEffect(() => {
        setSessionList(getTestSessionsList(3));
    }, []);



    function handleNewSession() {
        console.log("Starting new session");
    }

    function handleClearAll() {
        console.log("Clearing all sessions");
    }



    return (
        <div className="session-bar-container">
            <GenAIBot/>


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


                <div className="spacer"/>


                <div className="session-list-container">

                    <div className="session-list-header">
                        <ChatbotIcons.SVGSessions/>
                        <span>Sessions</span>
                    </div>


                    <div className="session-list-scroller">
                        <div className="session-list-contents">
                            {!sessionList ? null :
                                sessionList?.map(item => 
                                    <SessionListItem
                                        key={item.id}
                                        {...item}
                                    />
                                )
                            }
                        </div>
                    </div>

                </div>


            </div>

        </div>
    );
}






function SessionListItem(props: SessionListItem): JSX.Element {
    return (
        <div className="session-list-item">
            <ChatbotIcons.SVGMessage/>
            <span title={props.label}>{props.label}</span>
        </div>
    );
}