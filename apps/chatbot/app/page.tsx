import { ChatbotInput } from "./components/ChatbotInput";
import { ChatbotWindow } from "./components/ChatbotWindow";
import "./page.scss";




export default function Chatbot(): JSX.Element {



  return (
    <main className="chatbot-main-container">
      <ChatbotWindow/>

      <ChatbotInput/>
    </main>
  );
}
