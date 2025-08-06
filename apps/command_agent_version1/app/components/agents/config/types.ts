import {
  type AgentType,
  type ChatCompletionToolParam,
  type AgentNodeData,
  type PromptResponse,
} from "../../../lib/interfaces";

export interface ConfigurationTabProps {
  agentType: AgentType;
  deploymentType: string;
  modelProvider: string;
  model: string;
  outputFormat: string;
  setDeploymentType: (type: string) => void;
  setModelProvider: (provider: string) => void;
  setModel: (model: string) => void;
  setOutputFormat: (format: string) => void;
  disabledFields: boolean;
  agent: AgentNodeData;
  setAgentType?: (type: AgentType) => void;
  tags?: string;
  setTags?: (tags: string) => void;
}

export interface ToolsTabProps {
  selectedFunctions: ChatCompletionToolParam[];
  disabledFields: boolean;
  onEditPrompt: () => void;
  handleToolSelect: (toolName: string) => void;
  handlePromptSelect?: (promptId: string) => void;
  selectedPromptId?: string | null;
  agent: AgentNodeData;
  onPromptClick?: (prompt: PromptResponse) => void;
}
