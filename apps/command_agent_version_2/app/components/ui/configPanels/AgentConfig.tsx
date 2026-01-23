import { cls, CommonButton, CommonSelect, CommonTray, type CommonSelectOption } from "@repo/ui";
import { useEffect, useMemo, useState, type JSX } from "react";
import { useCanvas } from "../../../lib/contexts/CanvasContext";
import { useConfigPanel } from "../../../lib/contexts/ConfigPanelContext";
import { useFocusAnchor } from "../../../lib/hooks/useFocusAnchor";
import { useNodeConfig } from "../../../lib/hooks/useNodeConfig";
import { type ConfigPanelsProps, type SidePanelPayload } from "../../../lib/interfaces";
import { AgentKeys } from "../../../lib/model/innerEnums";
import { PromptNodeId } from "../../../lib/model/uiEnums";
import { getItemDetail, typeGuards } from "../../../lib/utilities/config";
import { Icons } from "../../icons";
import { DisplayText } from "../DisplayText";
import { ModelSelection } from "../ModelSelection";
import { Slider } from "../Slider";
import "./ConfigPanels.scss";


const personalityOptions: CommonSelectOption[] = [
    { value: "professional", label: "Professional" },
    { value: "friendly", label: "Friendly" },
    { value: "creative", label: "Creative" },
    { value: "analytical", label: "Analytical" },
    { value: "casual", label: "Casual" },
];

const chargeTypeOptions: CommonSelectOption[] = [
    { value: "token", label: "Token-Based" },
    { value: "request", label: "Request-Based" },
    { value: "compute", label: "Compute-Based" },
    { value: "free", label: "Free / Included" },
];

const outputTypeOptions: CommonSelectOption[] = [
    { value: "text", label: "Text" },
    { value: "json", label: "JSON" },
    // { value: "markdown", label: "Markdown" },
];

const toolOptions: CommonSelectOption[] = [
    { value: "hosted-label", label: "Hosted", isSeparator: true },
    { value: "file-search", label: "File Search", icon: <Icons.Tools.SVGFileSearch /> },
    { value: "web-search", label: "Web Search", icon: <Icons.Tools.SVGWebSearch /> },
    { value: "code-interpreter", label: "Code Interpreter", icon: <Icons.Tools.SVGInterpreter /> },
    { value: "local-label", label: "Local", isSeparator: true },
    { value: "function", label: "Function", icon: <Icons.Tools.SVGFunction /> },
];


