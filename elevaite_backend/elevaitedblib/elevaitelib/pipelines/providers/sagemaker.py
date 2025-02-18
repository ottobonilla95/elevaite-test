import threading
from typing import List

from .base import PipelineProvider
from ..utils.json2sagemaker import (
    load_pipeline_definition,
    run_pipeline_with_dynamic_dockerfile as run,
)


class SageMakerPipelineProvider(PipelineProvider):
    def __init__(self):
        super().__init__()

    def create_pipelines(self, file_paths: List[str]) -> int:
        """
        Creates pipelines using SageMaker by invoking the 'run' function for each file path.
        Uses threading to process the file paths in parallel.

        :param file_paths: List of file paths to be processed.
        :return: Status message after all threads complete.
        """
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
