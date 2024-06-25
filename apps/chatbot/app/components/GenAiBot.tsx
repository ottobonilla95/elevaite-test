import type { CommonSelectOption } from "@repo/ui/components";
import { CommonSelect } from "@repo/ui/components";
import { useContext } from "react";
import { ChatBotGenAI, defaultGenAIBotOption } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./GenAiBot.scss";


const genAIBotOptions: CommonSelectOption[] = [
    { value: ChatBotGenAI.Pan, label: "Hardware Firewall Provider", selectedLabel: "Firewall" },
    { value: ChatBotGenAI.Cisco, label: "Collaboration Provider", selectedLabel: "Collab" },
    { value: ChatBotGenAI.CiscoClo, label: "CLO" },
    { value: ChatBotGenAI.ServiceNow, label: "Service Now" },
    { value: ChatBotGenAI.BGPInsights, label: "BGP Insights" }
];




export function GenAiBot(): JSX.Element {
    const chatContext = useContext(ChatContext);


    function handleBotChange(value: ChatBotGenAI): void {
        chatContext.setSelectedGenAIBot(value);
    }


    return (
        <div className="gen-ai-bot-container">
            <div className="gen-ai-label">Gen AI BOT:</div>
            <CommonSelect
                options={genAIBotOptions}
                onSelectedValueChange={handleBotChange}
                anchor="right"
                defaultValue={defaultGenAIBotOption}
            />
        </div>
    );
}