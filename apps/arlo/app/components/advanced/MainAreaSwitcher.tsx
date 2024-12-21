"use client";
import { useEffect, useState, useContext } from "react";
import "./MainAreaSwitcher.scss";
import {ChatbotWindow} from "../ChatbotWindow.tsx";
import {ChatbotInput} from "../ChatbotInput.tsx";
import {ContactDetails} from "../ContactDetails.tsx";
import {Recents} from "../Recents.tsx";
import {ChatContext} from "../../ui/contexts/ChatContext.tsx";
import {WelcomeScreen} from "../WelcomeScreen.tsx";

export enum WindowGrid {
    active = "active-case",
    closed = "closed-case",
    welcome = "welcome-case"
}

export function MainAreaSwitcher({caseID}:{caseID:string|undefined}): JSX.Element {
    const [activeWindow, setActiveWindow] = useState<React.ReactNode[]>([]);
    const [activeGrid, setActiveGrid] = useState<WindowGrid|undefined>();
    const chatContext = useContext(ChatContext);

    useEffect(() => {
         if (chatContext.selectedSession?.chatFlow === "welcome") {
            if (caseID && caseID !== "999999") {
                console.log("Case ID:", caseID);
                chatContext.processSFChat(caseID);
                console.log("Processed Chat");
            }
         }
    }, [chatContext.selectedSession?.chatFlow]);



    useEffect(() => {
        if (chatContext.selectedSession?.chatFlow==="pasteChat") getActiveWindow(WindowGrid.active);
        else if (chatContext.selectedSession?.chatFlow==="chat") getActiveWindow(WindowGrid.closed);
        else getActiveWindow(WindowGrid.welcome);
    }, [chatContext.selectedSession?.chatFlow]);

    function getActiveGrid(type?: WindowGrid): void {
        switch(type) {
            case WindowGrid.active: setActiveGrid(WindowGrid.active); break;
            case WindowGrid.closed: setActiveGrid(WindowGrid.closed); break;
            case WindowGrid.welcome: setActiveGrid(WindowGrid.welcome); break;
            default: setActiveGrid(WindowGrid.welcome);
        }
    }

    function getActiveWindow(type?: WindowGrid): void {
        switch(type) {

            case WindowGrid.welcome:
                setActiveWindow([
                    // <div key="1" className="case-details">Test! <CommonButton onClick={() => { handleTest(type); }}>Switch</CommonButton></div>,
                    <div key="1" className="welcome-screen"><WelcomeScreen/></div>,
                    // <div key="3" className="summary"><Recents/></div>,
                ]);
            break;
            
            case WindowGrid.closed:
                setActiveWindow([
                    // <div key="1" className="case-details">Test! <CommonButton onClick={() => { handleTest(type); }}>Switch</CommonButton></div>,
                    <div key="1" className="chat"><ChatbotWindow/></div>,
                    // <div key="3" className="summary"><Recents/></div>,
                    <div key="2" className="chat-input"><ChatbotInput/></div>
                ]);
            break;

            case WindowGrid.active:
            default:
                setActiveWindow([
                    // <div key="test" className="contact-details">Test! <CommonButton onClick={() => { handleTest(type ?? WindowGrid.active); }}>Switch</CommonButton></div>,
                    <div key="test" className="contact-details"><ContactDetails/></div>,
                    <div key="test2" className="chat"><ChatbotWindow/></div>,
                    <div key="test3" className="recents"><Recents/></div>,
                    <div key="test4" className="chat-input"><ChatbotInput/></div>
                ]);
        }
        getActiveGrid(type);
    }


    return (
        <div className={["main-area-switcher-container", activeGrid].filter(Boolean).join(" ")}>
            {activeWindow.map(component => component)}
        </div>
    );
}