"use client";
import { CommonButton, ElevaiteIcons } from "@repo/ui/components";
import "./Tabs.scss";
import { useState } from "react";





export function Tabs(): JSX.Element {
    const [selectedTab, setSelectedTab] = useState<string|undefined>();

    const testTabs = [
        { id: "CASE200081", label: "CASE200081", onClick: handleClick, onClose: handleClose, hasAlert: true},
        { id: "CASE23114", label: "CASE23114", onClick: handleClick, onClose: handleClose, },
        { id: "CASEALONGNAME AND MORE TO BOOT", label: "CASEALONGNAME AND MORE TO BOOT", onClick: handleClick, onClose: handleClose, },
        { id: "CASE 4", label: "CASE 4", onClick: handleClick, onClose: handleClose, },
        { id: "CASE20034556", label: "CASE20034556", onClick: handleClick, onClose: handleClose, hasAlert: true },
        { id: "NOT A CASE", label: "NOT A CASE", onClick: handleClick, onClose: handleClose, },
        // { id: "CASE 42", label: "CASE 4", onClick: handleClick, onClose: handleClose, },
        // { id: "CASE200345562", label: "CASE20034556", onClick: handleClick, onClose: handleClose, hasAlert: true},
        // { id: "NOT A CASE2", label: "NOT A CASE", onClick: handleClick, onClose: handleClose, },
        // { id: "CASE 423", label: "CASE 4", onClick: handleClick, onClose: handleClose, },
        // { id: "CASE2003455623", label: "CASE20034556", onClick: handleClick, onClose: handleClose, },
        // { id: "NOT A CASE23", label: "NOT A CASE", onClick: handleClick, onClose: handleClose, },
        // { id: "CASE 4234", label: "CASE 4", onClick: handleClick, onClose: handleClose, },
        // { id: "CASE20034556234", label: "CASE20034556", onClick: handleClick, onClose: handleClose, },
        // { id: "NOT A CASE234", label: "NOT A CASE", onClick: handleClick, onClose: handleClose, },
    ]

    function handleClick(id: string): void {
        setSelectedTab(id);
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
                    {props.hasAlert ? <div className="green"/> : undefined}
                </div>
                <span className="tab-label" title={props.label}>{props.label}</span>
                <CommonButton
                    className="close"
                    onClick={handleClose}
                >
                    <ElevaiteIcons.SVGXmark/>
                </CommonButton>
            </div>
        :
            <CommonButton
                className="tab-container"
                onClick={handleClick}
                overrideClass
            >
                <div className="alert">
                    {props.hasAlert ? <div className="green"/> : undefined}
                </div>
                <span className="tab-label" title={props.label}>{props.label}</span>
            </CommonButton>
    );
}

