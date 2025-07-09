import { type AgentType } from "../../../lib/interfaces";
import { AGENT_STYLES } from "../../type";

// Constants
export const DEPLOYMENT_TYPES = [
    "Elevaite",
    "Enterprise",
    "Cloud"
];

export const OUTPUT_FORMATS = [
    "JSON",
    "Text",
    "CSV",
    "HTML",
    "Markdown",
    "YAML"
];

// Get the agent type display name
export const getAgentTypeDisplay = (type: AgentType): string => {
    switch (type) {
        case "router": return "Router";
        case "web_search": return "Web Search";
        case "Weather Search Agent": return "API";
        case "data": return "Data Extractor";
        case "troubleshooting": return "Troubleshooting";
        default: return type;
    }
};

// Get the style class for the agent type
export const getStyleClass = (type: AgentType): string => {
    // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Better safe than sorry
    const styles = AGENT_STYLES[type] || { bgClass: "bg-gray-100", textClass: "text-gray-600" };
    return `${styles.bgClass} ${styles.textClass}`;
};

// Get model providers based on deployment type
export const getModelProviders = (deployType: string): string[] => {
    switch (deployType) {
        case "Elevaite":
            return ["meta", "openbmb", "OpenAI"];
        case "Enterprise":
            return ["OpenAI", "Gemini", "Bedrock", "Azure"];
        case "Cloud":
            return ["OpenAI", "Gemini", "Bedrock", "Azure"];
        default:
            return ["meta"];
    }
};

// Get models based on deployment type and model provider
export const getModels = (deployType: string, provider: string): string[] => {
    // Currently only supporting GPT-4o
    return ["GPT-4o"];

    // Original code commented out - multiple model support
    // if (deployType === "Elevaite") {
    //     switch (provider) {
    //         case "meta":
    //             return ["Llama-3.1-8B-Instruct"];
    //         case "openbmb":
    //             return ["MiniCPM-V-2_6"];
    //         case "OpenAI":
    //             return ["GPT-4o", "GPT-4o mini", "GPT-3.5", "o3-mini"];
    //         default:
    //             return ["Llama-3.1-8B-Instruct"];
    //     }
    // } else if (deployType === "Enterprise" || deployType === "Cloud") {
    //     switch (provider) {
    //         case "OpenAI":
    //             return ["GPT-4o", "GPT-4o mini", "GPT-3.5", "o3-mini"];
    //         case "Gemini":
    //             return ["2.5 Pro", "2.5 Flash", "2.0 Flash"];
    //         case "Bedrock":
    //             return ["Claude 3.5", "Claude 3.5 Sonnet", "Claude 3.5 Haiku", "Llama 3.1 8B Instruct"];
    //         case "Azure":
    //             return ["GPT-4o", "GPT-4o mini", "GPT-3.5"];
    //         default:
    //             return ["GPT-4o"];
    //     }
    // }
    // return ["GPT-4o"];
};
