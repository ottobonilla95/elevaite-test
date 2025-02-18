from .providers.sagemaker import SageMakerPipelineProvider
from .interfaces.pipeline_types import ProviderType
from typing import List, Dict, Any


def universal_create_pipelines() -> List[str]:
    providers = [provider.value for provider in ProviderType]
    return providers


def create_pipelines_for_provider(
    provider_type: str, file_paths: List[str]
) -> Dict[str, Any]:
    try:
        if provider_type != ProviderType.SAGEMAKER:
            return {
                "code": 400,
                "message": f"Unknown provider type: {provider_type}. Only '{ProviderType.SAGEMAKER}' is supported.",
            }

        pipeline_provider = SageMakerPipelineProvider()
        result_code = pipeline_provider.create_pipelines(file_paths)

        if result_code == 200:
            return {"code": 200, "message": "Pipelines created successfully."}
        else:
            return {
                "code": result_code,
                "message": "Pipeline creation failed. Please check your file paths and configuration.",
            }

    except Exception as error:
        return {
            "code": 500,
            "message": f"An error occurred while creating pipelines: {str(error)}",
        }


def delete_pipelines_for_provider(
    provider_type: str, image_names: List[str]
) -> Dict[str, Any]:
    try:
        if provider_type != ProviderType.SAGEMAKER:
            return {
                "code": 400,
                "message": f"Unknown provider type: {provider_type}. Only '{ProviderType.SAGEMAKER}' is supported.",
            }

        pipeline_provider = SageMakerPipelineProvider()
        result_code = pipeline_provider.delete_pipelines(image_names)

        if result_code == 200:
            return {"code": 200, "message": "Pipelines deleted successfully."}
        else:
            return {
                "code": result_code,
                "message": "Pipeline deletion failed. Please verify the image names or deletion criteria.",
            }

    except Exception as error:
        return {
            "code": 500,
            "message": f"An error occurred while deleting pipelines: {str(error)}",
        }


def monitor_pipelines_for_provider(
    provider_type: str, execution_arns: List[str]
) -> Dict[str, Any]:
    try:
        if provider_type != ProviderType.SAGEMAKER:
            return {
                "code": 400,
                "message": f"Unknown provider type: {provider_type}. Only '{ProviderType.SAGEMAKER}' is supported.",
            }

        pipeline_provider = SageMakerPipelineProvider()
        outputs = pipeline_provider.monitor_pipelines(execution_arns)

        return {
            "code": 200,
            "message": "Pipelines monitored successfully.",
            "outputs": outputs,
        }

    except Exception as error:
        return {
            "code": 500,
            "message": f"An error occurred while monitoring pipelines: {str(error)}",
        }


def rerun_pipelines_for_provider(
    provider_type: str, execution_arns: List[str]
) -> Dict[str, Any]:
    try:
        if provider_type != ProviderType.SAGEMAKER:
            return {
                "code": 400,
                "message": f"Unknown provider type: {provider_type}. Only '{ProviderType.SAGEMAKER}' is supported.",
            }

        pipeline_provider = SageMakerPipelineProvider()
        result_code = pipeline_provider.rerun_pipelines(execution_arns)

        if result_code == 200:
            return {"code": 200, "message": "Pipelines rerun successfully."}
        else:
            return {
                "code": result_code,
                "message": "Pipeline rerun failed. Please verify the execution ARNs and try again.",
            }

    except Exception as error:
        return {
            "code": 500,
            "message": f"An error occurred while rerunning pipelines: {str(error)}",
        }
