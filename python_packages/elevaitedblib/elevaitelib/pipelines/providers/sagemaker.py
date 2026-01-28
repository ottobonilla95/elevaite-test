import threading
from typing import List

from .base import PipelineProvider
from ..utils.common.docker import remove_docker_image as delete
from ..utils.json2sagemaker import (
    load_pipeline_definition,
    run_tasks_from_json,
    monitor_pipeline,
)


class SageMakerPipelineProvider(PipelineProvider):
    def __init__(self):
        super().__init__()

    def create_pipelines(self, pipeline_configs: List[dict]) -> int:
        threads = []

        def run_pipeline(pipeline_config: dict):
            run_tasks_from_json(pipeline_def=pipeline_config, watch=False)

        for pipeline_config in pipeline_configs:
            thread = threading.Thread(target=run_pipeline, args=(pipeline_config,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return 200

    def delete_pipelines(self, pipeline_ids: List[str]) -> int:
        threads = []

        def delete_pipeline_thread(image_name: str):
            delete(image_name=image_name)

        for image_name in pipeline_ids:
            thread = threading.Thread(target=delete_pipeline_thread, args=(image_name))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return 200

    def monitor_pipelines(
        self, pipeline_run_ids: List[str], summarize: bool = False
    ) -> List[str]:
        threads = []
        outputs = []
        lock = threading.Lock()

        def monitor_pipeline_thread(execution_arn: str):
            result = monitor_pipeline(execution_arn=execution_arn, summarize=summarize)
            with lock:
                outputs.append(result)

        for execution_arn in pipeline_run_ids:
            thread = threading.Thread(
                target=monitor_pipeline_thread, args=(execution_arn,)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return outputs

    def rerun_pipelines(self, pipeline_ids: List[str]) -> int:
        threads = []

        def rerun_pipeline(pipeline_id: str):
            pipeline_def = load_pipeline_definition(pipeline_id)
            run_tasks_from_json(pipeline_def=pipeline_def, watch=False)

        for pipeline_id in pipeline_ids:
            thread = threading.Thread(target=rerun_pipeline, args=(pipeline_id))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return 200
