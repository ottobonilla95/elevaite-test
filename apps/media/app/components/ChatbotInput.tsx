"use client";
import { ChatbotIcons, CommonButton, SimpleInput } from "@repo/ui/components";
import { useContext, useState, useRef } from "react";
import { ChatContext } from "../ui/contexts/ChatContext";
import FileUpload from "./FileUpload";
import "./ChatbotInput.scss";
import "./MarkdownMessage.scss";

export function ChatbotInput(): JSX.Element {
    const chatContext = useContext(ChatContext);
    const [text, setText] = useState("");
    const [isExporting, setIsExporting] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    function handleTextChange(value: string): void {
        if (chatContext.isChatLoading) return;
        setText(value);
    }

    async function handleSend(): Promise<void>  {
        if (chatContext.isChatLoading) return;
        const workingText = text;
        setText("");
        if (!workingText.trim() && !selectedFile) return;

        try {
            console.log("Sending the file to the backend: ",selectedFile);
            await chatContext.addNewUserMessageWithLastMessages(workingText, selectedFile || undefined);
            setSelectedFile(null); // Clear the selected file after sending
        } catch (error) {
            console.error('Error sending message and file:', error);
        }
        // chatContext.addNewUserMessageWithLastMessages(workingText)
    }
    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSend();
    }
    function handleFileSelect(file: File): void {
        setSelectedFile(file);
    }
    // function handleSummarize(): void {
    //     if (chatContext.isChatLoading) return;
    //     chatContext.getSessionSummary();
    // }
    async function handleExport(): Promise<void> {
        const { selectedSession } = chatContext;
        if (!selectedSession || selectedSession.messages.length === 0) return;
    
        const markdownMessages = selectedSession.messages.map(message => message.text).join("\n\n");
        setIsExporting(true);
        try {
            const response = await fetch('http://localhost:8000/generate-pdf', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ markdown: markdownMessages }),
            });
    
            if (!response.ok) {
                throw new Error('Failed to generate PDF');
            }
    
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
    
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', 'chat_session.pdf');
    
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error exporting chat session:', error);
        } finally {
            setIsExporting(false);
        }
    }
    const isIdeatecreative = chatContext.selectedGenAIBot === "ideatecreative";
    return (
        <div className={["chatbot-input-container", chatContext.isChatLoading ? "loading" : undefined].filter(Boolean).join(" ")}>
            {/* File Preview Container (Above the Input) */}
                {selectedFile && (
                    <div className="uploaded-creative-container">
                        <button
                        className="close-icon"
                        onClick={() => setSelectedFile(null)} // Clear the selected file
                        >
                        &times; {/* X symbol */}
                        </button>
                    {selectedFile.type.startsWith("image/") || selectedFile.type === "image/gif" ? (
                        <img
                            src={URL.createObjectURL(selectedFile)}
                            alt="Uploaded Creative"
                            className="uploaded-creative"
                        />
                    ) : selectedFile.type.startsWith("video/") ? (
                        <video
                            controls
                            className="uploaded-creative"
                            src={URL.createObjectURL(selectedFile)}
                        />
                    ) : null}
                </div>
            )}
                      
            {!selectedFile && (<FileUpload
                onFileSelect={handleFileSelect}
                onUpload={() => console.log("File uploaded!")}
                isUploading={isUploading}
            />)}

            <SimpleInput
                wrapperClassName="chatbot-input-field"
                value={text}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                placeholder={chatContext.isChatLoading ? "Please wait..." : "Enter text and press ENTER"}
                disabled={chatContext.isChatLoading}
                rightIcon={
                    <CommonButton
                        onClick={handleSend}
                        disabled={chatContext.isChatLoading}
                    >
                        {chatContext.isChatLoading ? <ChatbotIcons.SVGSpinner /> : <ChatbotIcons.SVGSend />}
                    </CommonButton>
                }
            />

    
            <CommonButton
            className="export-button"
            onClick={handleExport}
            disabled={isUploading || chatContext.isChatLoading || isExporting}>
            {isExporting ? <ChatbotIcons.SVGSpinnerExport /> : <ChatbotIcons.SVGDownloadExport />}
        </CommonButton>
        </div>
    );
}