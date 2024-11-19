"use client"
import { useContext } from "react";
import { ChatbotInput } from "./components/ChatbotInput";
import { ChatbotWindow } from "./components/ChatbotWindow";
import { ChatContext } from "./ui/contexts/ChatContext"; 
import "./page.scss";




export default function Chatbot(): JSX.Element {

  const chatContext = useContext(ChatContext);

  return (
    <main className="chatbot-main-container">
      <ChatbotWindow/>
      <div className={chatContext.selectedSession?.messages.length === 0 ? "center-layout": "bottom-layout"}>
        <ChatbotInput/>
      </div>
    </main>
  );
}
