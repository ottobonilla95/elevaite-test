from enum import Enum


EXCHANGE_NAME = "rpc_exchange"


class RPCRoutingKeys(str, Enum):
    set_redis_stats = "set_redis_stats"
    set_instance_running = "set_instance_running"
    set_instance_completed = "set_instance_completed"
    set_pipeline_step_meta = "set_pipeline_step_meta"
    set_pipeline_step_completed = "set_pipeline_step_completed"
    set_pipeline_step_running = "set_pipeline_step_running"
    set_instance_chart_data = "set_instance_chart_data"
    get_repo_name = "get_repo_name"
    hello = "hello"
    log_info = "log_info"
    log_error = "log_error"
    set_redis_value = "set_redis_value"
    get_max_version_of_dataset = "get_max_version_of_dataset"
    create_dataset_version = "create_dataset_version"
    get_dataset_version_commit_id = "get_dataset_version_commit_id"
    get_collection_name = "get_collection_name"
