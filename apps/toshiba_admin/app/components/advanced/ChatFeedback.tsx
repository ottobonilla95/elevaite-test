import { useState } from "react";
import "./ChatFeedback.scss";
import { CommonButton } from "@repo/ui/components";




export function ChatFeedback(): JSX.Element {
    const [isSelectedResponse, setIsSelectedResponse] = useState(false);
    // Shift from one to the other if there's a selected Response.

    function handleKBMissing(): void {
        console.log("KB Missing clicked");
    }

    function handleIrrelevantKB(): void {
        console.log("Irrelevant KB clicked");
    }
    
    function handleIncorrectResponse(): void {
        console.log("Incorrect response clicked");
        //Test
        setIsSelectedResponse(false);
    }

    function handleApprove(): void {
        console.log("Approved!");
    }

    function handleDeny(): void {
        console.log("Denied!");
        //test
        setIsSelectedResponse(true);
    }

    return (
        <div className="chat-feedback-container">
            <div className="header">
                <span>{isSelectedResponse ? "Response Details" : "Chat Summary"}</span>
            </div>
            <div className="contents-details">
                Key points from the {isSelectedResponse ? "response" : "conversation"} will appear here.
            </div>
            {!isSelectedResponse ? 
                <div className="controls">
                    <CommonButton
                        onClick={handleApprove}
                        className="approve"
                    >Approve</CommonButton>
                    <CommonButton
                        onClick={handleDeny}
                        className="deny"
                    >Deny</CommonButton>
                </div>
            :
                <div className="controls standard">
                    <CommonButton
                        onClick={handleKBMissing}
                        title="Knowledge Base Missing"
                    >KB Missing</CommonButton>
                    <CommonButton
                        onClick={handleIrrelevantKB}
                        title="Irrelevant Knowledge Base"
                    >Irrelevant KB</CommonButton>
                    <CommonButton
                        onClick={handleIncorrectResponse}
                    >Incorrect Response</CommonButton>
                </div>
            }
        </div>
    );
}