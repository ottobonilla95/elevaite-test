import { CommonButton } from "@repo/ui/components";
import type { SessionSummaryObject } from "../lib/interfaces";
import "./SessionSummary.scss";



interface SessionSummaryProps {
    sessionId: string;
    summary: SessionSummaryObject;
    onClose: () => void;
    onDeleteSession: (sessionId: string) => void;
}


export function SessionSummary(props: SessionSummaryProps): JSX.Element {


    function handleClose(): void {
        props.onClose();
    }

    function handleDeleteSession(): void {
        props.onDeleteSession(props.sessionId);
    }



    return (
        <div className="session-summary-container">
            <div className="session-summary-header">Session Summary</div>

            <div className="session-summary-label">Title</div>
            <div className="session-summary-text title">{props.summary.title}</div>

            <div className="session-summary-label">Problem Description</div>
            <div className="session-summary-text description">{props.summary.problem}</div>

            <div className="session-summary-label">Solution</div>
            <div className="session-summary-text solution">{props.summary.solution}</div>

            <div className="session-summary-buttons-container">
                <CommonButton
                    onClick={handleClose}
                    title="Close the summary and return to the session."
                >
                    Close
                </CommonButton>

                <CommonButton
                    onClick={handleDeleteSession}
                    className="clear-button"
                    title="Close the summary and delete this session."
                >
                    Clear Session
                </CommonButton>
            </div>

        </div>
    );
}