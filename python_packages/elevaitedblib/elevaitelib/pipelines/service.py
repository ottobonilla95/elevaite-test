from .providers.sagemaker import SageMakerPipelineProvider

# from .providers.airflow import AirflowPipelineProvider
from .interfaces.pipeline_types import ProviderType
from typing import List, Dict, Any


def UnsupportedProviderResult(provider_type):
    return {
        "code": 400,
        "message": f"Unknown provider type: {provider_type}. Supported providers are: {ProviderType.SAGEMAKER} and {ProviderType.AIRFLOW}.",
    }


def get_available_providers() -> List[str]:
    providers = [provider.value for provider in ProviderType]
    return providers


def create_pipelines_for_provider(
    provider_type: str, file_paths: List[dict]
) -> Dict[str, Any]:
    try:
        match provider_type:
            case ProviderType.SAGEMAKER:
                pipeline_provider = SageMakerPipelineProvider()
            case ProviderType.AIRFLOW:
                # pipeline_provider = AirflowPipelineProvider()
                return UnsupportedProviderResult(provider_type)
            case _:
                return UnsupportedProviderResult(provider_type)

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
    provider_type: str, pipeline_ids: List[str]
) -> Dict[str, Any]:
    try:
        match provider_type:
            case ProviderType.SAGEMAKER:
                pipeline_provider = SageMakerPipelineProvider()
            case ProviderType.AIRFLOW:
                # pipeline_provider = AirflowPipelineProvider()
                return UnsupportedProviderResult(provider_type)
            case _:
                return UnsupportedProviderResult(provider_type)

        result_code = pipeline_provider.delete_pipelines(pipeline_ids)

        if result_code == 200:
            return {"code": 200, "message": "Pipelines deleted successfully."}
        else:
            return {
                "code": result_code,
                "message": "Pipeline deletion failed. Please verify the pipeline identifiers.",
            }

    except Exception as error:
        return {
            "code": 500,
            "message": f"An error occurred while deleting pipelines: {str(error)}",
        }


def monitor_pipelines_for_provider(
    provider_type: str, execution_ids: List[str]
) -> Dict[str, Any]:
    try:
        match provider_type:
            case ProviderType.SAGEMAKER:
                pipeline_provider = SageMakerPipelineProvider()
            case ProviderType.AIRFLOW:
                # pipeline_provider = AirflowPipelineProvider()
                return UnsupportedProviderResult(provider_type)
            case _:
                return UnsupportedProviderResult(provider_type)

        outputs = pipeline_provider.monitor_pipelines(execution_ids)

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
    provider_type: str, execution_ids: List[str]
) -> Dict[str, Any]:
    try:
        match provider_type:
            case ProviderType.SAGEMAKER:
                pipeline_provider = SageMakerPipelineProvider()
            case ProviderType.AIRFLOW:
                # pipeline_provider = AirflowPipelineProvider()
                return UnsupportedProviderResult(provider_type)
            case _:
                return UnsupportedProviderResult(provider_type)

        result_code = pipeline_provider.rerun_pipelines(execution_ids)

        if result_code == 200:
            return {"code": 200, "message": "Pipelines rerun successfully."}
        else:
            return {
                "code": result_code,
                "message": "Pipeline rerun failed. Please verify the execution identifiers and try again.",
            }

    except Exception as error:
        return {
            "code": 500,
            "message": f"An error occurred while rerunning pipelines: {str(error)}",
        }
