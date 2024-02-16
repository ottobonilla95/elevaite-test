"use client";
import { useEffect, useState } from "react";
import { ChatMessageObject } from "../lib/interfaces";
import "./ChatbotWindow.scss";
import { getTestMessagesList } from "../lib/testData";
import { ChatMessage } from "./ChatMessage";

interface ChatbotWindowProps {

}

export function ChatbotWindow(props: ChatbotWindowProps): JSX.Element {
    const [messageList, setMessageList] = useState<ChatMessageObject[]>([]);


    useEffect(() => {
        setMessageList(getTestMessagesList(4));
    }, []);



    return (
        <div className="chatbot-window-container">

            <div className="chatbot-window-header">
                <span>Firmware Upgrade Case</span>
            </div>


            <div className="chatbot-window-scroller">

                <div className="chatbot-window-message-list">

                    {messageList.length === 0 ? null :
                        messageList.map(message => 
                            <ChatMessage key={message.id} {...message} />
                        )
                    }

                </div>

            </div>

        </div>
    );
}