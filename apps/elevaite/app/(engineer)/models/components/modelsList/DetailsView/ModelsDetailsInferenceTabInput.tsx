import { useEffect, useRef, useState } from "react";
import "./ModelsDetailsInferenceTabInput.scss";
import { CommonButton, CommonDialog, CommonInput, ElevaiteIcons, SimpleInput, SimpleTextarea } from "@repo/ui/components";
import { useAutosizeTextArea } from "../../../../../lib/hooks";


enum SpecialHandlingTasks {
    SentenceSimilarity = "sentence-similarity",
    Summarization = "summarization",
    QuestionAnswering = "question-answering",
    TextGeneration = "text-generation",
};

enum InputNames {
    Source = "source",
    Testing = "testing",
    Summary = "summary",
    Question = "question",
    Context = "context",
    Prompt = "prompt",
    Query = "query",
    Text = "text",
}

const wrapperDefaults = {
    pre: "<s><INST>",
    post: "</INST></s>",
}

interface TaskStructure {
    type: SpecialHandlingTasks | "default";
    inputs: TaskStructureInput[],
}

interface TaskStructureInput {
    name: InputNames;
    value: string;
    placeholder: string;
    mandatory?: boolean;
    isTextField?: boolean;
}

const taskStructure: TaskStructure[] = [
    {
        type: SpecialHandlingTasks.SentenceSimilarity,
        inputs: [
            { name: InputNames.Source, value: "", placeholder: "Enter source sentence", mandatory: true },
            { name: InputNames.Testing, value: "", placeholder: "Enter testing sentence", mandatory: true },
        ],
    },
    {
        type: SpecialHandlingTasks.Summarization,
        inputs: [
            { name: InputNames.Summary, value: "", placeholder: "Enter text to be summarized", mandatory: true, isTextField: true },
        ],
    },
    {
        type: SpecialHandlingTasks.QuestionAnswering,
        inputs: [
            { name: InputNames.Question, value: "", placeholder: "Enter question", mandatory: true },
            { name: InputNames.Context, value: "", placeholder: "Enter context", mandatory: true },
        ],
    },
    {
        type: SpecialHandlingTasks.TextGeneration,
        inputs: [
            { name: InputNames.Prompt, value: "", placeholder: "Enter prompt", mandatory: true },
            { name: InputNames.Query, value: "", placeholder: "Enter query", mandatory: true },
            { name: InputNames.Context, value: "", placeholder: "Enter context", mandatory: false },
        ],
    },
];

const defaultTaskStructure: TaskStructure = {
    type: "default",
    inputs: [
        { name: InputNames.Text, value: "", placeholder: "Enter text", mandatory: true },
    ],
}




interface ModelsDetailsInferenceTabInputProps {
    task?: string | null;
    onSend: (userMessage: string, primary: string, secondary?: string) => void;
    loading?: boolean;
}

