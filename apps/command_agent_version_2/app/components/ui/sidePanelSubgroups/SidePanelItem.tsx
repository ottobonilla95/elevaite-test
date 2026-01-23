import { CommonButton, CommonTray } from "@repo/ui";
import { type CategoryId } from "../../../lib/enums";
import { type NodeDetails, type SidePanelOption } from "../../../lib/interfaces";
import { getCategoryIcon, getIcon, getPayloadFromOption, setDragData } from "../../../lib/utilities/nodes";
import { Icons } from "../../icons";
import "./SidePanelItem.scss";



import type { JSX } from "react";



interface SidePanelItemBaseProps {
    onClick: (option?: SidePanelOption) => void;
    classname?: string;
    preventDrag?: boolean;
}

type SidePanelWithOptionProps = SidePanelItemBaseProps & {
    option: SidePanelOption;
    addLabel?: never;
    isExpanded?: boolean;
};

type SidePanelAddProps = SidePanelItemBaseProps & {
    option?: never;
    addLabel: string;
    isExpanded?: never;
};

export type SidePanelItemProps = SidePanelWithOptionProps | SidePanelAddProps;


export default function SidePanelItem({option, addLabel, onClick, isExpanded, preventDrag, classname}: SidePanelItemProps): JSX.Element {

    function handleClick(): void {
        onClick(option);
    }

    function handleDragStart(event: React.DragEvent<HTMLDivElement>): void {
        if (preventDrag || !option) return;
        const nodeDetails: NodeDetails = { categoryId: option.nodeDetails?.categoryId };
        setDragData(event, "application/command-node", getPayloadFromOption(option, nodeDetails));
        event.dataTransfer.effectAllowed = "move";

        const draggedElement = event.currentTarget;
        draggedElement.classList.add("dragging");
        setTimeout(() => {
            draggedElement.classList.remove("dragging");
        }, 100);
    }

    return (
        <>
            <div
                className={[
                    "side-panel-item-container",
                    classname,
                    isExpanded ? "expanded" : undefined,
                ].filter(Boolean).join(" ")}
                draggable={!preventDrag}
                onDragStart={handleDragStart}
            >
                <div className="side-panel-item-header">
                    <CommonButton onClick={handleClick} className={addLabel ? "add-item-button" : undefined}>
                        {option ? (option.isCategory ? getCategoryIcon(option.icon as CategoryId, true) : getIcon(option.icon)) : <Icons.SVGPlus/>}
                        <div className="side-panel-item-header-label">
                            {option ? option.label : addLabel}
                            {option?.tag ? <div className="label-tag">{option.tag}</div> : undefined}
                        </div>
                        {!option?.children ? undefined :
                            <div className="side-panel-chevron">
                                <Icons.SVGChevronDown/>
                            </div>
                        }
                    </CommonButton>
                </div>
            </div>
            {!option?.children ? undefined :
                <div className="side-panel-item-list-container">
                    <CommonTray isOpen={isExpanded ?? false}>
                        {option.children}
                    </CommonTray>
                </div>
            }
        </>
    );
}