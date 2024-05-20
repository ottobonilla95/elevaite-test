import os
import sys
from elevaitelib.rpc.connection import get_rmq_connection
from flytekit.configuration import Config, ImageConfig
from flytekit.remote import FlyteRemote, FlyteWorkflow
from flytekit.configuration import SerializationSettings
from elevaitelib.rpc import start_rpc_server, RPCClient

from workflows.s3_ingest import (
    s3_ingest_callback,
    s3_ingest_workflow,
    initialize_resources,
)
from workflows.example import wf as example_wf
from util.interfaces import S3IngestData, Secrets
from util.func import get_flyte_remote, get_secrets


def main():
    start_rpc_server()
    fibonacci_rpc = RPCClient()

    remote = get_flyte_remote()

    connection = get_rmq_connection()
    channel = connection.channel()
    channel.queue_declare(queue="s3_ingest")
    channel.queue_declare(queue="preprocess")

    channel.basic_consume(
        queue="s3_ingest", on_message_callback=s3_ingest_callback, auto_ack=True
    )
    # channel.basic_consume(
    #     queue="preprocess", on_message_callback=preprocess_callback, auto_ack=True
    # )
    print("Awaiting Messages")

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

    # step = remote.register_script(
    #     entity=initialize_resources,
    #     version=None,
    #     module_name="worker",
    #     source_path=".",
    #     copy_all=True,
    #     image_config=ImageConfig.auto(img_name="localhost:30000/flyte_base:latest"),
    # )

    # wf = remote.register_script(
    #     entity=s3_ingest_workflow,
    #     version=None,
    #     module_name="worker",
    #     source_path=".",
    #     copy_all=True,
    #     image_config=ImageConfig.auto(img_name="localhost:30000/flyte_base:latest"),
    # )
    # remote.execute(
    #     wf,
    #     inputs={
    #         "input": S3IngestData(
    #             applicationId=1,
    #             datasetId="",
    #             projectId="7f66ade4-2bf0-4d46-a2dc-c2aee9e9e043",
    #             instanceId="abcd",
    #             roleARN="",
    #             type="s3_ingest",
    #             url="s3://training-data-webex/uncompressed/data/",
    #             useEC2=False,
    #         ).dict(),
    #         "secrets": get_secrets().dict(),
    #     },
    # )

    flyte_wf = remote.fetch_workflow(name="workflows.example.wf")
    execution = remote.execute(flyte_wf, inputs={"name": "Kermit"})


# def register_script(workflow: FlyteWorkflow, remote: FlyteRemote):
#     main_script_path = os.path.abspath(__file__)
#     source_dir = os.path.dirname(main_script_path)

#     # some custom use-case-specific logic
#     if os.path.basename(source_dir) == "scripts":
#         source_path = os.path.dirname(source_dir)
#     else:
#         source_path = source_dir

#     return remote.register_script(
#         entity=workflow,
#         version="4",
#         module_name="workflows",
#         source_path=source_path,
#         copy_all=True,
#     )


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Interrupted")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)
