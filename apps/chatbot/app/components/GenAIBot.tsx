import { CommonSelect, CommonSelectOption } from "@repo/ui/components";
import { useContext } from "react";
import { ChatBotGenAI, defaultGenAIBotOption } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./GenAIBot.scss";


const genAIBotOptions: CommonSelectOption[] = [
    { value: ChatBotGenAI.NETGEAR, label: "Network Devices Provider", selectedLabel: "Network" },
    { value: ChatBotGenAI.NETSKOPE, label: "Edge Security Provider", selectedLabel: "Edge" },
    { value: ChatBotGenAI.PAN, label: "Hardware Firewall Provider", selectedLabel: "Firewall" },
    { value: ChatBotGenAI.CISCO, label: "Collaboration Provider", selectedLabel: "Collab" },
    { value: ChatBotGenAI.CISCO_CLO, label: "CLO" },
    { value: ChatBotGenAI.ARLO, label: "Arlo" },
    // { value: ChatBotGenAI.JUNIPER, label: "" },
];




export function GenAIBot(): JSX.Element {
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
                anchor={"right"}
                defaultValue={defaultGenAIBotOption}
            />
        </div>
    );
}