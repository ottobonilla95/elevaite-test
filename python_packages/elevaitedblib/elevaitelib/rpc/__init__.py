import time
from . import func as rpc_func
from elevaite_client.rpc.client import RPCClient
from .server import RPCServer
from elevaite_client.rpc.constants import RPCRoutingKeys


def start_rpc_server():
    print(" [x] Starting RPC Server")
    server = RPCServer()
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.set_redis_stats, func=rpc_func.set_redis_stats
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.set_instance_running,
        func=rpc_func.set_instance_running,
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.set_instance_completed,
        func=rpc_func.set_instance_completed,
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.set_pipeline_step_meta,
        func=rpc_func.set_pipeline_step_meta,
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.set_pipeline_step_completed,
        func=rpc_func.set_pipeline_step_completed,
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.set_pipeline_step_running,
        func=rpc_func.set_pipeline_step_running,
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.set_instance_chart_data,
        func=rpc_func.set_instance_chart_data,
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.get_repo_name, func=rpc_func.get_repo_name
    )
    server.bind_and_consume(routing_key=RPCRoutingKeys.log_info, func=rpc_func.log_info)
    server.bind_and_consume(routing_key=RPCRoutingKeys.hello, func=rpc_func.hello)
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.set_redis_value, func=rpc_func.set_redis_value
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.get_max_version_of_dataset,
        func=rpc_func.get_max_version_of_dataset,
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.create_dataset_version,
        func=rpc_func.create_dataset_version,
    )
    server.bind_and_consume(
        routing_key=RPCRoutingKeys.register_experiment,
        func=rpc_func.register_experiment,
    )
    time.sleep(1)
    print(" [x] Started RPC Server")
