"Prebuilt workflow, ingesting servicenow tickets"

import json
import sys
from typing import Any, Dict, List
from elevaite_client.rpc.client import RPCClient, RPCLogger, RedisRPCHelper
from elevaite_client.rpc.interfaces import (
    LogInfo,
    RepoNameInput,
    SetInstanceChartDataInput,
)
from flytekit import task, workflow
import lakefs
from pydantic import BaseModel
from ..util.func import get_secrets, get_secrets_dict, path_leaf
from elevaite_client.connectors import lakefs


class ServiceNowTicket(BaseModel):
    problem_description: str
    source_ref_id: str
    source_url: str
    resolution: str


class ServiceNowIngestDataDTO(BaseModel):
    datasetId: str
    projectId: str
    instanceId: str
    tickets: List[ServiceNowTicket]


@task(enable_deck=True, environment=get_secrets_dict())
def servicenow_ingest(_data: Dict[str, str | int | bool | Any]):
    data = ServiceNowIngestDataDTO.parse_obj(_data)
    secrets = get_secrets()
    rpc_client = RPCClient()
    r = RedisRPCHelper(key=data.instanceId, client=rpc_client)
    logger = RPCLogger(key=data.instanceId, client=rpc_client)
    LAKEFS_ACCESS_KEY_ID = secrets.LAKEFS_ACCESS_KEY_ID
    LAKEFS_SECRET_ACCESS_KEY = secrets.LAKEFS_SECRET_ACCESS_KEY
    LAKEFS_ENDPOINT_URL = secrets.LAKEFS_ENDPOINT_URL
    LAKEFS_STORAGE_NAMESPACE = secrets.LAKEFS_STORAGE_NAMESPACE

    if data.datasetId is None:
        raise Exception("No datasetId recieved")

    repo_name = rpc_client.get_repo_name(
        RepoNameInput(dataset_id=data.datasetId, project_id=data.projectId)
    )

    repo = lakefs.get_or_create_lakefs_repo(
        repo_name=repo_name,
        options={
            "key_id": LAKEFS_ACCESS_KEY_ID,
            "secret_key": LAKEFS_SECRET_ACCESS_KEY,
            "endpoint": LAKEFS_ENDPOINT_URL,
            "namespace": LAKEFS_STORAGE_NAMESPACE,
        },
    )
    logger.info(msg="Initialized lake repository")
    lakefs_branch = repo.branch("main")

    logger.info(msg="Starting file ingestion")

    for ticket in data.tickets:
        r.set_value(path=".currentFile", obj=path_leaf(ticket.source_ref_id))
        obj = lakefs_branch.object(f"{ticket.source_ref_id}.json")
        with obj.writer(mode="w", pre_sign=True, content_type="application/json") as fd:
            json.dump(ticket.dict(), fd, ensure_ascii=False, indent=4)
        r.set_value(path=".ingested_size", obj=sys.getsizeof(ticket.json()))
        r.set_value(path=".ingested_items", obj=1)

    rpc_client.set_instance_chart_data(
        SetInstanceChartDataInput(instance_id=data.instanceId)
    )

    logger.info(msg="Completed file ingestion")


@workflow()
def servicenow_ingest_workflow(data: Dict[str, str | int | bool | Any]):
    servicenow_ingest(_data=data)
