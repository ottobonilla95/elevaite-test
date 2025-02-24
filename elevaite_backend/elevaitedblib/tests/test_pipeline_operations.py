import pytest
from ..elevaitelib.pipelines.service import (
    create_pipelines_for_provider,
    delete_pipelines_for_provider,
    monitor_pipelines_for_provider,
    rerun_pipelines_for_provider,
    ProviderType,
)


@pytest.mark.parametrize("provider_type", [provider.value for provider in ProviderType])
def test_create_pipelines(provider_type, pipeline_files):
    result = create_pipelines_for_provider(provider_type, pipeline_files)

    assert isinstance(result, dict)
    assert "code" in result
    assert "message" in result
    assert result["code"] == 200
    assert result["message"] == "Pipelines created successfully."


@pytest.mark.parametrize("provider_type", [provider.value for provider in ProviderType])
def test_delete_pipelines(provider_type):
    pipeline_ids = ["pipeline-1", "pipeline-2"]  # TODO: Replace with real IDs

    result = delete_pipelines_for_provider(provider_type, pipeline_ids)

    assert isinstance(result, dict)
    assert "code" in result
    assert "message" in result
    assert result["code"] == 200
    assert result["message"] == "Pipelines deleted successfully."


@pytest.mark.parametrize("provider_type", [provider.value for provider in ProviderType])
def test_monitor_pipelines(provider_type):
    execution_ids = ["exec-1", "exec-2"]  # TODO: Replace with real IDs

    result = monitor_pipelines_for_provider(provider_type, execution_ids)

    assert isinstance(result, dict)
    assert "code" in result
    assert "message" in result
    assert "outputs" in result
    assert result["code"] == 200
    assert result["message"] == "Pipelines monitored successfully."
    assert isinstance(result["outputs"], dict)


@pytest.mark.parametrize("provider_type", [provider.value for provider in ProviderType])
def test_rerun_pipelines(provider_type):
    execution_ids = ["exec-1", "exec-2"]  # TODO: Replace with real IDs

    result = rerun_pipelines_for_provider(provider_type, execution_ids)

    assert isinstance(result, dict)
    assert "code" in result
    assert "message" in result
    assert result["code"] == 200
    assert result["message"] == "Pipelines rerun successfully."


@pytest.mark.parametrize(
    "operation,args",
    [
        (create_pipelines_for_provider, (["test_file.json"],)),
        (delete_pipelines_for_provider, (["pipeline-1"],)),
        (monitor_pipelines_for_provider, (["exec-1"],)),
        (rerun_pipelines_for_provider, (["exec-1"],)),
    ],
)
def test_invalid_provider_type(operation, args):
    result = operation("INVALID_PROVIDER", *args)

    assert isinstance(result, dict)
    assert "code" in result
    assert "message" in result
    assert result["code"] == 400
    assert "Unknown provider type" in result["message"]


@pytest.mark.parametrize(
    "operation,args",
    [
        (create_pipelines_for_provider, (["nonexistent.json"],)),
        (delete_pipelines_for_provider, (["nonexistent-pipeline"],)),
        (monitor_pipelines_for_provider, (["nonexistent-execution"],)),
        (rerun_pipelines_for_provider, (["nonexistent-execution"],)),
    ],
)
@pytest.mark.parametrize("provider_type", [provider.value for provider in ProviderType])
def test_error_handling(operation, args, provider_type):
    result = operation(provider_type, *args)

    assert isinstance(result, dict)
    assert "code" in result
    assert "message" in result
    assert result["code"] in [500] or result["code"] >= 400
