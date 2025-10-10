"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import { useEffect, useState } from "react";
import { useChat } from "../../ui/contexts/ChatContext";
import "./Tabs.scss";
import { WindowGrid } from "../../../lib/interfaces";





export function Tabs(): JSX.Element {
    const chatContext = useChat();
    const [selectedTab, setSelectedTab] = useState<string | undefined>();

    const testTabs = [
        { id: "TEST01", label: "CASE200081", onClick: handleClick, onClose: handleClose, hasAlert: true },
        { id: "TEST02", label: "CASE23114", onClick: handleClick, onClose: handleClose, },
        { id: "TEST03", label: "CASEALONGNAME AND MORE TO BOOT", onClick: handleClick, onClose: handleClose, },
        { id: "CASE 4", label: "CASE 4", onClick: handleClick, onClose: handleClose, },
        { id: "TOSHIBA_1", label: "TOSHIBA 1", onClick: handleClick, onClose: handleClose, hasAlert: true },
        { id: "TOSHIBA_2", label: "TOSHIBA 2", onClick: handleClick, onClose: handleClose, },
    ];


    useEffect(() => {
        console.log("Sessions:", chatContext.sessions);
    }, [chatContext.sessions]);

    function handleClick(id: string): void {
        setSelectedTab(id);
        switch (id) {
            case "TEST01": chatContext.setActiveWindowGrid(WindowGrid.active); break;
            case "TEST02": chatContext.setActiveWindowGrid(WindowGrid.closed); break;
            case "TEST03": chatContext.setActiveWindowGrid(undefined); break;
            case "TOSHIBA_1": chatContext.setActiveWindowGrid(WindowGrid.toshiba1); break;
            case "TOSHIBA_2": chatContext.setActiveWindowGrid(WindowGrid.toshiba2); break;
        }
    }

    function handleClose(id: string): void {
        console.log("Closing", id);
    }


    return (
        <div className="tabs-container tabs-area">
            <div className="tabs-underline">
                {testTabs.map(tab =>
                    <Tab key={tab.id} {...tab} isSelected={tab.id === selectedTab} />
                )}
            </div>
        </div>
    );
}





interface TabProps {
    id: string;
    label: string;
    onClick: (id: string) => void;
    onClose: (id: string) => void;
    isSelected: boolean;
    hasAlert?: boolean;
}

function Tab(props: TabProps): JSX.Element {

    function handleClick(): void {
        props.onClick(props.id);
    }

    function handleClose(): void {
        props.onClose(props.id);
    }

    return (
        props.isSelected ?
            <div className="tab-container selected">
                <div className="alert">
                    {props.hasAlert ? <div className="green" /> : undefined}
                </div>
                <span className="tab-label" title={props.label}>{props.label}</span>
                <CommonButton
                    className="close"
                    onClick={handleClose}
                >
                    <ElevaiteIcons.SVGXmark />
                </CommonButton>
            </div>
            :
            <CommonButton
                className="tab-container"
                onClick={handleClick}
                overrideClass
            >
                <div className="alert">
                    {props.hasAlert ? <div className="green" /> : undefined}
                </div>
                <span className="tab-label" title={props.label}>{props.label}</span>
            </CommonButton>
    );
}

