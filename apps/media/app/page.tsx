"use client"
import { useContext, useState } from "react";
import { ChatbotInput } from "./components/ChatbotInput";
import { ChatbotWindow } from "./components/ChatbotWindow";
import { ChatContext } from "./ui/contexts/ChatContext"; 
import "./page.scss";




export default function Chatbot(): JSX.Element {

  const chatContext = useContext(ChatContext);
  const [inputText, setInputText] = useState("");
  
  function parentHandleQueryClick(query: string): void {
    if (chatContext.isChatLoading) return;
    setInputText(query);
    chatContext.addNewUserMessageWithLastMessages(query);
    setInputText("");
}

  return (
    <main className="chatbot-main-container">
      <ChatbotWindow onQueryClick={parentHandleQueryClick}/>
      <div className={chatContext.selectedSession?.messages.length === 0 ? "center-layout": "bottom-layout"}>
        <ChatbotInput text={inputText} setText={setInputText} />
      </div>
    </main>
  );
}
