from enum import Enum


class ProviderType(str, Enum):
    """Enum representing available pipeline providers."""

    AIRFLOW = "airflow"
    BEDROCK = "bedrock"
    SAGEMAKER = "sagemaker"
    FLYTE = "flyte"
