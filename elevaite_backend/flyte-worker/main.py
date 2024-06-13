import os
import sys

# from pprint import pprint
# import flytekit
# from flytekit.models.common import NamedEntityIdentifier
# from flytekit.models.admin.workflow import Workflow
# from flytekit.models.core.identifier import Identifier
# from flytekit.models.filters import Filter, FilterList
# from flytekit.configuration import Config, ImageConfig, PlatformConfig
# from flytekit.tools.translator import Options
# from flyteidl.service import admin_pb2_grpc
# from flytekit.clients.friendly import SynchronousFlyteClient
# from flytekit.remote import FlyteRemote, FlyteWorkflow
# from flytekit.configuration import SerializationSettings, FastSerializationSettings
from elevaitelib.rpc import start_rpc_server

from worker.workflows.s3_ingest import S3IngestData
from worker.util.func import get_flyte_remote, get_secrets, get_secrets_dict


def main():
    start_rpc_server()

    remote = get_flyte_remote()

    # client = SynchronousFlyteClient(cfg=PlatformConfig(insecure=True))

    # res = client.list_workflows_paginated(
    #     identifier=NamedEntityIdentifier(project="elevaite", domain="development"),
    # )
    # for a in res[0]:
    #     print(f"{a.id.name}, {a.id.version}")
    #     pprint(a.closure.compiled_workflow.tasks, depth=10)

    # res2 = client.list_workflow_ids_paginated(project="elevaite", domain="development")
    # pprint(res2[0])

    # res3 = client.get_workflow(res[0][1].id)
    # pprint(res3.closure.compiled_workflow)

    # remote.fetch_execution()

    # for t in res3.closure.compiled_workflow.tasks:
    #     pprint(t.template.__dict__)

    # for node in s3_ingest_wf.nodes:
    #     pprint(node.flyte_entity.__dict__)
    #     print(node.id)
    #     print()

    # print("Awaiting Messages")

    wf = remote.fetch_workflow(
        name="flyte-worker.worker.workflows.s3_ingest.s3_ingest_workflow"
    )

    # # remote.

    # if wf.flyte_tasks is not None:
    #     print(len(wf.flyte_tasks))
    #     for task in wf.flyte_tasks:
    #         pprint(task.id)

    # pprint(S3IngestData.schema())

    exec = remote.execute(
        wf,
        inputs={
            "data": {
                "datasetId": "3abcba29-490c-441f-bb37-28743afa28f0",
                "projectId": "7f66ade4-2bf0-4d46-a2dc-c2aee9e9e043",
                "instanceId": "06ae4f5f-6f93-4b70-9eaf-d24573ded430",
                "roleARN": "",
                "url": "s3://training-data-webex/uncompressed/data/",
                "useEC2": False,
            },
        },
        envs=get_secrets_dict(),
    )

    execname = exec.id.name

    exec2 = remote.fetch_execution(name=execname)
    exec2


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
