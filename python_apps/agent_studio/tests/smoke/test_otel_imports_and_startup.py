import importlib


def test_opentelemetry_instrumentation_importable():
    fastapi_inst = importlib.import_module("opentelemetry.instrumentation.fastapi")
    sqlalchemy_inst = importlib.import_module(
        "opentelemetry.instrumentation.sqlalchemy"
    )
    assert fastapi_inst is not None
    assert sqlalchemy_inst is not None


def test_elevaite_logger_attach_no_crash(monkeypatch):
    # Do not actually export in tests
    monkeypatch.setenv("OTLP_ENDPOINT", "")
    from fastapi_logger import ElevaiteLogger

    ElevaiteLogger.attach_to_uvicorn(service_name="agent-studio", configure_otel=True)
    assert True
