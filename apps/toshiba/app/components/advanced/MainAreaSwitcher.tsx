"use client";
import { useEffect, useState } from "react";
import { WindowGrid } from "../../lib/interfaces";
import { useChat } from "../../ui/contexts/ChatContext";
import { ChatbotInput } from "../ChatbotInput";
import { ChatbotWindow } from "../ChatbotWindow";
import { CaseDetails } from "./CaseDetails";
import { CaseSummary } from "./CaseSummary";
import { CaseSummaryBlock } from "./CaseSummaryBlock";
import { ContactDetails } from "./ContactDetails";
import { CoPilot } from "./CoPilot";
import { CoPilotStart } from "./CoPilotStart";
import "./MainAreaSwitcher.scss";
import { Recents } from "./Recents";
import { Discover } from "./Discover";
import { Tabs } from "./Tabs";
import { ChatFeedback } from "./ChatFeedback";



export function MainAreaSwitcher(): JSX.Element {
    const chatContext = useChat();
    const [activeWindow, setActiveWindow] = useState<React.ReactNode[]>([]);


    useEffect(() => {
        getActiveWindow(chatContext.activeWindowGrid);
    }, [chatContext.activeWindowGrid]);



    function getActiveWindow(type?: WindowGrid): void {        
        switch(type) {
            
            case WindowGrid.closed:
                setActiveWindow([
                    <div key="tabs" className="tabs"><Tabs/></div>,
                    <div key="case-details" className="case-details"><CaseDetails/></div>,
                    <div key="chat" className="chat"><CoPilot noUpload><ChatbotWindow noSession noSummary/></CoPilot></div>,
                    <div key="summary" className="summary"><CaseSummary/></div>,
                    <div key="chat-input" className="chat-input"><ChatbotInput noSummarize/></div>
                ]);
            break;

            case WindowGrid.active:
                setActiveWindow([
                    // <div key="tabs" className="tabs"><Tabs/></div>,
                    // <div key="contact-details" className="contact-details"><ContactDetails/></div>,
                    // <div key="chat" className="chat"><CoPilot><CaseSummaryBlock/><ChatbotWindow noSession noSummary/></CoPilot></div>,
                    <div key="chat" className="chat"><CoPilot><ChatbotWindow noSession noSummary/></CoPilot></div>,
                    // <div key="recents" className="recents"><Recents/></div>,
                    <div key="chat-input" className="chat-input"><ChatbotInput noSummarize/></div>
                ]);
            break;

            case WindowGrid.dashboard:
                setActiveWindow([
                    <div key="chat" className="chat"><CoPilot noUpload label="Chat Session"><ChatbotWindow noSession noSummary/></CoPilot></div>,
                    <div key="feedback" className="chat-feedback"><ChatFeedback/></div>
                ]);
            break;

            case WindowGrid.discover:
                setActiveWindow([
                    <div key="title" className="title"><span>Discover</span></div>,
                    <div key="discover" className="discover"><Discover/></div>,
                    <div key="chat" className="chat"><CoPilot noUpload label="Agent AI"><ChatbotWindow noSession noSummary/></CoPilot></div>,
                    <div key="chat-input" className="chat-input"><ChatbotInput noSummarize/></div>
                ]);
            break;

            case WindowGrid.toshiba1:
                setActiveWindow([                    
                    <div key="toshiba1" className="toshiba1">
                        <CoPilot noUpload label="AI Assist">
                            <CoPilotStart
                                wide
                                addedControls
                                inputPlaceholder="Type message here"
                                inlinePrompts={[
                                    "Need help with account setup?",
                                    "Resetting user permissions?",
                                    "Summarize Case"
                                ]}
                            />
                        </CoPilot>
                    </div>,
                ]);
            break;

            case WindowGrid.toshiba2:
                setActiveWindow([
                    <div key="tabs" className="tabs"><Tabs/></div>,
                    <div key="case-details" className="case-details"><CaseDetails/></div>,
                    <div key="chat" className="chat"><CoPilot noUpload><ChatbotWindow noSession noSummary/></CoPilot></div>,
                    <div key="summary" className="summary"><CaseSummary/></div>,
                    <div key="chat-input" className="chat-input"><ChatbotInput noSummarize/></div>
                ]);
            break;

            case undefined:
                setActiveWindow([
                    <div key="tabs" className="tabs"><Tabs/></div>,
                    <div key="contact-details" className="contact-details"><ContactDetails/></div>,
                    <div key="recents" className="recents"><Recents/></div>,
                    <div key="co-pilot" className="co-pilot"><CoPilot><CoPilotStart/></CoPilot></div>,
                ]);
            break;
            
            // Without default, Typescript lets you know if a case is unhandled.
            // default:
            //     setActiveWindow([
            //         <div key="tabs" className="tabs"><Tabs/></div>,
            //         <div key="contact-details" className="contact-details"><ContactDetails/></div>,
            //         <div key="recents" className="recents"><Recents/></div>,
            //         <div key="co-pilot" className="co-pilot"><CoPilot><CoPilotStart/></CoPilot></div>,
            //     ]);
        }
    }


    return (
        <div className={["main-area-switcher-container", chatContext.activeWindowGrid ?? "co-pilot"].filter(Boolean).join(" ")}>
            {activeWindow.map(component => component)}
        </div>
    );
}