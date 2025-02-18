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
