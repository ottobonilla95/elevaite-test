from abc import ABC, abstractmethod
from typing import List


class PipelineProvider(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_pipelines(self, pipeline_configs: List[dict]) -> int:
        """
        Abstract method to create pipelines based on the provided configurations.

        :param pipeline_configs: A list of pipeline configuration objects.
        :return: An integer status code (e.g., 200 for success).
        """
        pass

    @abstractmethod
    def delete_pipelines(self, pipeline_ids: List[str]) -> int:
        """
        Abstract method to delete pipelines based on the provided identifiers.

        :param pipeline_ids: A list of identifiers corresponding to pipelines to be deleted.
                             For instance, these could be image names for SageMaker or DAG IDs for Airflow.
        :return: An integer status code after deletion.
        """
        pass

    @abstractmethod
    def monitor_pipelines(
        self, pipeline_run_ids: List[str], summarize: bool
    ) -> List[str]:
        """
        Abstract method to monitor pipelines based on the provided run identifiers.

        :param pipeline_run_ids: A list of identifiers corresponding to pipeline runs to be monitored.
        :param summarize: A boolean allowing you to choose whether you want summarized logs or not.
        :return: A list of status messages or outputs for each pipeline.
        """
        pass

    @abstractmethod
    def rerun_pipelines(self, pipeline_ids: List[str]) -> int:
        """
        Abstract method to rerun pipelines based on the provided identifiers.

        :param pipeline_ids: A list of identifiers corresponding to pipelines to be rerun.
        :return: An integer status code after processing the rerun.
        """
        pass
