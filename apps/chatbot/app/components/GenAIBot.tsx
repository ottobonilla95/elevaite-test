import { CommonSelect, CommonSelectOption } from "@repo/ui/components";
import "./GenAIBot.scss";


const genAIBotOptions: CommonSelectOption[] = [
    { value: "netgear", label: "Network Devices Provider", selectedLabel: "Network" },
    { value: "netskope", label: "Edge Security Provider", selectedLabel: "Edge" },
    { value: "pan", label: "Hardware Firewall Provider", selectedLabel: "Firewall" },
    { value: "cisco", label: "Collaboration Provider", selectedLabel: "Collab" },
    { value: "cisco_clo", label: "CLO" },
    { value: "arlo", label: "Arlo" },
    // { value: "juniper_vsrx", label: "" },
];
const defaultGenAIBotOption = "cisco_clo";



interface GenAIBotProps {

}

export function GenAIBot(props: GenAIBotProps): JSX.Element {



    function handleBotChange(value: string): void {
        console.log("Bot", value, "was selected");
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