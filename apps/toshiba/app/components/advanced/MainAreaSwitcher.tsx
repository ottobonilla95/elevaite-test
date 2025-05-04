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

export function MainAreaSwitcher({ isSidebarCollapsed }): JSX.Element {
    const chatContext = useChat();
    const [activeWindow, setActiveWindow] = useState<React.ReactNode[]>([]);

    // console.log("activeWindow", activeWindow);
    // console.log("chatcontext", chatContext.activeWindowGrid);

    useEffect(() => {
        if (chatContext.activeWindowGrid === undefined) {
            getActiveWindow(WindowGrid.toshiba1);
        } else {
            getActiveWindow(chatContext.activeWindowGrid);
        }
    }, [chatContext.activeWindowGrid]);
    // console.log("open", isSidebarCollapsed)
    function getActiveWindow(type?: WindowGrid): void {
        switch (type) {
            case WindowGrid.closed:
                setActiveWindow([
                    <div key="tabs" className="tabs"><Tabs /></div>,
                    <div key="case-details" className="case-details"><CaseDetails /></div>,
                    <div key="chat" className="chat"><CoPilot noUpload><ChatbotWindow noSession noSummary /></CoPilot></div>,
                    <div key="summary" className="summary"><CaseSummary /></div>,
                    <div key="chat-input" className="chat-input"><ChatbotInput noSummarize /></div>
                ]);
                break;

            case WindowGrid.active:
                // This is the active chat interface for ongoing conversations
                setActiveWindow([
                    <div key="chat" className="chat">
                        <CoPilot>
                            <ChatbotWindow
                                noSession
                                noSummary
                            />
                        </CoPilot>
                    </div>,
                    <div key="chat-input" className="chat-input">
                        <ChatbotInput noSummarize placeholder="Write a message..." />
                    </div>
                ]);
                break;

            case WindowGrid.dashboard:
                setActiveWindow([
                    <div key="chat" className="chat"><CoPilot noUpload label="Chat Session"><ChatbotWindow noSession noSummary /></CoPilot></div>,
                    <div key="feedback" className="chat-feedback"><ChatFeedback /></div>
                ]);
                break;

            case WindowGrid.discover:
                setActiveWindow([
                    <div key="title" className="title"><span>Discover</span></div>,
                    <div key="discover" className="discover"><Discover /></div>,
                    <div key="chat" className="chat"><CoPilot noUpload label="Agent AI"><ChatbotWindow noSession noSummary /></CoPilot></div>,
                    <div key="chat-input" className="chat-input"><ChatbotInput noSummarize /></div>
                ]);
                break;

            case WindowGrid.toshiba1:
                // This is the welcome screen / new chat screen
                setActiveWindow([
                    <div key="toshiba1" className="toshiba1">
                        <CoPilot noUpload label="What can I help with?">
                            <CoPilotStart
                                wide
                                addedControls
                                inputPlaceholder="Write a message..."
                                inlinePrompts={[
                                    "Part Number lookUp",
                                    "Diagnostic Code Lookup",
                                    "Troubleshooting"
                                ]}
                            />
                        </CoPilot>
                    </div>,
                ]);
                break;

            case WindowGrid.toshiba2:
                setActiveWindow([
                    <div key="tabs" className="tabs"><Tabs /></div>,
                    <div key="case-details" className="case-details"><CaseDetails /></div>,
                    <div key="chat" className="chat"><CoPilot noUpload><ChatbotWindow noSession noSummary /></CoPilot></div>,
                    <div key="summary" className="summary"><CaseSummary /></div>,
                    <div key="chat-input" className="chat-input"><ChatbotInput noSummarize /></div>
                ]);
                break;

            case undefined:
                // Default to welcome screen when no specific layout is set
                setActiveWindow([
                    <div key="toshiba1" className="toshiba1">
                        <CoPilot noUpload label="What can I help with?">
                            <CoPilotStart
                                wide
                                addedControls
                                inputPlaceholder="Write a message..."
                                inlinePrompts={[
                                    "Tell me about your capabilities",
                                    "Help me solve a problem",
                                    "Generate some creative content"
                                ]}
                            />
                        </CoPilot>
                    </div>,
                ]);
                break;
        }
    }

    function handlePromptClick(prompt: string): void {
        // Add a new session if needed
        if (!chatContext.selectedSession) {
            chatContext.addNewSession();
        }

        // Add the message and switch to active chat
        chatContext.addNewUserMessageToCurrentSession(prompt);
        chatContext.setActiveWindowGrid(WindowGrid.active);
    }

    return (
        <div className={["main-area-switcher-container", chatContext.activeWindowGrid ?? "toshiba1", isSidebarCollapsed ? "sidebar-collapsed" : "sidebar-expanded"].filter(Boolean).join(" ")}>
            {activeWindow.map(component => component)}
        </div>
    );
}