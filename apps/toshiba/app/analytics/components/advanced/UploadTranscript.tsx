import { CommonButton, SimpleTextarea } from "@repo/ui/components";
import { useState } from "react";
import "./UploadTranscript.scss";




export function UploadTranscript(): JSX.Element {
    const [transcript, setTranscript] = useState("");


    function handleProcess(): void {
        console.log("Processing transcript");
    }

    function askQuestion(): void {
        console.log("Asking question");
    }


    return (
        <div className="upload-transcript-container">
            <span className="title">Please provide the transcript</span>
            <div className="transcript-area-container">
                <SimpleTextarea
                    value={transcript}
                    onChange={setTranscript}
                    wrapperClassName="transcript-area"
                />
            </div>
            <div className="controls-container">
                <CommonButton className="process" onClick={handleProcess}>Process Transcript</CommonButton>
                <CommonButton onClick={askQuestion}>Ask a Question</CommonButton>
            </div>
        </div>
    );
}