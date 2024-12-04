"use client";
import { ChatbotIcons, CommonButton, SimpleInput } from "@repo/ui/components";
import { useContext, useState } from "react";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./ChatbotInput.scss";
import "./MarkdownMessage.scss";
// import { jsPDF } from "jspdf";
// import { marked } from "marked";
// import html2canvas from "html2canvas";


export function ChatbotInput(): JSX.Element {
    const chatContext = useContext(ChatContext);
    const [text, setText] = useState("");

    function handleTextChange(value: string): void {
        if (chatContext.isChatLoading) return;
        setText(value);
    }

    function handleSend(): void {
        if (chatContext.isChatLoading) return;
        const workingText = text;
        setText("");
        if (!workingText.trim()) return;
        chatContext.addNewUserMessageWithLastMessages(workingText)
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSend();
    }

    function handleSummarize(): void {
        if (chatContext.isChatLoading) return;
        chatContext.getSessionSummary();
    }
    async function handleExport(): Promise<void> {
        // const { selectedSession } = chatContext;
        // if (!selectedSession || selectedSession.messages.length === 0) return;
    
        // const doc = new jsPDF();
        // const pageWidth = doc.internal.pageSize.getWidth();
        // const pageHeight = doc.internal.pageSize.getHeight();
        // const margin = 15;
        // let yPosition = margin;
    
        // // Create and append style element (CSS remains the same as before)
        // const styleElement = document.createElement("style");
        // styleElement.innerHTML = `
        // `;
        // document.head.appendChild(styleElement);
    
        // for (const message of selectedSession.messages) {
        //     const markdownText: string = message.text;
        //     console.log(markdownText);
        //     const htmlContent: string = await marked(markdownText);
            
        //     const tempDiv = document.createElement("div");
        //     tempDiv.innerHTML = htmlContent;
        //     document.body.appendChild(tempDiv);
    
        //     const canvas = await html2canvas(tempDiv);
        //     const imgData = canvas.toDataURL("image/png");
            
        //     const imgWidth = pageWidth - 2 * margin;
        //     const imgHeight = (canvas.height * imgWidth) / canvas.width;
            
        //     // Check if the image fits on the current page
        //     if (yPosition + imgHeight > pageHeight - margin) {
        //         doc.addPage();
        //         yPosition = margin;
        //     }
    
        //     doc.addImage(imgData, "PNG", margin, yPosition, imgWidth, imgHeight);
            
        //     yPosition += imgHeight + 10; // Add some space between messages
    
        //     // Add a separator line between messages
        //     if (message !== selectedSession.messages[selectedSession.messages.length - 1]) {
        //         if (yPosition + 10 > pageHeight - margin) {
        //             doc.addPage();
        //             yPosition = margin;
        //         }
        //         doc.setDrawColor(200);
        //         doc.line(margin, yPosition, pageWidth - margin, yPosition);
        //         yPosition += 10;
        //     }
    
        //     document.body.removeChild(tempDiv);
        // }
    
        // document.head.removeChild(styleElement);
        // doc.save('chat_session.pdf');
    }
    return (
        <div className={["chatbot-input-container", chatContext.isChatLoading ? "loading" : undefined].filter(Boolean).join(" ")}>
            <SimpleInput
                wrapperClassName="chatbot-input-field"
                value={text}
                onChange={handleTextChange}
                onKeyDown={handleKeyDown}
                placeholder={chatContext.isChatLoading ? "Please wait..." : "Enter text and press ENTER"}
                disabled={chatContext.isChatLoading || chatContext.isFeedbackBoxOpen}
                rightIcon={
                    <CommonButton
                        onClick={handleSend}
                        disabled={chatContext.isChatLoading}
                    >
                        {chatContext.isChatLoading ?
                            <ChatbotIcons.SVGSpinner/> :
                            <ChatbotIcons.SVGSend/>
                        }
                    </CommonButton>                    
                }
            />

            <CommonButton
                className=".export-button"
                overrideClass
                onClick={async () => {
                    // await handleExport();
                }}
            >
                <ChatbotIcons.SVGDocument/>
                {/* <span>Export</span> */}
            </CommonButton>
        </div>
    );
}