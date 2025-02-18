from abc import ABC, abstractmethod
from typing import List


class PipelineProvider(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def create_pipelines(self, file_paths: List[str]) -> str:
        """
        Abstract method to create pipelines based on the list of file paths.

        :param file_paths: List of file paths to be processed.
        :return: Status message after processing.
        """
        pass

    @abstractmethod
    def delete_pipelines(self, image_names: List[str]) -> str:
        """
        Abstract method to delete pipelines based on the list of file paths.

        :param image_names: List of image names corresponding to pipelines to be deleted.
        :return: Status message after deletion.
        """
        pass

    @abstractmethod
    def monitor_pipelines(self, execution_arns: List[str]) -> List[str]:
        """
        Abstract method to monitor pipelines based on the list of file paths.

        :param execution_arns: List of role names corresponding to pipelines to be monitored.
        :return: List of status messages or outputs for each pipeline.
        """
        pass

    @abstractmethod
    def rerun_pipelines(self, execution_arns: List[str]) -> str:
        """
        Abstract method to rerun pipelines based on the list of file paths.

        :param execution_arns: List of role names corresponding to pipelines to be rerun.
        :return: Status message after processing the rerun.
        """
        pass