export function ModelsDetailsInferenceTabInput(props: ModelsDetailsInferenceTabInputProps): JSX.Element {
    const textAreaRef = useRef<HTMLTextAreaElement>(null);
    const [activeStructure, setActiveStructure] = useState<TaskStructure>(defaultTaskStructure);
    const [hasErrors, setHasErrors] = useState(false);
    const [isSettingsOpen, setIsSettingsOpen] = useState(false);
    const [textGenWrapper, setTextGenWrapper] = useState({pre: wrapperDefaults.pre, post: wrapperDefaults.post});
    const [displayPre, setDisplayPre] = useState(wrapperDefaults.pre);
    const [displayPost, setDisplayPost] = useState(wrapperDefaults.post);


    useAutosizeTextArea(textAreaRef.current, activeStructure.inputs[0]?.value ?? "");

    useEffect(() => {
        setIsSettingsOpen(false);
        initializeStructure(props.task);
    }, [props.task]);

    useEffect(() => {
        setDisplayPost(textGenWrapper.post);
        setDisplayPre(textGenWrapper.pre);
    }, [textGenWrapper]);


    function initializeStructure(task?: string | null): void {
        const foundTaskStructure = taskStructure.find(item => item.type === task);
        if (foundTaskStructure) setActiveStructure(JSON.parse(JSON.stringify(foundTaskStructure)) as TaskStructure);
        else setActiveStructure(JSON.parse(JSON.stringify(defaultTaskStructure)) as TaskStructure);
    }

    function handleTextChange(text: string, input: TaskStructureInput): void {
        setActiveStructure(current => {
            const updatedInputs = current.inputs.map(item =>
                item.name === input.name ? { ...item, value: text } : item
            );
            return { ...current, inputs: updatedInputs };
        });
    }

    function formatUserMessage(details: TaskStructure): string {
        switch (details.type) {
            case SpecialHandlingTasks.SentenceSimilarity: {
                const sourceValue = details.inputs.find(input => input.name === InputNames.Source)?.value;
                const testingValue = details.inputs.find(input => input.name === InputNames.Testing)?.value;
                return `Source sentence: ${sourceValue ?? ""}\nTesting sentence: ${testingValue ?? ""}`
            }
            case SpecialHandlingTasks.QuestionAnswering: {
                const questionValue = details.inputs.find(input => input.name === InputNames.Question)?.value;
                const contextValue = details.inputs.find(input => input.name === InputNames.Context)?.value;
                return `Context: ${contextValue ?? ""}\nQuestion: ${questionValue ?? ""}`
            }
            case SpecialHandlingTasks.TextGeneration: {
                const promptValue = details.inputs.find(input => input.name === InputNames.Prompt)?.value;
                const queryValue = details.inputs.find(input => input.name === InputNames.Query)?.value;
                const contextValue = details.inputs.find(input => input.name === InputNames.Context)?.value;
                return `Prompt: ${promptValue ?? ""}\n${queryValue ? ["Query: ", queryValue].join("") : ""}\n${contextValue ? ["Context: ", contextValue].join("") : ""}`
            }
            case SpecialHandlingTasks.Summarization: {
                const summaryValue = details.inputs.find(input => input.name === InputNames.Summary)?.value;
                return summaryValue ?? "";
            }
            case "default": {
                const primaryValue = details.inputs.find(input => input.name === InputNames.Text)?.value;
                return primaryValue ?? "";
            }
            default: return "";
        }
    }

    function formatTextGeneration(details: TaskStructure): string {
        const promptValue = details.inputs.find(input => input.name === InputNames.Prompt)?.value;
        if (!promptValue) return "";
        const queryValue = details.inputs.find(input => input.name === InputNames.Query)?.value;
        const contextValue = details.inputs.find(input => input.name === InputNames.Context)?.value;

        const formattedMessageArray: string[] = [textGenWrapper.pre];
        formattedMessageArray.push(promptValue);
        if (queryValue) formattedMessageArray.push(` Query: ${queryValue}`);
        if (contextValue) formattedMessageArray.push(` Context: ${contextValue}`);
        formattedMessageArray.push(textGenWrapper.post);
        return formattedMessageArray.join("");
    }

    function handleKeyDown(key: string): void {
        if (key === "Enter") handleSend();
    }


    function handleSettingsClick(): void {
        setIsSettingsOpen(true);
    }

    function handleSettingsChange(): void {
        setIsSettingsOpen(false);
        setTextGenWrapper({pre: displayPre, post: displayPost});
    }


    function handleSend(): void {
        if (props.loading) return;
        setHasErrors(false);

        for (const input of activeStructure.inputs) {
            if (input.mandatory && !input.value.trim()) {
                setHasErrors(true);
                return;
            }
        }
        
        if (props.task === SpecialHandlingTasks.TextGeneration) {
            props.onSend(formatUserMessage(activeStructure), formatTextGeneration(activeStructure));
        } else {
            const spreadInputs = activeStructure.inputs.map(input => input.value);
            props.onSend(formatUserMessage(activeStructure), spreadInputs[0] ?? "", spreadInputs[1]);
        }
        initializeStructure(props.task);
    }


    return (
        <div className="models-details-inference-tab-input-container">

            <div className="chat-input-container">
                {activeStructure.inputs.map(input =>
                    input.isTextField ? 
                    <SimpleTextarea
                        key={input.name}
                        passedRef={textAreaRef}
                        wrapperClassName={["chat-input-field", hasErrors && input.mandatory && !input.value.trim() ? "error" : undefined].filter(Boolean).join(" ")}
                        value={input.value}
                        onChange={(text) => { handleTextChange(text, input); }}
                        onKeyDown={handleKeyDown}
                        placeholder={props.loading ? "Please wait..." : input.placeholder}
                        disabled={props.loading}
                        title={hasErrors && input.mandatory && !input.value.trim() ? "This field is required." : ""}
                    />
                    :
                    <SimpleInput
                        key={input.name}
                        wrapperClassName={["chat-input-field", hasErrors && input.mandatory && !input.value.trim() ? "error" : undefined].filter(Boolean).join(" ")}
                        value={input.value}
                        onChange={(text) => { handleTextChange(text, input); }}
                        onKeyDown={handleKeyDown}
                        placeholder={props.loading ? "Please wait..." : input.placeholder
                        }
                        disabled={props.loading}
                        title={hasErrors && input.mandatory && !input.value.trim() ? "This field is required." : ""}
                    />
                )}
            </div>

            <div className="chat-input-controls">
                {activeStructure.type !== SpecialHandlingTasks.TextGeneration ? undefined :
                    <CommonButton
                        className="chat-input-settings"
                        onClick={handleSettingsClick}
                    >
                        <ElevaiteIcons.SVGSettings/>
                    </CommonButton>
                }
                <CommonButton
                    className={["chat-input-send", props.loading ? "loading" : ""].filter(Boolean).join(" ")}
                    onClick={handleSend}
                    disabled={props.loading}
                >
                    {props.loading ?
                        <ElevaiteIcons.SVGSpinner/> :
                        <ElevaiteIcons.SVGSend/>
                    }
                </CommonButton>
            </div>


            {!isSettingsOpen ? undefined :
                <CommonDialog
                    title="Text Generation wrapper"
                    onConfirm={handleSettingsChange}
                    onCancel={() => { setIsSettingsOpen(false); } }

                >
                    <CommonInput
                        label="Prefix"
                        initialValue={textGenWrapper.pre}
                        onChange={setDisplayPre}
                        placeholder={wrapperDefaults.pre}
                    />
                    <CommonInput
                        label="Postfix"
                        initialValue={textGenWrapper.post}
                        onChange={setDisplayPost}
                        placeholder={wrapperDefaults.post}
                    />
                </CommonDialog>
            }
        </div>
    );
}