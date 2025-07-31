import { CommonSelect, SimpleTextarea } from "@repo/ui/components";
import { useState } from "react";
import { type PromptInputItem, PromptInputTypes } from "../lib/interfaces";
import { usePrompt } from "../ui/contexts/PromptContext";
import "./PromptInput.scss";
import PromptMultiTagInputs from "./PromptMultiTagInputs";


const promptInputTypeLabels: Record<PromptInputTypes, string> = {
    [PromptInputTypes.DocumentHeader]: "Document Header",
    [PromptInputTypes.LineItemHeader]: "Line Item Header",
    [PromptInputTypes.UserFeedback]: "User Feedback",
    [PromptInputTypes.LineItems]: "Line Items",
    [PromptInputTypes.ExpectedOutput]: "Expected Output",
    // [PromptInputTypes.System]: "System",
    // [PromptInputTypes.UserInstructions]: "User Instructions",
};


type PromptInputProps = PromptInputItem;

export function PromptInput(props: PromptInputProps): JSX.Element {
    const promptContext = usePrompt();
    const [type, setType] = useState<PromptInputTypes|string>(props.type ?? "");
    // const [text, setText] = useState("");

    function handleTypeChange(value: PromptInputTypes): void {
        setType(value);
        promptContext.updatePromptInput(props.id, { type: value });
    }

    function handleTextChange(passedText: string): void {
        // setText(passedText);
        promptContext.updatePromptInput(props.id, { prompt: passedText });
    }

    function handleRemovePrommpt(): void {
        promptContext.removePromptInput(props.id);
    }


    return (
        <div className="prompt-input-container">
            <div className="prompt-input-header">
                <CommonSelect
                    className="prompt-select"
                    options={Object.entries(PromptInputTypes).map(([_key, value]) => ({
                        value,
                        label: promptInputTypeLabels[value],
                    }))}
                    controlledValue={type}
                    onSelectedValueChange={handleTypeChange}
                    noSelectionMessage="Choose type"
                    useCommonStyling
                />
                <div className="prompt-input-controls">
                    {/* <div className="prompt-input-tag">AI Assist</div> */}
                    {!promptContext.isEngineerPage ? undefined :
                        <button className="prompt-input-remove-button" onClick={handleRemovePrommpt} type="button">
                            <svg width="17" height="16" viewBox="0 0 17 16" fill="none">
                                <g opacity="0.8">
                                    <path d="M11.1667 4V3.46671C11.1667 2.71997 11.1667 2.3466 11.0213 2.06139C10.8935 1.8105 10.6895 1.60653 10.4387 1.4787C10.1534 1.33337 9.78007 1.33337 9.03333 1.33337H7.96667C7.21993 1.33337 6.84656 1.33337 6.56135 1.4787C6.31046 1.60653 6.10649 1.8105 5.97866 2.06139C5.83333 2.3466 5.83333 2.71997 5.83333 3.46671V4M7.16667 7.66671V11M9.83333 7.66671V11M2.5 4H14.5M13.1667 4V11.4667C13.1667 12.5868 13.1667 13.1469 12.9487 13.5747C12.7569 13.951 12.451 14.257 12.0746 14.4487C11.6468 14.6667 11.0868 14.6667 9.96667 14.6667H7.03333C5.91323 14.6667 5.35318 14.6667 4.92535 14.4487C4.54903 14.257 4.24307 13.951 4.05132 13.5747C3.83333 13.1469 3.83333 12.5868 3.83333 11.4667V4" stroke="#212124" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                </g>
                            </svg>
                        </button>
                    }
                </div>
            </div>

            {(type as PromptInputTypes === PromptInputTypes.DocumentHeader || type as PromptInputTypes === PromptInputTypes.LineItemHeader) ? (
                <PromptMultiTagInputs
                    placeholder="Add content..."
                    values={props.values}
                    onChange={values => { promptContext.updatePromptInput(props.id, { values }); }}
                />
            ) : (
                <SimpleTextarea
                    wrapperClassName="prompt-input"
                    value={props.prompt}
                    onChange={handleTextChange}
                    placeholder="Enter prompt text..."
                    useCommonStyling
                />
            )}
        </div>
    );
}