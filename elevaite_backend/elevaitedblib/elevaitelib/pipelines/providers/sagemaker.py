import threading
from typing import List, Union

from .base import PipelineProvider
from ..utils.common.docker import remove_docker_image as delete
from ..utils.json2sagemaker import (
    load_pipeline_definition,
    run_pipeline_with_dynamic_dockerfile as run,
    monitor_pipeline as monitor,
)


class SageMakerPipelineProvider(PipelineProvider):
    def __init__(self):
        super().__init__()

    def create_pipelines(self, file_paths: List[str]) -> int:
        threads = []

        def run_pipeline(file_path: str):
            pipeline_def = load_pipeline_definition(file_path)
            run(pipeline_def=pipeline_def)

        for file_path in file_paths:
            thread = threading.Thread(target=run_pipeline, args=(file_path,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return 200

    def delete_pipelines(self, image_names: List[str]) -> int:
        threads = []

        def delete_pipeline_thread(image_name: str):
            delete(image_name=image_name)

        for image_name in image_names:
            thread = threading.Thread(target=delete_pipeline_thread, args=(image_name))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return 200

    def monitor_pipelines(
        self, execution_arn_list: List[str], summarize: bool = False
    ) -> List[Union[str, dict]]:
        threads = []
        outputs = []
        lock = threading.Lock()

        def monitor_pipeline_thread(execution_arn: str):
            result = monitor(execution_arn=execution_arn, summarize=summarize)
            with lock:
                outputs.append(result)

        for execution_arn in execution_arn_list:
            thread = threading.Thread(
                target=monitor_pipeline_thread, args=(execution_arn,)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return outputs

    def rerun_pipelines(self, execution_arns: List[str]) -> int:
        threads = []

        def rerun_pipeline(execution_arn: str):
            pipeline_def = load_pipeline_definition(execution_arn)
            run(pipeline_def=pipeline_def)

        for execution_arn in execution_arns:
            thread = threading.Thread(target=rerun_pipeline, args=(execution_arn))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        return 200
