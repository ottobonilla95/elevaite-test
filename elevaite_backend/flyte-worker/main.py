import os
from pprint import pprint
import sys
import flytekit
from flytekit.models.common import NamedEntityIdentifier
from flytekit.models.admin.workflow import Workflow
from flytekit.models.core.identifier import Identifier
from flytekit.configuration import Config, ImageConfig, PlatformConfig
from flytekit.tools.translator import Options
from flyteidl.service import admin_pb2_grpc
from flytekit.clients.friendly import SynchronousFlyteClient
from flytekit.remote import FlyteRemote, FlyteWorkflow
from flytekit.configuration import SerializationSettings, FastSerializationSettings
from elevaitelib.rpc import start_rpc_server, RPCClient

from worker.workflows.s3_ingest import (
    s3_ingest_callback,
    s3_ingest_workflow as s3_ingest_wf,
)
from worker.workflows.example import wf as example_wf
from worker.util.interfaces import S3IngestData, Secrets
from worker.util.func import get_flyte_remote, get_secrets


def main():
    # start_rpc_server()
    # # fibonacci_rpc = RPCClient()

    remote = get_flyte_remote()
    # client = SynchronousFlyteClient(cfg=PlatformConfig(insecure=True))

    # res = client.list_workflows_paginated(
    #     identifier=NamedEntityIdentifier(project="elevaite", domain="development")
    # )
    # for a in res[0]:
    #     print(f"{a.id.name}, {a.id.version}")
    #     pprint(a.closure._compiled_workflow.__dict__, depth=10)

    # for node in s3_ingest_wf.nodes:
    #     pprint(node.flyte_entity.__dict__)
    #     print(node.id)
    #     print()

    # connection = get_rmq_connection()
    # channel = connection.channel()
    # channel.queue_declare(queue="s3_ingest")
    # channel.queue_declare(queue="preprocess")

    # channel.basic_consume(
    #     queue="s3_ingest", on_message_callback=s3_ingest_callback, auto_ack=True
    # )
    # channel.basic_consume(
    #     queue="preprocess", on_message_callback=preprocess_callback, auto_ack=True
    # )
    print("Awaiting Messages")

    # _, native_url = remote.fast_package(root=f"{os.getcwd()}/elevaite_backend/flyte-worker/worker/workflows")  # type: ignore

    # flyte_workflow = remote.register_workflow(
    #     entity=s3_ingest_wf,
    #     serialization_settings=SerializationSettings(
    #         image_config=ImageConfig.auto(img_name="localhost:30000/flyte_base:latest"),
    #         version="v46",
    #         fast_serialization_settings=FastSerializationSettings(
    #             enabled=True, destination_dir="./", distribution_location=native_url
    #         ),
    #     ),
    # )

    # flyte_workflow = remote.register_script(
    #     entity=s3_ingest_wf,
    #     image_config=ImageConfig.auto(img_name="localhost:30000/flyte_base:latest"),
    # )

    # print(""" [x] Requesting hello({"hello":"world"})""")
    # response = fibonacci_rpc.hello({"hello": "world"})
    # print(f" [.] Got {response}, with type {type(response)}")

    # channel.start_consuming()
    # remote.register_workflow(
    #     s3_ingest_wf,
    #     version="1",
    # )
    # register_script(workflow=s3_ingest_wf, remote=remote)
    # remote.register_workflow(example_wf, version="1")
    # remote.execute(example_wf, inputs={"name": "Hello"})

    # executions = remote.recent_executions()
    # for exe in executions:
    #     print(exe)

    wf = remote.fetch_workflow(
        name="flyte-worker.worker.workflows.s3_ingest.s3_ingest_workflow"
    )

    # remote.

    if wf.flyte_tasks is not None:
        print(len(wf.flyte_tasks))
        for task in wf.flyte_tasks:
            pprint(task.id)

    exec = remote.execute(
        wf,
        inputs={
            "input": S3IngestData(
                applicationId=1,
                datasetId="3abcba29-490c-441f-bb37-28743afa28f0",
                projectId="7f66ade4-2bf0-4d46-a2dc-c2aee9e9e043",
                instanceId="06ae4f5f-6f93-4b70-9eaf-d24573ded430",
                roleARN="",
                type="s3_ingest",
                url="s3://training-data-webex/uncompressed/data/",
                useEC2=False,
            ).dict(),
            "secrets": get_secrets().dict(),
        },
        # envs=get_secrets().dict(),
    )
    flytekit.Deck


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
