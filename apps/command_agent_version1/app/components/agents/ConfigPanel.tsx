"use client";

import { ChevronsLeft, ChevronsRight, PenLine } from "lucide-react";
import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useState,
} from "react";
import {
  type AgentConfigData,
  type AgentNodeData,
  type AgentType,
  type ChatCompletionToolParam,
  type PromptResponse,
} from "../../lib/interfaces";
import { fetchToolSchemasAsArray } from "../../lib/toolActions";
import { usePrompts } from "../../ui/contexts/PromptsContext";
import TabHeader, { type Tab } from "../TabHeader";
import {
  ConfigurationTab,
  ToolsTab,
  getModelProviders,
  getModels,
} from "./config";
import PromptDetailView from "./config/PromptDetailView";
import "./ConfigPanel.scss";
import { getAgentIcon } from "./iconUtils";

export interface ConfigPanelHandle {
  setTab: (tab: "config" | "tools") => void;
  enableEdit: () => void;
  disableEdit: () => void;
  showPromptDetail: (prompt?: PromptResponse) => void;
  resetView: () => void;
}

interface ConfigPanelProps {
  agent: AgentNodeData;
  agentName: string;
  agentType: AgentType | "custom";
  agentConfig?: AgentConfigData;
  description: string;
  onEditPrompt: () => void;
  onSave?: (configData: AgentConfigData) => void;
  onClose?: () => void;
  onNameChange?: (newName: string) => void;
  toggleSidebar?: () => void;
  sidebarOpen?: boolean;
  setSidebarOpen?: () => void;
  currentFunctions?: ChatCompletionToolParam[]; // Current agent functions
  onFunctionsChange?: (functions: ChatCompletionToolParam[]) => void; // Callback for function changes
}

