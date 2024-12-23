"use client";
import { ChatbotIcons, CommonButton, SimpleInput } from "@repo/ui/components";
import { useContext, useState, useRef } from "react";
import { ChatContext } from "../ui/contexts/ChatContext";
import FileUpload from "./FileUpload";
import { ChatbotInputProps } from "../lib/interfaces";
import "./ChatbotInput.scss";
import "./MarkdownMessage.scss";

export function ChatbotInput({ text, setText }: ChatbotInputProps):  JSX.Element {
    const chatContext = useContext(ChatContext);
    const [isExporting, setIsExporting] = useState(false);
    const [isUploading, setIsUploading] = useState(false);
    const [selectedFile, setSelectedFile] = useState<File | null>(null);

    const inputRef = useRef<HTMLInputElement | null>(null);
    const isFirstMessage = chatContext.selectedSession?.messages.length === 0;

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
    function handleButtonClick(buttonText: string): void{
        setText(buttonText);
        if (inputRef.current) {
            inputRef.current.focus();
        }
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
            const response = await fetch('http://127.0.0.1:8000/generate-pdf', {
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
                        
        <div>
                {isFirstMessage && (
                    <div className="chatbot-welcome-message">
                        <h1>How can I assist with your campaign performance or planning?</h1>
                    </div>
                )}
        
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
                            placeholder={chatContext.isChatLoading ? "Please wait..." : "Ask ElevAIte"}
                            disabled={chatContext.isChatLoading}
                            rightIcon={
                                <CommonButton
                                    onClick={handleSend}
                                    disabled={chatContext.isChatLoading}
                                >
                                    {chatContext.isChatLoading ? <ChatbotIcons.SVGSpinner /> : <ChatbotIcons.SVGSend />}
                                </CommonButton>
                            }
                            passedRef={inputRef}
                        />

                    {!isFirstMessage && (
                        <CommonButton
                        className="export-button"
                        onClick={handleExport}
                        disabled={isUploading || chatContext.isChatLoading || isExporting}>
                        {isExporting ? <ChatbotIcons.SVGSpinnerExport /> : <ChatbotIcons.SVGDownloadExport />}
                    </CommonButton>)}
            </div>
            {isFirstMessage && (
                                <div className="first-message-buttons">
                                <CommonButton onClick={() => handleButtonClick("Generate a Media plan ")}>Generate a Media plan</CommonButton>
                                <CommonButton onClick={() => handleButtonClick("Generate an Ad Creative ")}>Generate an Ad Creative</CommonButton>
                                <CommonButton onClick={() => handleButtonClick("Provide Creative Insights ")}>Provide Creative Insights</CommonButton>
                                <CommonButton onClick={() => handleButtonClick("Campaign Performance and Insights ")}>Campaign Performance and Insights</CommonButton>
                                </div>
            )}
        </div>
        
    );
}