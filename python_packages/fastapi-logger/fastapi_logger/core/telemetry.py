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
    otlp_insecure: bool = False,
    otlp_timeout: int = 5,
) -> trace.TracerProvider:
    """
    Configure OpenTelemetry tracer with optional OTLP exporter.

    Args:
        service_name: Name of the service for telemetry data
        otlp_endpoint: Endpoint for OTLP exporter (e.g. 'http://localhost:4317')
        add_console_exporter: Whether to add a console exporter for traces
        resource_attributes: Additional resource attributes to add
        otlp_insecure: Whether to use insecure connection for OTLP (default: False for security)
        otlp_timeout: Timeout in seconds for OTLP exporter (default: 5)

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
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
                timeout=otlp_timeout,
                insecure=otlp_insecure,
            )
            otlp_processor = BatchSpanProcessor(
                otlp_exporter,
                export_timeout_millis=otlp_timeout * 1000,  # Convert to milliseconds
                schedule_delay_millis=1000,  # Export every 1 second
            )
            provider.add_span_processor(otlp_processor)
            security_mode = "insecure" if otlp_insecure else "secure"
            print(
                f"✅ OTLP exporter configured for {otlp_endpoint} ({security_mode}, timeout={otlp_timeout}s)"
            )
        except Exception as e:
            print(f"⚠️  Failed to configure OTLP exporter: {e}")
            print("   Continuing with console exporter only")

    return provider


# Default tracer provider for when developers don't configure their own
# Use a minimal configuration to avoid interfering with the application
default_tracer_provider = TracerProvider()
default_tracer = trace.get_tracer(__name__)

# Only set up OpenTelemetry if explicitly requested
# Don't automatically instrument logging or set up exporters
