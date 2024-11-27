import type { CommonSelectOption } from "@repo/ui/components";
import { CommonSelect } from "@repo/ui/components";
import { useContext } from "react";
import { ChatBotGenAI, defaultGenAIBotOption } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./GenAiBot.scss";


const genAIBotOptions: CommonSelectOption[] = [
    // { value: ChatBotGenAI.Pan, label: "Hardware Firewall Provider", selectedLabel: "Firewall" },
    // { value: ChatBotGenAI.Cisco, label: "Collaboration Provider", selectedLabel: "Collab" },
    { value: ChatBotGenAI.MediaPerformance, label: "Media Performance" },
    // { value: ChatBotGenAI.IdeateCreative, label: "Ideate to Create" },
    { value: ChatBotGenAI.ContractsBilling, label: "Contracts and Billing" }
];


export function GenAiBot(): JSX.Element {
    const chatContext = useContext(ChatContext);


    function handleBotChange(value: ChatBotGenAI): void {
        chatContext.setSelectedGenAIBot(value);
    }


    return (
        <div className="gen-ai-bot-container">
            {/* <div className="gen-ai-label">Gen AI Bot:</div> */}
            <CommonSelect
                options={genAIBotOptions}
                onSelectedValueChange={handleBotChange}
                anchor="right"
                defaultValue={defaultGenAIBotOption}
            />
        </div>
    );
}