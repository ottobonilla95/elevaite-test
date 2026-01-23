import { CommonSelect, type CommonSelectOption } from "@repo/ui";
import Image from "next/image";
import React, { useMemo, type JSX } from "react";
import { Icons } from "../icons";
import claudeLogo from "../icons/logos/claude.png";
import geminiLogo from "../icons/logos/gemini.png";
import gptLogo from "../icons/logos/gpt.png";
import "./ModelSelection.scss";


export interface ModelOption {
    id: string;
    label: string;
    provider?: string;
    icon?: React.ReactElement<any>;
    tooltip?: string;
    tag?: React.ReactNode;
}

enum ModelTypes {
    GPT = "gpt",
    CLAUDE = "claude",
    GEMINI = "Gemini",
}

const modelOptions: ModelOption[] = [
    { id: "category-OpenAI", label: "OpenAI" },
    { id: "gpt-4o", label: "GPT-4o", provider: "openai_textgen", icon: getIcon(ModelTypes.GPT), tag: getTag("Fast & Flexible") },
    { id: "gpt-4o-mini", label: "GPT-4o Mini", provider: "openai_textgen", icon: getIcon(ModelTypes.GPT), tag: getTag("Affordable") },
    { id: "gpt-4.1", label: "GPT-4.1", provider: "openai_textgen", icon: getIcon(ModelTypes.GPT), tag: getTag("Smartest Non-Reasoning") },
    { id: "gpt-4.1-mini", label: "GPT-4.1 Mini", provider: "openai_textgen", icon: getIcon(ModelTypes.GPT), tag: getTag("Faster") },
    { id: "gpt-5", label: "GPT-5", provider: "openai_textgen", icon: getIcon(ModelTypes.GPT), tag: getTag("Reasoning") },
    { id: "gpt-5-mini", label: "GPT-5 Mini", provider: "openai_textgen", icon: getIcon(ModelTypes.GPT), tag: getTag("Cost-Efficient") },
    { id: "gpt-5.1", label: "GPT-5.1", provider: "openai_textgen", icon: getIcon(ModelTypes.GPT) },
    { id: "gpt-5.2", label: "GPT-5.2", provider: "openai_textgen", icon: getIcon(ModelTypes.GPT), tag: getTag("Best for Coding") },
    { id: "o3-mini", label: "o3-mini", provider: "openai_textgen", icon: getIcon(ModelTypes.GPT), tag: getTag("Small Reasoner") },

    { id: "category-Google", label: "Google" },
    { id: "gemini-2.5-pro", label: "Gemini 2.5 Pro", provider: "gemini_textgen", icon: getIcon(ModelTypes.GEMINI), tag: getTag("Advanced Thinking") },
    { id: "gemini-2.5-flash", label: "Gemini 2.5 Flash", provider: "gemini_textgen", icon: getIcon(ModelTypes.GEMINI), tag: getTag("Best Value") },
    { id: "gemini-2.5-flash-lite", label: "Gemini 2.5 Flash Lite", provider: "gemini_textgen", icon: getIcon(ModelTypes.GEMINI), tag: getTag("Ultra Fast") },
    { id: "gemini-3.0-pro", label: "Gemini 3.0 Pro", provider: "gemini_textgen", icon: getIcon(ModelTypes.GEMINI), tag: getTag("Most Intelligent") },
    { id: "gemini-3.0-flash", label: "Gemini 3.0 Flash", provider: "gemini_textgen", icon: getIcon(ModelTypes.GEMINI), tag: getTag("Balanced") },
];

// Old model options (deprecated)
// const modelOptions: ModelOption[] = [
//     { id: "category-OpenAI", label: "OpenAI", },
//     { id: "gpt-4.1", label: "GPT-4.1", icon: getIcon(ModelTypes.GPT), tag: getTag("Smart and Fast") },
//     { id: "gpt-4o-mini", label: "GPT-4o Mini", icon: getIcon(ModelTypes.GPT), tag: getTag("Fastest") },
//     { id: "gpt-4o-mini-deep", label: "GPT-4o Mini Deep Research", icon: getIcon(ModelTypes.GPT), tag: getTag("Deep Research") },
//     { id: "gpt-5-pro", label: "GPT-5 Pro", icon: getIcon(ModelTypes.GPT), tag: getTag("Advanced Reasoning") },
//     { id: "gpt-5-nano", label: "GPT-5 nano", icon: getIcon(ModelTypes.GPT), tag: getTag("Latest and Fastest") },
//     
//     { id: "category-Anthropic", label: "Anthropic", },
//     { id: "claude-4.5", label: "Claude 4.5", icon: getIcon(ModelTypes.CLAUDE), tag: getTag("New") },
//     { id: "claude-4-sonnet-1m", label: "Claude 4.5 Sonnet 1M", icon: getIcon(ModelTypes.CLAUDE), tag: getTag("Beta") },
//     { id: "claude-4.1-opus", label: "Claude 4.1 Opus", icon: getIcon(ModelTypes.CLAUDE) },
//     { id: "claude-4 opus", label: "Claude 4 Opus", icon: getIcon(ModelTypes.CLAUDE) },
//     
//     { id: "category-Google", label: "Google", },
//     { id: "gemini-3-pro", label: "Gemini 3 Pro", icon: getIcon(ModelTypes.GEMINI), tag: getTag("New") },
//     { id: "gemini-2.5-pro", label: "Gemini 2.5 Pro", icon: getIcon(ModelTypes.GEMINI), },
// ];

function getIcon(model: ModelTypes): React.ReactElement<any> {
    switch (model) {
        case ModelTypes.GPT: return <Image src={gptLogo} alt="Chat GPT Icon" height={16} width={16} className="invert-on-dark" />
        case ModelTypes.CLAUDE: return <Image src={claudeLogo} alt="Claude Icon" height={16} width={16} className="invert-on-dark" />
        case ModelTypes.GEMINI: return <Image src={geminiLogo} alt="Gemini Icon" height={13} width={16} />
    }
}

function getTag(model: string): React.ReactElement<any> {
    return (
        <div className="model-tag">
            {model}
        </div>
    )
}

export function getModelById(id: string): ModelOption | undefined {
    return modelOptions.find(option => option.id === id && !option.id.includes("category"));
}


interface ModelSelectionProps {
    value: string;
    onChange: (modelId: string) => void;
    disabled?: boolean;
}

export function ModelSelection({ value, onChange, disabled }: ModelSelectionProps): JSX.Element {
    const selectOptions: CommonSelectOption[] = useMemo(() => modelOptions.map((option) => {
        if (option.id.includes("category")) {
            return {
                value: option.id,
                label: option.label,
                isSeparator: true,
                disabled: true,
            };
        }
        return {
            value: option.id,
            label: option.label,
            icon: option.icon,
            tooltip: option.tooltip,
            suffix: option.tag,
        };
    }), []);

    function handleSelectedValueChange(newValue: string): void {
        const selectedOption = modelOptions.find(opt => opt.id === newValue);
        if (selectedOption && !selectedOption.id.includes("category")) {
            onChange(newValue);
        }
    }

    return (
        <div className="model-selection-container">
            <CommonSelect
                options={selectOptions}
                controlledValue={value || undefined}
                onSelectedValueChange={handleSelectedValueChange}
                contentsClassName="model-selection-menu"
                left
                usePortal
                noSelectionMessage="Select Model"
                selectIcon={<Icons.SVGChevronDown />}
                disabled={disabled}
            />
        </div>
    );
}