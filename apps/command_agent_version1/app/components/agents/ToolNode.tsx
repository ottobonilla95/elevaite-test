import { CommonButton } from "@repo/ui/components";
import { GripHorizontal, PenLine, Trash2 } from "lucide-react";
import { Handle, Position } from "react-flow-renderer";
import { type ToolNodeData } from "../../lib/interfaces";
import { getToolIcon } from "./iconUtils";
import "./ToolNode.scss";



interface ToolNodeProps {
  id: string;
  data: ToolNodeData;
  selected: boolean;
}

export function ToolNode({ id, data, selected }: ToolNodeProps): JSX.Element {
    const { type: _type, name, tool, onDelete, onAction } = data;


    function handleDelete(event: React.MouseEvent): void {
        event.stopPropagation();
        onDelete(id);
    }

    function handleEdit(): void {
        handleAction("editTool");
    }
    
    function handleAction(action: string): void {
        if (onAction) onAction(id, action, data);
    }



    return (
        <div className="tool-node-container">
            <div className={["tool-node", selected ? "selected" : undefined].filter(Boolean).join(" ")}>
                <GripHorizontal className="grip-icon"/>

                <div className="main-details-container">
                    <div className="icon-container">
                        {getToolIcon(tool.name)}
                    </div>
                    <div className="labels-container">
                        <div className="top-label-container">
                            <div className="label-name">{name}</div>
                            <div className="buttons-container">
                                <CommonButton
                                    onClick={handleEdit}
                                    noBackground
                                >
                                    <PenLine size={16} />
                                </CommonButton>
                                <CommonButton
                                    onClick={handleDelete}
                                    noBackground
                                >
                                    <Trash2 size={16} />
                                </CommonButton>
                            </div>
                        </div>
                        <div className="label-description" title={tool.description}>{tool.description}</div>
                    </div>
                </div>

                {!tool.tags || tool.tags.length === 0 ? undefined :
                    <div className="tool-tags-container">
                        {tool.tags.map(tag =>
                            <div key={tag} className="tool-tag">{tag}</div>
                        )}
                    </div>
                }
            </div>


            <Handle
                type="target"
                position={Position.Top}
                className="input-handle"
                id={`${id}-target`}
            />
            <Handle
                type="source"
                position={Position.Bottom}
                className="output-handle"
                id={`${id}-source`}
            />
        </div>
    );
}

