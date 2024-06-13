from enum import Enum
from typing import Any, Dict, List, Optional, TypeGuard, TypedDict

from pydantic import BaseModel
from flytekit.models.core.compiler import CompiledWorkflowClosure, CompiledWorkflow
from flytekit.models.core.workflow import (
    BranchNode,
    WorkflowNode,
    GateNode,
    ArrayNode,
    Node,
    TaskNode,
)
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
    arrayNode: Optional[ArrayNode]
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

def getNodeExecutionDetails(node: dNode, tasks: List[CompiledTask]) -> NodeExecutionInfo:
    if node.value is None: 
        raise Exception("Not sure what to do")
    taskNode = node.value.array_node.node.task_node if node.value.array_node is not None else node.value.task_node
    taskType = getTaskTypeFromCompiledNode(taskNode=taskNode, tasks=tasks) # type: ignore
    

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


def createDNode(props: CreateDNodeProps) -> dNode:
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
        value=nodeValue,  # type: ignore
        type=type,
        edges=[],
        nodes=[],
        level=level,
        name=getDisplayName(props.compiledNode),
        **nodeMetadata.__dict__,
    )
    if not isStartOrEndNode(node=props.compiledNode):
        nodeExecutionInfo = 

    return output


def buildDAG(
    contextWorkflow,
    contextCompiledNode,
    compiledWorkflowClosure,
    graphType,
    nodeMetadataMap,
    root,
    staticExecutionIdsMap,
):
    match (graphType):
        case dTypes.branch:
            parseBranch(
                root=root,
                contextCompiledNode=contextCompiledNode,
                nodeMetadataMap=nodeMetadataMap,
                staticExecutionIdsMap=staticExecutionIdsMap,
                workflow=compiledWorkflowClosure,
            )
        # case dTypes.subworkflow:
        #     parseWorkflow()
        # case dTypes.primary:
        #     parseWorkflow()


def parseBranch(
    root,
    contextCompiledNode: CompiledNode,
    nodeMetadataMap,
    staticExecutionIdsMap,
    workflow,
):
    otherNode = (
        contextCompiledNode.branchNode.if_else.other
        if contextCompiledNode.branchNode is not None
        else None
    )
    thenNode = (
        contextCompiledNode.branchNode.if_else.case.then_node
        if contextCompiledNode.branchNode is not None
        else None
    )
    elseNode = (
        contextCompiledNode.branchNode.if_else.else_node
        if contextCompiledNode.branchNode is not None
        else None
    )

    if thenNode:
        parseNode()


def parseNode(
    node: Node,
    root: dNode,
    nodeMetadataMap,
    staticExecutionIdsMap,
    compiledWorkflowClosure: CompiledWorkflowClosure,
):
    _dNode: dNode
    if node.branch_node:
        _dNode = createDNode(
            CreateDNodeProps(
                {
                    "compiledNode": node,
                    "parentDNode": root,
                    "nodeMetadataMap": nodeMetadataMap,
                    "staticExecutionIdsMap": staticExecutionIdsMap,
                    "compiledWorkflowClosure": compiledWorkflowClosure,
                }
            )
        )
        buildDAG(
            root=_dNode,
            contextCompiledNode=node,
            graphType=dTypes.branch,
            nodeMetadataMap=nodeMetadataMap,
            staticExecutionIdsMap=staticExecutionIdsMap,
            compiledWorkflowClosure=compiledWorkflowClosure,
            contextWorkflow=None,
        )
    elif node.workflow_node:
        if node.workflow_node.launchplan_ref:
            _dNode = createDNode(
                CreateDNodeProps(
                    {
                        "compiledNode": node,
                        "parentDNode": root,
                        "nodeMetadataMap": nodeMetadataMap,
                        "staticExecutionIdsMap": staticExecutionIdsMap,
                        "compiledWorkflowClosure": compiledWorkflowClosure,
                    }
                )
            )
        else:
            id = node.workflow_node.sub_workflow_ref
            subworkflow = getSubWorkflowFromId(id, compiledWorkflowClosure)
            _dNode = createDNode(
                CreateDNodeProps(
                    {
                        "compiledNode": node,
                        "parentDNode": root,
                        "nodeMetadataMap": nodeMetadataMap,
                        "staticExecutionIdsMap": staticExecutionIdsMap,
                        "compiledWorkflowClosure": compiledWorkflowClosure,
                    }
                )
            )
            buildDAG(
                root=_dNode,
                contextCompiledNode=node,
                graphType=dTypes.branch,
                nodeMetadataMap=nodeMetadataMap,
                staticExecutionIdsMap=staticExecutionIdsMap,
                compiledWorkflowClosure=compiledWorkflowClosure,
                contextWorkflow=None,
            )
    elif node.array_node:
        arrayNode = node.array_node.node
        taskNode = arrayNode.task_node
        taskType = getTaskTypeFromCompiledNode(taskNode=taskNode, tasks=compiledWorkflowClosure.tasks)  # type: ignore
        _dNode = createDNode(
            CreateDNodeProps(
                {
                    "compiledNode": node,
                    "parentDNode": root,
                    "nodeMetadataMap": nodeMetadataMap,
                    "staticExecutionIdsMap": staticExecutionIdsMap,
                    "compiledWorkflowClosure": compiledWorkflowClosure,
                    "taskTemplate": taskType,
                }
            )
        )
    elif node.task_node:
        taskType = getTaskTypeFromCompiledNode(
            taskNode=node.task_node, tasks=compiledWorkflowClosure.tasks
        )
        _dNode = createDNode(
            CreateDNodeProps(
                {
                    "compiledNode": node,
                    "parentDNode": root,
                    "nodeMetadataMap": nodeMetadataMap,
                    "staticExecutionIdsMap": staticExecutionIdsMap,
                    "compiledWorkflowClosure": compiledWorkflowClosure,
                    "taskTemplate": taskType,
                }
            )
        )
    else:
        _dNode = createDNode(
            CreateDNodeProps(
                {
                    "compiledNode": node,
                    "parentDNode": root,
                    "nodeMetadataMap": nodeMetadataMap,
                    "staticExecutionIdsMap": staticExecutionIdsMap,
                    "compiledWorkflowClosure": compiledWorkflowClosure,
                }
            )
        )
    root.nodes.append(_dNode)


def isCompiledWorkflowClosure(obj: Any) -> TypeGuard[CompiledWorkflowClosure]:
    return type(obj) == "object" and obj.primary is not None


def getSubWorkflowFromId(id, workflow: CompiledWorkflowClosure | CompiledWorkflow):
    subworkflows: List[CompiledWorkflow] = (
        workflow.sub_workflows if isCompiledWorkflowClosure(workflow) else []
    )

    for k in subworkflows:
        if k.template.id == id:
            return k
    return None


def getTaskTypeFromCompiledNode(taskNode: TaskNode, tasks: List[CompiledTask]):
    if taskNode.reference_id is None:
        return None
    for task in tasks:
        if taskNode.reference_id == task.template.id:
            return task
    return None


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

    dag: dNode

    # try:
    #     dag = buildDAG()
