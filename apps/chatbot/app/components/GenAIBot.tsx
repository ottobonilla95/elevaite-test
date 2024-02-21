import type { CommonSelectOption } from "@repo/ui/components";
import { CommonSelect } from "@repo/ui/components";
import { useContext } from "react";
import { ChatBotGenAI, defaultGenAIBotOption } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./GenAiBot.scss";


const genAIBotOptions: CommonSelectOption[] = [
    { value: ChatBotGenAI.Netgear, label: "Network Devices Provider", selectedLabel: "Network" },
    { value: ChatBotGenAI.Netskope, label: "Edge Security Provider", selectedLabel: "Edge" },
    { value: ChatBotGenAI.Pan, label: "Hardware Firewall Provider", selectedLabel: "Firewall" },
    { value: ChatBotGenAI.Cisco, label: "Collaboration Provider", selectedLabel: "Collab" },
    { value: ChatBotGenAI.CiscoClo, label: "CLO" },
    { value: ChatBotGenAI.Arlo, label: "Arlo" },
    // { value: ChatBotGenAI.JUNIPER, label: "" },
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