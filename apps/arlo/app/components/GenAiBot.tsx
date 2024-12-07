import type { CommonSelectOption } from "@repo/ui/components";
import { CommonSelect } from "@repo/ui/components";
import { useContext } from "react";
import { ChatBotGenAI, defaultGenAIBotOption } from "../lib/interfaces";
import { ChatContext } from "../ui/contexts/ChatContext";
import "./GenAiBot.scss";


const genAIBotOptions: CommonSelectOption[] = [
    // { value: ChatBotGenAI.Pan, label: "Hardware Firewall Provider", selectedLabel: "Firewall" },
    // { value: ChatBotGenAI.Cisco, label: "Collaboration Provider", selectedLabel: "Collab" },
    { value: ChatBotGenAI.CiscoClo, label: "Product Support" },
    { value: ChatBotGenAI.Creative, label: "Ideate to Create" },
    { value: ChatBotGenAI.BGPInsights, label: "Contracts and Billing" }
];




export function GenAiBot(): JSX.Element {
    const chatContext = useContext(ChatContext);


    function handleBotChange(value: ChatBotGenAI): void {
        chatContext.setSelectedGenAIBot(value);
    }


    return ( void 0

    );
}