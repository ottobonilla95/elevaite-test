from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel
from flytekit.models.core.compiler import CompiledWorkflowClosure, CompiledWorkflow
from flytekit.models.core.workflow import BranchNode, WorkflowNode, GateNode
from flytekit.remote import FlyteWorkflow, FlyteNode, FlyteTask

startNodeId = "start-node"
endNodeId = "end-node"


class dTypes(Enum):
    task = 1
    primary = 2
    branch = 3
    subworkflow = 4
    start = 5
    end = 6
    nestedEnd = 7
    nestedStart = 8
    nestedMaxDepth = 9
    staticNode = 10
    staticNestedNode = 11
    gateNode = 12


class ResourceType(Enum):
    UNSPECIFIED = 0
    TASK = 1
    WORKFLOW = 2
    LAUNCH_PLAN = 3
    DATASET = 4


class Identifier(BaseModel):
    resourceType: Optional[ResourceType]
    project: str
    domain: str
    name: str
    version: str
    org: Optional[str]


class TaskTemplate(BaseModel):
    id: Identifier
    type: str
    shortDescription: Optional[str]


class CompiledTask(BaseModel):
    template: TaskTemplate


class NodeExecutionDetails(BaseModel):
    displayId: Optional[str]
    displayName: Optional[str]
    displayType: str
    scopedId: Optional[str]
    subWorkflowName: str
    taskTemplate: Optional[TaskTemplate]


class NodeExecutionInfo(NodeExecutionDetails):
    scopedId: Optional[str]


class CompiledNode(BaseModel):
    id: str
    branchNode: Optional[BranchNode]
    workflowNode: Optional[WorkflowNode]
    gateNode: Optional[GateNode]
    # sourceId: str
    # targetId: str


class dEdge(BaseModel):
    id: str
    sourceId: str
    targetId: str


class dNode(BaseModel):
    id: str
    scopedId: str
    type: dTypes
    name: str
    value: Optional[FlyteNode]
    nodes: List["dNode"]
    edges: List[dEdge]
    expanded: Optional[bool]
    grayedOut: Optional[bool]
    level: Optional[int]
    isParentNode: Optional[bool]
    nodeExecutionInfo: Optional[NodeExecutionInfo]


class NodeMetadata(BaseModel):
    expanded: Optional[bool]
    isParentNode: Optional[bool]


class CreateDNodeProps(dict):
    compiledNode: FlyteNode
    parentDNode: Optional[dNode]
    taskTemplate: Optional[FlyteTask]
    typeOverride: Optional[dTypes]
    nodeMetadataMap: Dict[str, NodeMetadata]
    staticExecutionIdsMap: Optional[Any]
    compiledWorkflowClosure: CompiledWorkflowClosure


def isStartNode(node: FlyteNode) -> bool:
    return node.id == startNodeId


def isEndNode(node: FlyteNode) -> bool:
    return node.id == endNodeId


def isStartOrEndNode(node: dNode | FlyteNode):
    return node.id == startNodeId or node.id == endNodeId


def getNodeTypeFromCompiledNode(node: FlyteNode) -> dTypes:
    if isStartNode(node):
        return dTypes.start

    if isEndNode(node):
        return dTypes.end

    if node.branch_node:
        return dTypes.subworkflow

    if node.workflow_node:
        if node.workflow_node.launchplan_ref:
            return dTypes.task

        return dTypes.subworkflow
    if node.gate_node:
        return dTypes.gateNode

    return dTypes.task


def getDisplayName(context: Any, truncate: bool = True):
    displayName = ""
    if isinstance(context, FlyteNode):
        displayName = context.metadata.name
    elif isinstance(context, FlyteWorkflow):
        displayName = context.name
    else:
        displayName = context.id

    if displayName == startNodeId:
        return "start"
    if displayName == endNodeId:
        return "end"
    if displayName.index(".") > 0 and truncate:
        return displayName[displayName.rfind(".") + 1 :]
    return displayName


def createDNode(props: CreateDNodeProps):
    nodeValue = (
        props.compiledNode
        if props.taskTemplate is None
        else {**props.compiledNode.__dict__, **props.taskTemplate.__dict__}
    )
    scopedId = ""
    if (
        isStartOrEndNode(props.compiledNode)
        and props.parentDNode is not None
        and not isStartOrEndNode(props.parentDNode)
    ):
        scopedId = f"{props.parentDNode.scopedId}-{props.compiledNode.id}"
    elif props.parentDNode is not None and props.parentDNode.type != dTypes.start:
        if (
            props.parentDNode.type == dTypes.branch
            or props.parentDNode.type == dTypes.subworkflow
        ):
            scopedId = f"{props.parentDNode.scopedId}-0-{props.compiledNode.id}"
        else:
            scopedId = f"{props.parentDNode.scopedId}-{props.compiledNode.id}"
    else:
        scopedId = props.compiledNode.id
    type = (
        getNodeTypeFromCompiledNode(props.compiledNode)
        if props.typeOverride is None
        else props.typeOverride
    )

    nodeMetadata = (
        props.nodeMetadataMap[scopedId]
        if props.nodeMetadataMap[scopedId] is not None
        else {}
    )
    level = (
        props.parentDNode.level + 1
        if (props.parentDNode is not None and props.parentDNode.level is not None)
        else 0
    )

    output = dNode(
        id=props.compiledNode.id,
        scopedId=scopedId,
        value=nodeValue,
        type=type,
        edges=[],
        nodes=[],
        level=level,
        name=getDisplayName(props.compiledNode),
        **nodeMetadata.__dict__,
    )


def workflowToDagTransformer(
    workflowClosure: CompiledWorkflowClosure, nodeMetadataMap: Dict[str, NodeMetadata]
):
    primary = workflowClosure.primary
    staticExecutionIdsMap = {}

    primaryWorkflowRoot = createDNode(
        CreateDNodeProps(
            {
                "compiledNode": {
                    id: startNodeId,
                },
                "nodeMetadataMap": nodeMetadataMap,
                "staticExecutionIdsMap": staticExecutionIdsMap,
                "compiledWorkflowClosure": workflowClosure,
            }
        )
    )
