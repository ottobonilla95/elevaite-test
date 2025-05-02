from typing import Optional, Dict, Any
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes
from opentelemetry.instrumentation.logging import LoggingInstrumentor


def configure_tracer(
    service_name: str = "fastapi-service",
    otlp_endpoint: Optional[str] = None,
    add_console_exporter: bool = True,
    resource_attributes: Optional[Dict[str, Any]] = None,
) -> trace.TracerProvider:
    """
    Configure OpenTelemetry tracer with optional OTLP exporter.

    Args:
        service_name: Name of the service for telemetry data
        otlp_endpoint: Endpoint for OTLP exporter (e.g. 'http://localhost:4317')
        add_console_exporter: Whether to add a console exporter for traces
        resource_attributes: Additional resource attributes to add

    Returns:
        The configured TracerProvider
    """
    # Create resource with service info
    attributes = {
        ResourceAttributes.SERVICE_NAME: service_name,
    }

    # Add any additional attributes
    if resource_attributes:
        attributes.update(resource_attributes)

    resource = Resource.create(attributes)

    # Create and set tracer provider
    provider = TracerProvider(resource=resource)

    # Add console exporter if requested
    if add_console_exporter:
        console_processor = BatchSpanProcessor(ConsoleSpanExporter())
        provider.add_span_processor(console_processor)

    # Add OTLP exporter if endpoint provided
    if otlp_endpoint:
        otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        otlp_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(otlp_processor)

    return provider


# Default tracer provider for when developers don't configure their own
default_tracer_provider = TracerProvider()
trace.set_tracer_provider(default_tracer_provider)
default_tracer = trace.get_tracer(__name__)

default_span_processor = BatchSpanProcessor(ConsoleSpanExporter())
trace.get_tracer_provider().add_span_processor(default_span_processor)  # type: ignore

# Configure logging instrumentation
LoggingInstrumentor().instrument(set_logging_format=True)
