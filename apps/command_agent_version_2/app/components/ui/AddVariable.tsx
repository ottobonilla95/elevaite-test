import { CommonMenu, type CommonMenuItem } from "@repo/ui";
import { useMemo, type JSX } from "react";
import { type BuiltInVariable } from "../../lib/actions/steps";
import { useCanvas } from "../../lib/contexts/CanvasContext";
import { useConfigPanel } from "../../lib/contexts/ConfigPanelContext";
import { CategoryId } from "../../lib/enums";
import { type SidePanelPayload } from "../../lib/interfaces";
import { getCategoryLabel } from "../../lib/utilities/nodes";
import { Icons } from "../icons";
import "./AddVariable.scss";


interface NodeVariable {
    nodeId: string;
    label: string;
    category: string;
    variableLabel: string;
}

interface AddVariableProps {
    onSelect?: (variableLabel: string) => void;
}

export function AddVariable(props: AddVariableProps): JSX.Element {
    const { nodes } = useCanvas();
    const { onSelect } = props;
    const { builtInVariables, builtInVariablesLoading } = useConfigPanel();

    const nodeVariables = useMemo<NodeVariable[]>(() => {
        return nodes
            .map(node => {
                const payload = node.data as SidePanelPayload;
                const categoryId = payload.nodeDetails?.categoryId;
                
                // Determine the variable suffix based on category
                const isAgent = categoryId === CategoryId.AGENTS || categoryId === CategoryId.EXTERNAL_AGENTS;
                const suffix = isAgent ? "response" : "text";
                
                return {
                    nodeId: node.id,
                    label: payload.label,
                    category: categoryId ? getCategoryLabel(categoryId, true) : "Node",
                    variableLabel: `{{${node.id}.${suffix}}}`,
                };
            })
            .sort((a, b) => a.label.localeCompare(b.label));
    }, [nodes]);

    const menuItems = useMemo<CommonMenuItem[]>(() => {
        if (builtInVariablesLoading) {
            return [
                { label: "Loading...", isCategoryLabel: false, onClick: () => { /** */ }, isDisabled: true },
            ];
        }

        const items: CommonMenuItem[] = [];

        // Node Variables
        if (nodeVariables.length > 0) {
            items.push({ label: "Node Variables", isCategoryLabel: true });
            
            for (const nodeVar of nodeVariables) {
                items.push({
                    label: nodeVar.label,
                    onClick: () => { handleNodeVariableSelect(nodeVar.variableLabel); },
                    suffix: <span className="variable-category-tag">{nodeVar.category}</span>,
                });
            }
        }

        // System Variables
        const sortedVariables = [...builtInVariables].sort((a, b) => 
            a.name.localeCompare(b.name)
        );

        items.push({ label: "System Variables", isCategoryLabel: true });

        for (const variable of sortedVariables) {
            items.push({
                label: `{{${variable.name}}}`,
                onClick: () => { handleBuiltInVariableSelect(variable); },
                suffix: <span className="variable-category-tag">{variable.category}</span>,
            });
        }

        return items;
    }, [builtInVariables, builtInVariablesLoading, nodeVariables]);

    function handleNodeVariableSelect(variableLabel: string): void {
        if (onSelect) onSelect(variableLabel);
    }

    function handleBuiltInVariableSelect(variable: BuiltInVariable): void {
        if (onSelect) onSelect(`{{${variable.name}}}`);
    }

    return (
        <div className="add-variable-container">
            <CommonMenu
                menu={menuItems}
                menuIcon={
                    <>
                        <Icons.Node.SVGAddVariable />
                        <span className="add-variable-label">Add Variable</span>
                    </>
                }
                usePortal
                menuClassName="add-variable-menu"
            />
        </div>
    );
}