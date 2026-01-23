import { cls, CommonButton, CommonInput } from "@repo/ui";
import { useMemo, type JSX } from "react";
import { useConfigPanel } from "../../lib/contexts/ConfigPanelContext";
import { AgentNodeId, CategoryId, InputNodeId, OutputNodeId, PromptNodeId } from "../../lib/enums";
import { type ConfigPanelsProps, type SidePanelNodeId } from "../../lib/interfaces";
import { getCategoryColor, getIcon } from "../../lib/utilities/nodes";
import { Icons } from "../icons";
import "./ConfigPanel.scss";
import { AgentConfig } from "./configPanels/AgentConfig";
import { Default } from "./configPanels/Default";
import { InputTextConfig } from "./configPanels/InputTextConfig";
import { OutputTextConfig } from "./configPanels/OutputTextConfig";
import { PromptConfig } from "./configPanels/PromptConfig";


interface HeaderDetails {
    label?: string;
    icon?: React.ReactNode;
    color?: string;
}

type ConfigPanelsRenderer = (props: ConfigPanelsProps) => JSX.Element;

const ConfigPanelsRegistry: Partial<Record<SidePanelNodeId, ConfigPanelsRenderer>> = {
    // Agents
    [AgentNodeId.NEW]: AgentConfig,
    [AgentNodeId.CONTRACT]: AgentConfig,
    [AgentNodeId.CHATBOT]: AgentConfig,
    [AgentNodeId.ROUTER]: AgentConfig,
    [AgentNodeId.ESCALATION]: AgentConfig,
    [AgentNodeId.IMAGE]: AgentConfig,
    // Prompts
    [CategoryId.PROMPTS]: PromptConfig,
    [PromptNodeId.NEW]: PromptConfig,
    [PromptNodeId.CONTRACT]: PromptConfig,
    [PromptNodeId.CHATBOT]: PromptConfig,
    [PromptNodeId.ROUTER]: PromptConfig,
    [PromptNodeId.ESCALATION]: PromptConfig,
    // Inputs/Outputs
    [InputNodeId.TEXT]: InputTextConfig,
    [OutputNodeId.TEXT]: OutputTextConfig,
};


export function ConfigPanel(): JSX.Element {
    const configPanel = useConfigPanel();
    const headerDetails: HeaderDetails = useMemo(() => {
        if (!configPanel.selectedNode) return {};
        return {
            label: configPanel.selectedNode.label,
            icon: getIcon(configPanel.selectedNode.icon),
            color: getCategoryColor(configPanel.selectedNode.nodeDetails?.categoryId)
        }
    }, [configPanel.selectedNode]);

    // Get the current display label (draft label or original label)
    const displayLabel = configPanel.draftLabel ?? headerDetails.label ?? "";

    const InnerConfigPanel = useMemo(() => {
        if (!configPanel.selectedNode) return Default;
        return getConfigPanel(configPanel.selectedNode.id);
    }, [configPanel.selectedNode]);

    function getConfigPanel(nodeId?: SidePanelNodeId): ConfigPanelsRenderer {
        if (!nodeId) return Default;
        return ConfigPanelsRegistry[nodeId] ?? Default;
    }

    function handleClosePanel(): void {
        configPanel.closeConfigPanel();
    }

    function handleLabelChange(value: string): void {
        configPanel.setDraftLabel(value);
    }


    return (
        <div className={cls("config-panel-container", configPanel.isConfigPanelOpen && "open")}>
            <div className="config-panel-contents">

                <div className="config-panel-header">
                    <div className="config-panel-header-section">
                        <div className="icon-wrapper" style={{ backgroundColor: headerDetails.color }}>
                            {headerDetails.icon}
                        </div>
                        {configPanel.isLabelEditable ? (
                            <CommonInput
                                className="header-title-input"
                                controlledValue={displayLabel}
                                onChange={handleLabelChange}
                                placeholder="Enter node name"
                            />
                        ) : (
                            <div className="header-title">
                                {headerDetails.label}
                            </div>
                        )}
                    </div>

                    <div className="config-panel-header-section">
                        <CommonButton className="close-button" onClick={handleClosePanel} noBackground>
                            <Icons.SVGClose />
                        </CommonButton>
                    </div>
                </div>

                <div className="inner-config">
                    {!configPanel.selectedNode ? undefined :
                        <InnerConfigPanel
                            node={configPanel.selectedNode}
                        />
                    }
                </div>

                <div className="config-panel-footer">
                    <CommonButton
                        className="config-button cancel"
                        noBackground
                        onClick={configPanel.discardChanges}
                    >
                        Cancel
                    </CommonButton>
                    <CommonButton
                        className="config-button save"
                        onClick={configPanel.saveChanges}
                        disabled={!configPanel.isDirty}
                    >
                        Save
                    </CommonButton>
                </div>

            </div>
        </div>
    );
}