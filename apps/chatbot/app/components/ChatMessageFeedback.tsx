"use client";
import { ChatbotIcons, CommonButton, SimpleInput } from "@repo/ui/components";
import { useContext, useState } from "react";
import type { ChatMessageFileObject } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./ChatMessageFeedback.scss";



interface ChatMessageFeedbackProps {
    id: string;
    feedback?: string;
    onFeedbackSubmit?: () => void;
}

export function ChatMessageFeedback(props: ChatMessageFeedbackProps): JSX.Element {
    const chatContext = useContext(ChatContext);
    const [feedbackText, setFeedbackText] = useState(props.feedback ?? "");
    const [files, setFiles] = useState<ChatMessageFileObject[]>([]);

    function handleSubmit(): void {
        chatContext.updateMessageFeedback(props.id, feedbackText);
        if (props.onFeedbackSubmit) props.onFeedbackSubmit();
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSubmit();
    }

    function handleUpload(): void {
        setFiles((current) => [
            ...current,
            {
                id: `testId${current.length.toString()}1`,
                filename: `Test_file_${(current.length + 1).toString()}.doc`,
            },
        ]);
    }

    function handleFileDeletion(id: string): void {
        setFiles((current) => current.filter((item) => item.id !== id));
    }

    return (
        <div className="chat-message-feedback-container">
            <div
                className={["feedback-files-container", files.length > 0 ? "open" : undefined]
                    .filter(Boolean)
                    .join(" ")}
            >
                <div className="feedback-files-accordion">
                    <div className="feedback-files-contents">
                        {files.map((file) => (
                            <FeedbackFile key={file.id} {...file} onDelete={handleFileDeletion} />
                        ))}
                    </div>
                </div>
            </div>

            <SimpleInput
                wrapperClassName={["feedback-input-field", files.length > 0 ? "open" : undefined]
                    .filter(Boolean)
                    .join(" ")}
                value={feedbackText}
                onChange={(string) => {
                    setFeedbackText(string);
                }}
                onKeyDown={handleKeyDown}
                placeholder="Add your feedback."
                rightIcon={
                    <div className="feedback-buttons">
                        <CommonButton onClick={handleUpload}>
                            <ChatbotIcons.SVGUpload />
                        </CommonButton>
                        <CommonButton onClick={handleSubmit}>
                            <ChatbotIcons.SVGSend />
                        </CommonButton>
                    </div>
                }
            />
        </div>
    );
}

function FeedbackFile(props: ChatMessageFileObject & { onDelete: (id: string) => void }): JSX.Element {
    return (
        <div className="feedback-file-container">
            <ChatbotIcons.SVGDocument />
            <span title={props.filename}>{props.filename}</span>
            <CommonButton
                onClick={() => {
                    props.onDelete(props.id);
                }}
            >
                <ChatbotIcons.SVGClose />
            </CommonButton>
        </div>
    );
}
