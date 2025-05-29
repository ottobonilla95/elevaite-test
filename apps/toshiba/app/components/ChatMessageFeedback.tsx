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
    const [addedTags, setAddedTags] = useState<string[]>([]);

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

    function handleTagClick(tag: string): void {
        // Check if the tag is already added
        if (addedTags.includes(tag)) {
            // Remove the tag from the addedTags array
            const updatedTags = addedTags.filter(t => t !== tag);

            // Extract the actual content without any tags
            let contentText = feedbackText;
            const allTags = addedTags.map(t => `[${t}]`);

            allTags.forEach(tagStr => {
                contentText = contentText.replace(tagStr, "").trim();
            });

            // Rebuild the text with the remaining tags
            const remainingTagsText = updatedTags.map(t => `[${t}]`).join(" ");
            const newText = contentText ? `${remainingTagsText} ${contentText}`.trim() : remainingTagsText;

            setFeedbackText(newText);
            setAddedTags(updatedTags);
        } else {
            // Add the tag to the text and the addedTags array
            const tagText = `[${tag}]`;

            // Extract any existing tags from the beginning of the text
            let remainingText = feedbackText;
            const existingTags = addedTags.map(t => `[${t}]`);

            // Remove existing tags from the text to get the actual content
            existingTags.forEach(tagStr => {
                remainingText = remainingText.replace(tagStr, "").trim();
            });

            // Create new text with all tags at the beginning
            const newTags = [...addedTags, tag].map(t => `[${t}]`).join(" ");
            const newText = remainingText ? `${newTags} ${remainingText}` : newTags;

            setFeedbackText(newText);
            setAddedTags([...addedTags, tag]);
        }
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

            <div className="feedback-tag-buttons">
                <CommonButton
                    onClick={() => handleTagClick("Incorrect Answer")}
                    className={addedTags.includes("Incorrect Answer") ? "active" : ""}
                >
                    Incorrect Answer
                </CommonButton>
                <CommonButton
                    onClick={() => handleTagClick("Wrong Source")}
                    className={addedTags.includes("Wrong Source") ? "active" : ""}
                >
                    Wrong Source
                </CommonButton>
                <CommonButton
                    onClick={() => handleTagClick("Incorrect Steps")}
                    className={addedTags.includes("Incorrect Steps") ? "active" : ""}
                >
                    Incorrect Steps
                </CommonButton>
            </div>
            <SimpleInput
                wrapperClassName={["feedback-input-field", files.length > 0 ? "open" : undefined]
                    .filter(Boolean)
                    .join(" ")}
                value={feedbackText}
                onChange={(string) => {
                    setFeedbackText(string);

                    // Check which tags are still present in the text
                    const possibleTags = ["Incorrect Answer", "Wrong Source", "Incorrect Steps"];
                    const presentTags = possibleTags.filter(tag => string.includes(`[${tag}]`));

                    // Update the addedTags state if it's different
                    if (JSON.stringify(presentTags.sort()) !== JSON.stringify(addedTags.sort())) {
                        setAddedTags(presentTags);
                    }
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