const ConfigPanel = forwardRef<ConfigPanelHandle, ConfigPanelProps>(
  function ConfigPanel(
    {
      agent,
      agentName,
      agentType,
      description,
      onEditPrompt,
      onSave,
      toggleSidebar,
      sidebarOpen,
      currentFunctions = [],
      onFunctionsChange,
      agentConfig,
    },
    ref
  ): JSX.Element {
    // State for editable fields
    const [deploymentType, setDeploymentType] = useState("Elevaite");
    const [modelProvider, setModelProvider] = useState("meta");
    const [model, setModel] = useState("gpt-4o");
    const [outputFormat, setOutputFormat] = useState("JSON");
    const [activeTab, setActiveTab] = useState("config");

    // State for sidebar view mode
    const [sidebarView, setSidebarView] = useState<"config" | "prompt">(
      "config"
    );

    const [selectedPromptForView, setSelectedPromptForView] =
      useState<PromptResponse | null>(null);

    // State for selected tools (now as ChatCompletionToolParam array)
    const [selectedFunctions, setSelectedFunctions] =
      useState<ChatCompletionToolParam[]>(currentFunctions);

    // State for available tool schemas
    const [availableToolSchemas, setAvailableToolSchemas] = useState<
      ChatCompletionToolParam[]
    >([]);
    const [toolSchemasLoading, setToolSchemasLoading] = useState(false);
    const [toolSchemasError, setToolSchemasError] = useState<string | null>(
      null
    );

    // Note: We're now using tool schemas directly instead of the tools context

    // State for agent name editing
    const [editedName, setEditedName] = useState(agentName);
    const [disabledFields, setDisabledFields] = useState(true);

    // State for editable agent type and tags
    const [editedAgentType, setEditedAgentType] = useState<AgentType>(
      agent.agent.agent_type ?? (agentType === "custom" ? "router" : agentType)
    );
    const [editedDescription, setEditedDescription] = useState(
      agent.agent.description ?? description
    );
    const [editedTags, setEditedTags] = useState(
      agent.agent.system_prompt.tags?.join(", ") ?? ""
    );
    const [selectedPromptId, setSelectedPromptId] = useState<string | null>(
      agent.agent.system_prompt?.pid ?? null
    );

    // Debug: Log the initial selectedPromptId
    useEffect(() => {
      console.log("Initial selectedPromptId:", selectedPromptId);
      console.log("Agent system prompt:", agent.agent.system_prompt);
    }, []);

    // Get prompts context
    const { getPromptById } = usePrompts();

    // Update local state when agentName prop changes
    useEffect(() => {
      setEditedName(agentName);
    }, [agentName]);

    // Update all agent-related state when agent prop changes
    useEffect(() => {
      setEditedAgentType(
        agent.agent.agent_type ??
        (agentType === "custom" ? "router" : agentType)
      );
      setEditedDescription(agent.agent.description ?? description);
      setEditedTags(agent.agent.system_prompt.tags?.join(", ") ?? "");
      // Set selectedPromptId to null if it's a placeholder prompt, otherwise use the actual pid
      const isPlaceholderPrompt =
        agent.agent.system_prompt.pid === "placeholder";
      setSelectedPromptId(
        isPlaceholderPrompt ? null : agent.agent.system_prompt.pid
      );
    }, [agent, agentType, description]);

    // Update selected functions when currentFunctions prop changes
    useEffect(() => {
      setSelectedFunctions(currentFunctions);
    }, [currentFunctions]);

    // Load tool schemas on component mount
    useEffect(() => {
      const loadToolSchemas = async (): Promise<void> => {
        try {
          setToolSchemasLoading(true);
          setToolSchemasError(null);
          const schemas = await fetchToolSchemasAsArray();
          setAvailableToolSchemas(schemas);
        } catch (error) {
          // eslint-disable-next-line no-console -- TODO: Replace with proper error handling
          console.error("Failed to load tool schemas:", error);
          setToolSchemasError("Failed to load tool schemas");
        } finally {
          setToolSchemasLoading(false);
        }
      };

      void loadToolSchemas();
    }, []);

    // Define tabs for TabHeader component
    const sidebarTabs: Tab[] = [
      { id: "config", label: "Configuration" },
      { id: "tools", label: "Tools & Prompts" },
    ];

    // Update model provider when deployment type changes
    useEffect(() => {
      const providers = getModelProviders(deploymentType);
      setModelProvider(providers[0]);
    }, [deploymentType]);

    // Update model when model provider changes
    useEffect(() => {
      const availableModels = getModels(deploymentType, modelProvider);
      setModel(availableModels[0]);
    }, [modelProvider, deploymentType]);

    useEffect(() => {
      if (agentConfig) {
        setDeploymentType(agent.config?.deploymentType ?? "Elevaite");
        setModelProvider(agent.agent.system_prompt.ai_model_provider);
        setModel(agent.agent.system_prompt.ai_model_name);
        setOutputFormat(agent.agent.output_type.join(", "));
        setSelectedFunctions(agentConfig.selectedTools);
      }
    }, [agentConfig]);

    // Reset sidebar view when agent changes
    useEffect(() => {
      setSidebarView("config");
      setSelectedPromptForView(null);
    }, [agent]);

    // Function to handle tool selection
    const handleToolSelect = (toolName: string): void => {
      // Find the tool schema for the selected tool
      const toolSchema = availableToolSchemas.find(
        (schema) => schema.function.name === toolName
      );
      if (!toolSchema) return;

      // Check if tool is already selected
      const isSelected = selectedFunctions.some(
        (func) => func.function.name === toolName
      );

      let updatedFunctions: ChatCompletionToolParam[];
      if (isSelected) {
        // Remove the tool
        updatedFunctions = selectedFunctions.filter(
          (func) => func.function.name !== toolName
        );
      } else {
        // Add the tool
        updatedFunctions = [...selectedFunctions, toolSchema];
      }

      setSelectedFunctions(updatedFunctions);

      // Notify parent component of the change
      if (onFunctionsChange) {
        onFunctionsChange(updatedFunctions);
      }
    };

    useImperativeHandle(ref, () => ({
      setTab(tab: "config" | "tools") {
        setActiveTab(tab);
      },
      enableEdit() {
        setDisabledFields(false);
      },
      disableEdit() {
        setDisabledFields(true);
      },
      showPromptDetail(prompt?: PromptResponse) {
        setSelectedPromptForView(prompt ?? null);
        if (prompt !== undefined) {
          setSidebarView("prompt");
        }
      },
      resetView() {
        setSidebarView("config");
        setSelectedPromptForView(null);
      },
    }));

    // Handle save button click
    const handleSave = useCallback((): void => {
      console.log("Current selectedPromptId in handleSave:", selectedPromptId);
      if (onSave) {
        console.log("Saving agent configuration:", {
          agentName: editedName,
          agentType: editedAgentType,
          description: editedDescription,
          tags: editedTags,
          selectedPromptId,
          deploymentType,
          modelProvider,
          model,
          outputFormat,
          selectedTools: selectedFunctions,
        });
        onSave({
          agentName: editedName, // Include the potentially updated name
          agentType: editedAgentType,
          description: editedDescription,
          tags: editedTags,
          selectedPromptId, // Include the selected prompt
          deploymentType,
          modelProvider,
          model,
          outputFormat,
          selectedTools: selectedFunctions,
        });
      }
    }, [
      selectedPromptId,
      editedName,
      editedAgentType,
      editedDescription,
      editedTags,
      deploymentType,
      modelProvider,
      model,
      outputFormat,
      selectedFunctions,
      onSave,
    ]);

    // Handle save as button click - creates a new agent
    const handleSaveAs = useCallback((): void => {
      if (onSave) {
        // Create a new agent with the current configuration
        onSave({
          agentName: editedName, // Use the edited name for the new agent
          agentType: editedAgentType,
          description: editedDescription,
          tags: editedTags,
          selectedPromptId, // Include the selected prompt for new agent
          deploymentType,
          modelProvider,
          model,
          outputFormat,
          selectedTools: selectedFunctions,
          isNewAgent: true, // Flag to indicate this should create a new agent
        });
      }
    }, [
      selectedPromptId,
      editedName,
      editedAgentType,
      editedDescription,
      editedTags,
      deploymentType,
      modelProvider,
      model,
      outputFormat,
      selectedFunctions,
      onSave,
    ]);

    // Handle prompt selection
    const handlePromptSelect = (promptId: string): void => {
      console.log("handlePromptSelect called with promptId:", promptId);
      const selectedPrompt = getPromptById(promptId);
      console.log("Got one, ", selectedPrompt);
      if (selectedPrompt) {
        console.log("Setting selectedPromptId to:", promptId);
        setSelectedPromptId(promptId);
      } else {
        console.log("No prompt found for ID:", promptId);
      }
    };

    // Handle prompt click to view details
    const handlePromptClick = (prompt: PromptResponse): void => {
      setSelectedPromptForView(prompt);
      setSidebarView("prompt");
    };

    // Handle back to config view
    const handleBackToConfig = (): void => {
      setSidebarView("config");
      setSelectedPromptForView(null);
    };

    return (
      <div className="config-panel">
        {/* Header with close button and editable name */}
        {selectedPromptForView ? (
          <PromptDetailView
            prompt={selectedPromptForView}
            onBack={handleBackToConfig}
            disabledFields={disabledFields}
            setDisabledFields={setDisabledFields}
          />
        ) : (
          <>
            <div
              className={[
                "config-panel-header",
                !disabledFields ? "editing" : undefined,
              ]
                .filter(Boolean)
                .join(" ")}
            >
              <div className="flex flex-1 items-center pr-3">
                {!disabledFields ? (
                  <div className="flex flex-col gap-3 flex-1">
                    <div className="flex flex-col gap-1">
                      <label
                        htmlFor="agent-name-input"
                        className="text-sm font-medium"
                        style={{ fontSize: "14px" }}
                      >
                        Agent Base
                      </label>
                      <input
                        id="agent-name-input"
                        type="text"
                        value={editedName}
                        onChange={(e) => {
                          setEditedName(e.target.value);
                        }}
                        className="border border-gray-300 rounded-md px-3 py-2"
                        style={{ fontSize: "12px" }}
                        placeholder="Enter agent name"
                      />
                    </div>
                    <div className="flex flex-col gap-1">
                      <label
                        htmlFor="agent-description-input"
                        className="text-sm font-medium"
                        style={{ fontSize: "14px" }}
                      >
                        Description
                      </label>
                      <input
                        id="agent-description-input"
                        type="text"
                        value={editedDescription}
                        onChange={(e) => {
                          setEditedDescription(e.target.value);
                        }}
                        className="border border-gray-300 rounded-md px-3 py-2"
                        style={{ fontSize: "12px" }}
                        placeholder="Enter agent description"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="flex flex-1 items-center gap-3 justify-between">
                    <div className="agent-name-display">
                      <div className="agent-icon flex-shrink-0">
                        {getAgentIcon(agentType)}
                      </div>
                      <div className="agent-title">
                        <p className="agent-name">{editedName}</p>
                        <p className="agent-description">{editedDescription}</p>
                      </div>
                    </div>
                    <button
                      className="activate-fields"
                      type="button"
                      onClick={() => {
                        setDisabledFields(!disabledFields);
                      }}
                    >
                      <PenLine size={20} />
                    </button>
                    {/* <button type="button">
									<svg width="4" height="18" viewBox="0 0 4 18" fill="none" xmlns="http://www.w3.org/2000/svg">
										<path d="M2 10C2.55228 10 3 9.55228 3 9C3 8.44772 2.55228 8 2 8C1.44772 8 1 8.44772 1 9C1 9.55228 1.44772 10 2 10Z" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										<path d="M2 3C2.55228 3 3 2.55228 3 2C3 1.44772 2.55228 1 2 1C1.44772 1 1 1.44772 1 2C1 2.55228 1.44772 3 2 3Z" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
										<path d="M2 17C2.55228 17 3 16.5523 3 16C3 15.4477 2.55228 15 2 15C1.44772 15 1 15.4477 1 16C1 16.5523 1.44772 17 2 17Z" stroke="black" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
									</svg>
								</button> */}
                  </div>
                )}
              </div>

              <button
                type="button"
                onClick={toggleSidebar}
                className="flex flex-shrink-0 items-center"
              >
                {sidebarOpen ? <ChevronsRight /> : <ChevronsLeft />}
              </button>
            </div>
            <div className="nav-wrapper flex flex-col justify-between flex-1">
              <div className="nav-container">
                {/* Navigation Tabs */}
                <TabHeader
                  tabs={sidebarTabs}
                  activeTab={activeTab}
                  onTabChange={setActiveTab}
                  innerClassName="sidebar-header-tabs-inner p-1 text-xs font-normal rounded-lg flex items-center w-full"
                />

                {/* Tab Content */}
                {activeTab === "config" && (
                  <ConfigurationTab
                    agent={agent}
                    agentType={editedAgentType}
                    deploymentType={deploymentType}
                    setDeploymentType={setDeploymentType}
                    modelProvider={modelProvider}
                    setModelProvider={setModelProvider}
                    model={model}
                    setModel={setModel}
                    outputFormat={outputFormat}
                    setOutputFormat={setOutputFormat}
                    disabledFields={disabledFields}
                    setAgentType={setEditedAgentType}
                    tags={editedTags}
                    setTags={setEditedTags}
                  />
                )}

                {activeTab === "tools" && (
                  <ToolsTab
                    selectedFunctions={selectedFunctions}
                    handleToolSelect={handleToolSelect}
                    handlePromptSelect={handlePromptSelect}
                    selectedPromptId={selectedPromptId}
                    disabledFields={disabledFields}
                    onEditPrompt={onEditPrompt}
                    agent={agent}
                    onPromptClick={handlePromptClick}
                  />
                )}
              </div>

              {/* Action Buttons - Only show when editing */}
              {!disabledFields && (
                <div className="flex gap-3 justify-evenly">
                  {/* Cancel Button */}
                  <button
                    onClick={() => {
                      // Reset all edited values to original
                      setEditedName(agentName);
                      setEditedDescription(
                        agent.agent.description ?? description
                      );
                      setEditedAgentType(
                        agent.agent.agent_type ??
                        (agentType === "custom" ? "router" : agentType)
                      );
                      setEditedTags(
                        agent.agent.system_prompt.tags?.join(", ") ?? ""
                      );
                      setDisabledFields(true);
                    }}
                    className="grow px-4 py-2 border border-[#FF681F] text-[#FF681F] rounded-md hover:bg-[#FF681F]/5 transition-colors"
                    style={{ fontSize: "14px" }}
                    type="button"
                  >
                    Cancel
                  </button>

                  {/* Save Button */}
                  <button
                    onClick={() => {
                      handleSave();
                      setDisabledFields(true);
                    }}
                    className="grow px-4 py-2 border border-[#FF681F] text-[#FF681F] rounded-md hover:bg-[#FF681F]/5 transition-colors"
                    style={{ fontSize: "14px" }}
                    type="button"
                  >
                    Save
                  </button>

                  {/* Save As Button */}
                  <button
                    onClick={() => {
                      handleSaveAs();
                      setDisabledFields(true);
                    }}
                    className="grow px-4 py-2 bg-[#FF681F] text-white rounded-md hover:bg-[#E55A1A] transition-colors"
                    style={{ fontSize: "14px" }}
                    type="button"
                  >
                    Save As
                  </button>
                </div>
              )}
            </div>
          </>
        )}
      </div>
    );
  }
);

export default ConfigPanel;
