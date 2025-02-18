from .providers.sagemaker import SageMakerPipelineProvider
from .providers.base import PipelineProvider
from .interfaces.pipeline_types import ProviderType
from typing import List, Type


def universal_create_pipelines() -> List[str]:
    return [provider.value for provider in ProviderType]


def create_pipelines_for_provider(provider_type: str, file_paths: List[str]) -> str:
    if provider_type == ProviderType.SAGEMAKER:
        pipeline_provider = SageMakerPipelineProvider()
        result = pipeline_provider.create_pipelines(file_paths)
        return result
    else:
        raise ValueError(f"Unknown provider type: {provider_type}")