export function AgentConfig({ node: _node }: ConfigPanelsProps): JSX.Element {
    useFocusAnchor();
    const { selectedNode, updateDraftMultiple } = useConfigPanel();
    const { nodes, edges, selectedNodeId, setSelectedNodeId } = useCanvas();

    // Collapsible section states
    const [isPromptOpen, setIsPromptOpen] = useState(true);
    const [isParametersOpen, setIsParametersOpen] = useState(true);
    const [isToolsOpen, setIsToolsOpen] = useState(true);

    // Read config values using useNodeConfig hook
    const [description, setDescription] = useNodeConfig(AgentKeys.DESCRIPTION, "", typeGuards.isString);
    const [query, setQuery] = useNodeConfig(AgentKeys.QUERY, "", typeGuards.isString);
    const [personality, setPersonality] = useNodeConfig(AgentKeys.PERSONALITY, "", typeGuards.isString);
    const [agentInstructions, setAgentInstructions] = useNodeConfig(AgentKeys.INSTRUCTIONS, "", typeGuards.isString);
    const [model, setModel] = useNodeConfig(AgentKeys.MODEL, "", typeGuards.isString);
    const [modelChargeType, setModelChargeType] = useNodeConfig(AgentKeys.CHARGE_TYPE, "", typeGuards.isString);
    const [outputType, setOutputType] = useNodeConfig(AgentKeys.OUTPUT_TYPE, "", typeGuards.isString);
    const [temperature, setTemperature] = useNodeConfig(AgentKeys.TEMPERATURE, 0.5, typeGuards.isNumber);
    const [maxTokens, setMaxTokens] = useNodeConfig(AgentKeys.MAX_TOKENS, 4000, typeGuards.isNumber);

    // Check if a prompt node is connected and get its info
    const connectedPromptNode = useMemo(() => {
        if (!selectedNodeId) return undefined;
        // Find all edges where this node is the target (incoming edges)
        const incomingEdges = edges.filter(edge => edge.target === selectedNodeId);
        // Check if any source node is a prompt node
        const promptNodeIds = Object.values(PromptNodeId) as string[];
        for (const edge of incomingEdges) {
            const sourceNode = nodes.find(n => n.id === edge.source);
            if (!sourceNode) continue;
            const payload = sourceNode.data as SidePanelPayload | undefined;
            if (payload?.id && promptNodeIds.includes(payload.id)) {
                // Found a prompt node - return its React Flow node ID and text
                const promptText = payload.nodeDetails?.itemDetails?.text;
                return {
                    nodeId: sourceNode.id,
                    text: typeof promptText === "string" ? promptText : "",
                };
            }
        }
        return undefined;
    }, [selectedNodeId, edges, nodes]);

    const hasConnectedPromptNode = connectedPromptNode !== undefined;

    // Navigate to the connected prompt node
    const handleGoToPromptNode = (): void => {
        if (connectedPromptNode?.nodeId) {
            setSelectedNodeId(connectedPromptNode.nodeId);
        }
    };

    // Initialize default values if not set
    useEffect(() => {
        if (!selectedNode) return;
        const missing: Record<string, number> = {};
        if (getItemDetail(selectedNode, AgentKeys.TEMPERATURE) === undefined) missing[AgentKeys.TEMPERATURE] = 0.5;
        if (getItemDetail(selectedNode, AgentKeys.MAX_TOKENS) === undefined) missing[AgentKeys.MAX_TOKENS] = 4000;
        if (Object.keys(missing).length > 0) updateDraftMultiple(missing);
    }, [selectedNode?.id]);


    return (
        <div className="inner-config-panel-container agent-config">

            <div id={AgentKeys.DESCRIPTION} className="config-section">
                <DisplayText
                    label="Description"
                    value={description}
                    onChange={setDescription}
                    placeholder="Brief summary of what this agent does (helps identify it in the workflow)"
                    className="display-small"
                />
            </div>

            <CommonButton className="tray-button" noBackground onClick={() => { setIsPromptOpen(!isPromptOpen); }}>
                <div className="tray-row">
                    <div className="main-label">
                        <div className="icon"><Icons.Dark.SVGPrompt /></div>
                        <span>Prompt</span>
                    </div>
                </div>
                <div className={cls("tray-chevron", isPromptOpen && "open")}>
                    <Icons.SVGChevronDown />
                </div>
            </CommonButton>
            <CommonTray isOpen={isPromptOpen}>
                <div id={AgentKeys.PERSONALITY} className={cls("tray-row", hasConnectedPromptNode && "disabled")}>
                    <span className="label">Personality</span>
                    <CommonSelect
                        options={personalityOptions}
                        controlledValue={personality || undefined}
                        onSelectedValueChange={setPersonality}
                        noSelectionMessage="Select"
                        usePortal
                        disabled={hasConnectedPromptNode}
                    />
                </div>
                <div id={AgentKeys.INSTRUCTIONS}>
                    <DisplayText
                        label="Agent Instructions"
                        info={hasConnectedPromptNode ? "Read-only - edit in the connected Prompt Node" : "Define what the agent should do"}
                        value={hasConnectedPromptNode ? connectedPromptNode.text : agentInstructions}
                        onChange={hasConnectedPromptNode ? undefined : setAgentInstructions}
                        placeholder="Define what the agent should do. Use {{variable_name}} to reference data from previous nodes. Or click &quot;+&quot; for pre-built templates."
                        className="display-medium"
                        showExpand={!hasConnectedPromptNode}
                        showAIAssist={!hasConnectedPromptNode}
                        showAddVariable={!hasConnectedPromptNode}
                        disabled={hasConnectedPromptNode}
                        readOnly={hasConnectedPromptNode}
                        topRightIcons={hasConnectedPromptNode ? [
                            <CommonButton
                                key="goToPrompt"
                                className="from-prompt-node-link"
                                onClick={handleGoToPromptNode}
                                title="Click to view and edit the connected Prompt Node"
                                noBackground
                            >
                                <Icons.Dark.SVGPrompt />
                                <span>From Prompt Node</span>
                            </CommonButton>
                        ] : [
                            <CommonSelect
                                key="addPrompt"
                                options={[]}
                                onSelectedValueChange={(value) => { console.log("Add prompt:", value); }}
                                emptyListLabel="No prompts found"
                                selectIcon={<Icons.SVGPlus color="var(--ev-colors-highlight)" />}
                                usePortal
                                noLabel
                                title="Add prompts saved from Prompt Studio"
                            />
                        ]}
                    />
                </div>
                <div id={AgentKeys.QUERY}>
                    <DisplayText
                        label="Query"
                        info="The input query or question to send to the agent. Use {{variable_name}} to reference data from previous nodes."
                        value={query}
                        onChange={setQuery}
                        placeholder="Enter your query here. Use {{variable_name}} to reference data from previous nodes."
                        className="display-medium"
                        showExpand
                        showAIAssist
                        showAddVariable
                    />
                </div>
            </CommonTray>
            <CommonButton className="tray-button" noBackground onClick={() => { setIsParametersOpen(!isParametersOpen); }}>
                <div className="tray-row">
                    <div className="main-label">
                        <div className="icon"><Icons.SVGSettings /></div>
                        <span>Parameters</span>
                        {hasConnectedPromptNode ? <span className="override-badge">From Prompt Node</span> : undefined}
                        <div className="info" title="Configure model parameters"><Icons.SVGInfo /></div>
                    </div>
                </div>
                <div className={cls("tray-chevron", isParametersOpen && "open")}>
                    <Icons.SVGChevronDown />
                </div>
            </CommonButton>
            <CommonTray isOpen={!hasConnectedPromptNode && isParametersOpen}>
                <div id={AgentKeys.MODEL} className={cls("tray-row", hasConnectedPromptNode && "disabled")}>
                    <span className="label">Model</span>
                    <ModelSelection
                        value={model}
                        onChange={setModel}
                        disabled={hasConnectedPromptNode}
                    />
                </div>
                <div id={AgentKeys.CHARGE_TYPE} className={cls("tray-row", hasConnectedPromptNode && "disabled")}>
                    <span className="label">Model Charge Type</span>
                    <CommonSelect
                        options={chargeTypeOptions}
                        controlledValue={modelChargeType || undefined}
                        onSelectedValueChange={setModelChargeType}
                        noSelectionMessage="Select"
                        usePortal
                        disabled={hasConnectedPromptNode}
                    />
                </div>
                <div id={AgentKeys.OUTPUT_TYPE} className={cls("tray-row", hasConnectedPromptNode && "disabled")}>
                    <span className="label">Output Type</span>
                    <CommonSelect
                        options={outputTypeOptions}
                        controlledValue={outputType || undefined}
                        onSelectedValueChange={setOutputType}
                        noSelectionMessage="Select"
                        usePortal
                        disabled={hasConnectedPromptNode}
                    />
                </div>
                <div id={AgentKeys.TEMPERATURE} className={cls("tray-row", hasConnectedPromptNode && "disabled")}>
                    <Slider
                        value={temperature}
                        onChange={setTemperature}
                        min={0}
                        max={1}
                        label="Temperature"
                        startLabel="Predictable"
                        endLabel="Creative"
                        disabled={hasConnectedPromptNode}
                    />
                </div>
                <div id={AgentKeys.MAX_TOKENS} className={cls("tray-row", hasConnectedPromptNode && "disabled")}>
                    <Slider
                        value={maxTokens}
                        onChange={setMaxTokens}
                        min={0}
                        max={10000}
                        step={100}
                        decimals={0}
                        label="Max Tokens"
                        startLabel="Small Content"
                        endLabel="Large Content"
                        disabled={hasConnectedPromptNode}
                    />
                </div>
            </CommonTray>

            <div className="tray-row">
                <CommonButton className="tray-button display-grow" noBackground onClick={() => { setIsToolsOpen(!isToolsOpen); }}>
                    <div className="tray-row">
                        <div className="main-label">
                            <div className="icon"><Icons.Node.SVGTool /></div>
                            <span>Tools</span>
                            <div className="info" title="Add tools for the agent to use"><Icons.SVGInfo /></div>
                        </div>
                    </div>
                    <div className={cls("tray-chevron", isToolsOpen && "open")}>
                        <Icons.SVGChevronDown />
                    </div>
                </CommonButton>
                <CommonSelect
                    options={toolOptions}
                    onSelectedValueChange={(value) => { console.log("Add tool:", value); }}
                    noSelectionMessage="Add Tool"
                    selectIcon={<Icons.SVGPlus color="var(--ev-colors-highlight)" />}
                    usePortal
                    noLabel
                />
            </div>
            <CommonTray isOpen={isToolsOpen}>
                <div id={AgentKeys.TOOLS} className="tools-empty">
                    <span>No tools added</span>
                    <span className="subtitle">Add a tool to get started</span>
                </div>
            </CommonTray>

        </div>
    );
}

