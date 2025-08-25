import importlib
from fastapi import FastAPI


def test_opentelemetry_instrumentation_importable():
    fastapi_inst = importlib.import_module("opentelemetry.instrumentation.fastapi")
    sqlalchemy_inst = importlib.import_module(
        "opentelemetry.instrumentation.sqlalchemy"
    )
    assert fastapi_inst is not None
    assert sqlalchemy_inst is not None


def test_fastapi_instrumentor_does_not_crash():
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

    app = FastAPI()
    FastAPIInstrumentor.instrument_app(app)
    assert True
