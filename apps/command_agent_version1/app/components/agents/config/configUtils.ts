import { type AgentType } from "../../../lib/interfaces";
import { AGENT_STYLES } from "../../type";

// Constants
export const DEPLOYMENT_TYPES = ["Elevaite", "Enterprise", "Cloud"];

export const OUTPUT_FORMATS = [
  "JSON",
  "Text",
  "CSV",
  "HTML",
  "Markdown",
  "YAML",
];

// Get the agent type display name
export const getAgentTypeDisplay = (type: AgentType): string => {
  switch (type) {
    case "router":
      return "Router";
    case "web_search":
      return "Web Search";
    case "Weather Search Agent":
      return "API";
    case "data":
      return "Data Extractor";
    case "troubleshooting":
      return "Troubleshooting";
    default:
      return type;
  }
};

// Get the style class for the agent type
export const getStyleClass = (type: AgentType): string => {
  // eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- Better safe than sorry
  const styles = AGENT_STYLES[type] || {
    bgClass: "bg-gray-100",
    textClass: "text-gray-600",
  };
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

// Model configuration: maps display names to model codes
export const MODEL_OPTIONS = [
  { displayName: "GPT-4o", modelCode: "gpt-4o" },
  { displayName: "GPT-4o Mini", modelCode: "gpt-4o-mini" },
  { displayName: "GPT-4.1", modelCode: "gpt-4.1" },
  { displayName: "GPT-4.1 Mini", modelCode: "gpt-4.1-mini" },
  { displayName: "GPT-5", modelCode: "gpt-5" },
  { displayName: "GPT-5 Mini", modelCode: "gpt-5-mini" },
  { displayName: "o3-mini", modelCode: "o3-mini" },
  { displayName: "Gemini 2.5 Pro", modelCode: "gemini-2.5-pro" },
  { displayName: "Gemini 2.5 Flash", modelCode: "gemini-2.5-flash" },
  { displayName: "Gemini 2.5 Flash Lite", modelCode: "gemini-2.5-flash-lite" },
] as const;

// Get available models (returns model codes)
export const getModels = (_deployType: string, _provider: string): string[] => {
  return MODEL_OPTIONS.map((model) => model.modelCode);
};

// Get display name for a model code
export const getModelDisplayName = (modelCode: string): string => {
  const model = MODEL_OPTIONS.find((m) => m.modelCode === modelCode);
  return model ? model.displayName : modelCode;
};

// Get model code from display name
export const getModelCode = (displayName: string): string => {
  const model = MODEL_OPTIONS.find((m) => m.displayName === displayName);
  return model ? model.modelCode : displayName;
};
