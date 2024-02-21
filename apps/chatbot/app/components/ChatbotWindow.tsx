"use client";
import { LoadingBar } from "@repo/ui/components";
import { useContext, useEffect, useRef } from "react";
import { ChatContext } from "../ui/contexts/ChatContext";
import { ChatMessage } from "./ChatMessage";
import "./ChatbotWindow.scss";



export function ChatbotWindow(): JSX.Element {
    const chatContext = useContext(ChatContext);
    const messageListRef = useRef<HTMLDivElement|null>(null);


    useEffect(() => {
        if (chatContext.selectedSession?.messages.length && chatContext.selectedSession.messages.length > 0) {
            scrollToLastMessage();
        }
    }, [chatContext.selectedSession?.messages.length]);



    function scrollToLastMessage(): void {
        if (!messageListRef.current) return;
        messageListRef.current.scrollIntoView({ behavior: "smooth", block: "end", inline: "nearest" });
    }



    return (
        <div className="chatbot-window-container">

            <div className="chatbot-window-header">
                <span>{chatContext.selectedSession?.label}</span>
            </div>


            <div className="chatbot-window-scroller">

                <div className="chatbot-window-message-list" ref={messageListRef}>

                    {chatContext.selectedSession?.messages.length === 0 ? null :
                        chatContext.selectedSession?.messages.map(message => 
                            <ChatMessage key={message.id} {...message} />
                        )
                    }

                </div>

            </div>

            {!chatContext.isChatLoading ? null : 
                <div className="chatbot-window-loader">
                    <LoadingBar/>
                    <span>{chatContext.chatLoadingMessage ? chatContext.chatLoadingMessage : "\u200B"}</span>
                </div>
            }


        </div>
    );
}