import { ChatbotIcons, CommonButton } from "@repo/ui/components";
import { useChat } from "../../ui/contexts/ChatContext";
import { ChatbotInput } from "../../../components/ChatbotInput";
import "./CoPilotStart.scss";
import { useState, useEffect } from "react";






const commonPrompts = [
    {
        prompt: "Summarize Case",
        description: "Quickly summarize the details of the active case"
    },
    {
        prompt: "Suggest Next Steps",
        description: "Get AI-driven recommendations for resolving the issue"
    },
    {
        prompt: "Analyze Customer History",
        description: "Review the customer's recent interactions and patterns"
    },
];


interface CoPilotStartProps {
    inlinePrompts?: string[];
    addedControls?: boolean;
    inputPlaceholder?: string;
    wide?: boolean;
}

export function CoPilotStart(props: CoPilotStartProps): JSX.Element {
    const chatContext = useChat();

    const [text, setText] = useState("")


    function handlePromptClick(prompt: string): void {
        chatContext.addNewUserMessageToCurrentSession(prompt);
    }

    const handleTextChange = (value: string): void => {
        if (chatContext.isChatLoading) return;
        setText(value)
    }

    function handleAddFiles() {
        console.log("Adding files");
    }

    function handleAddInstructions() {
        console.log("Adding instructions");
    }

    console.log("common", props.inlinePrompts)
    return (
        <div className={["co-pilot-start-container", props.wide ? "wide" : undefined].filter(Boolean).join(" ")}>
            <div className="info">
                <span className="query">What can I help with?</span>
                <span>Select a common prompt below to begin</span>
            </div>

            {props.inlinePrompts ? undefined :
                <div className="common-prompts-container">
                    {commonPrompts.map(prompt =>
                        <CommonButton
                            key={prompt.prompt}
                            className="common-prompt-button"
                            onClick={() => { handlePromptClick(prompt.prompt); }}
                        >
                            <span className="prompt">{prompt.prompt}</span>
                            <span>{prompt.description}</span>
                        </CommonButton>
                    )}
                </div>
            }

            <div className="input-container">
                <ChatbotInput
                    noSummarize
                    bareBones
                    placeholder={props.inputPlaceholder ?? "or type your own question"}
                    // inlinePrompts={props.inlinePrompts}
                    text={text}
                />
            </div>

            {!props.inlinePrompts ? undefined :
                <div className="added-controls-container">

                    {props.inlinePrompts.map((prompt, index) =>
                        <CommonButton
                            className="added-control"
                            noBackground
                            onClick={() => handleTextChange(prompt)}
                            key={index}
                        >
                            <span>{prompt}</span>
                        </CommonButton>
                    )}
                </div>
            }

            {/* <CommonButton className="added-control" noBackground onClick={handleAddFiles}>
                <span>Add files</span>
                <span>Chats in this project can access file content.</span>
                <ChatbotIcons.SVGAddFile />
            </CommonButton>
            <CommonButton className="added-control" noBackground onClick={handleAddInstructions}>
                <span>Add instructions</span>
                <span>Customize the response in this project.</span>
                <ChatbotIcons.SVGInstructions />
            </CommonButton> */}
        </div>
    );
}

