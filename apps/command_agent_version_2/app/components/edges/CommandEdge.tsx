import { getBezierPath, type Edge, type EdgeProps } from "@xyflow/react";
import { useCanvas } from "../../lib/contexts/CanvasContext";
import { NodeStatus } from "../../lib/enums";
import "./CommandEdge.scss";

import type { JSX } from "react";

type CommandEdgeType = Edge<Record<string, never>, "command">;

export function CommandEdge({
	id,
	sourceX,
	sourceY,
	targetX,
	targetY,
	sourcePosition,
	targetPosition,
	target,
}: EdgeProps<CommandEdgeType>): JSX.Element {
	const canvasContext = useCanvas();

	const stepStatuses = canvasContext.executionStatus?.step_statuses;
	const targetStatus: NodeStatus = stepStatuses?.[target] ?? NodeStatus.PENDING;
	const isActive = targetStatus !== NodeStatus.PENDING;

	const [edgePath] = getBezierPath({
		sourceX,
		sourceY,
		sourcePosition,
		targetX,
		targetY,
		targetPosition,
	});

	return (
		<g>
			<path
				id={id}
				d={edgePath}
				className={isActive ? "command-edge active" : "command-edge"}
				fill="none"
				strokeWidth={2}
			/>
		</g>
	);
}
