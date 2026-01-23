import { cls, CommonButton, CommonMenu, type CommonMenuItem } from "@repo/ui";
import { Handle, Position, type Node, type NodeProps } from "@xyflow/react";
import { useMemo, type JSX } from "react";
import { useCanvas } from "../../lib/contexts/CanvasContext";
import { NodeStatus, type CanvasNodeType } from "../../lib/enums";
import { type NodeStatusInfo, type SidePanelPayload } from "../../lib/interfaces";
import { getCategoryColor, getCategoryIcon, getCategoryLabel, getIcon, getStatusDisplay } from "../../lib/utilities/nodes";
import { Icons } from "../icons";
import "./CommandNode.scss";
import { CommandNodeTags } from "./CommandNodeTags";
import { CommandNodeTray } from "./CommandNodeTray";




type CommandNodeDataType = Node<SidePanelPayload, CanvasNodeType.COMMAND>;


export function CommandNode({ id, data, selected }: NodeProps<CommandNodeDataType>): JSX.Element {
	const canvasContext = useCanvas();
	const KEEP_HANDLES_STATIC = true;
	const stepStatuses: Record<string, NodeStatus> | undefined = canvasContext.executionStatus?.step_statuses;
	const executionStepStatus: NodeStatus | undefined = stepStatuses?.[id];
	const derivedStatus = executionStepStatus ?? NodeStatus.PENDING;
	const nodeStatus: NodeStatusInfo = useMemo(() => ({ status: derivedStatus }), [derivedStatus]);
	const statusTag = useMemo(() => getStatusDisplay(nodeStatus.status), [nodeStatus.status]);


	const nodeMenu: CommonMenuItem[] = [
		{ label: "Swap Node", icon: <Icons.Node.SVGSwap />, onClick: handleMenuSwap, },
		{ label: "Disable Node", icon: <Icons.Node.SVGDisable />, onClick: handleMenuDisable, },
		{ label: "Duplicate Node", icon: <Icons.Node.SVGDuplicate />, onClick: handleMenuDuplicate, },
		{ label: "Vertical Ports", icon: <Icons.Node.SVGVertical />, onClick: handleMenuVertical, },
		{ label: "Delete Node", icon: <Icons.Node.SVGDelete color="var(--ev-colors-danger)" />, onClick: handleMenuDelete, },
	];




	function handleViewToggle(): void {
		canvasContext.nodeViewChange(id);
	}


	// Menu functions
	function handleMenuSwap(): void {
		console.log("Handling swap");
		console.log("Node data:", data);
	}

	function handleMenuDisable(): void {
		console.log("Handling disable");
	}

	function handleMenuDuplicate(): void {
		console.log("Handling duplication");
	}

	function handleMenuVertical(): void {
		console.log("Handling vertical");
	}

	function handleMenuDelete(): void {
		canvasContext.deleteNodeById(id);
	}

	const isActive = nodeStatus.status === NodeStatus.RUNNING || nodeStatus.status === NodeStatus.WAITING;

	return (
		<div className="command-node-wrapper">

			<div
				className={cls(
					"command-node-container",
					selected ? "selected" : undefined,
					isActive ? "active" : undefined,
				)}
				data-status={nodeStatus.status}
			>

				{!data.nodeDetails?.categoryId ? undefined :
					<CommandNodeTags
						tags={[
							{
								color: getCategoryColor(data.nodeDetails.categoryId),
								background: getCategoryColor(data.nodeDetails.categoryId, true),
								icon: getCategoryIcon(data.nodeDetails.categoryId),
								label: getCategoryLabel(data.nodeDetails.categoryId, true),
							},
							statusTag
						]}
					/>
				}

				{/* eslint-disable-next-line @typescript-eslint/no-unnecessary-condition -- KEEP_HANDLES_STATIC is a flag */}
				<div className={["simple-view-container", KEEP_HANDLES_STATIC ? "static-handles" : undefined].filter(Boolean).join(" ")}>

					<div className="command-node-icon">
						{data.nodeDetails?.isNewItem ? !data.nodeDetails.categoryId ? undefined :
							getCategoryIcon(data.nodeDetails.categoryId, true)
							:
							<div className="icon-wrapper" style={{ backgroundColor: getCategoryColor(data.nodeDetails?.categoryId) }}>
								{getIcon(data.icon)}
							</div>
						}
					</div>
					<div className="command-node-label">
						{data.label}
					</div>
					<div className="command-node-controls-container">
						<CommonButton
							className="toggle-view-button nodrag nopan"
							onClick={handleViewToggle}
						>
							{data.nodeDetails?.isExpanded ? <Icons.SVGDetailedView /> : <Icons.SVGSimpleView />}
						</CommonButton>
						<CommonMenu
							className="nodrag nopan"
							menu={nodeMenu}
							useAlternativeClickOutsideDetector
						/>
					</div>

					<Handle type="target" position={Position.Left} />
					<Handle type="source" position={Position.Right} />
				</div>

				<CommandNodeTray
					isOpen={data.nodeDetails?.isExpanded ?? false}
					nodeId={data.id}
					nodeData={data}
					status={nodeStatus}
				/>
			</div>

		</div>
	);
}
