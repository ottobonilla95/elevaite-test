from typing import Optional, Dict, Any
import sys
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource

# Resolve service.name key across semconv versions
try:
    from opentelemetry.semconv.attributes.resource import SERVICE_NAME as SERVICE_NAME_KEY
except Exception:
    try:
        from opentelemetry.semconv.resource import ResourceAttributes as _ResAttrs  # type: ignore

        SERVICE_NAME_KEY = getattr(_ResAttrs, "SERVICE_NAME", "service.name")
    except Exception:
        SERVICE_NAME_KEY = "service.name"
from opentelemetry.metrics import set_meter_provider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader

# Import both exporters under different names to avoid shadowing
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
    OTLPMetricExporter as _GrpcMetricExporter,
)
from opentelemetry.exporter.otlp.proto.http.metric_exporter import (
    OTLPMetricExporter as _HttpMetricExporter,
)


def configure_tracer(
    service_name: str = "fastapi-service",
    otlp_endpoint: Optional[str] = None,
    add_console_exporter: bool = False,
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
        SERVICE_NAME_KEY: service_name,
    }

    # Add any additional attributes
    if resource_attributes:
        attributes.update(resource_attributes)

    resource = Resource.create(attributes)

    # Create and set tracer provider
    provider = TracerProvider(resource=resource)

    # Add console exporter only if explicitly requested (or OTEL_CONSOLE_EXPORT=1)
    import os as _os

    if add_console_exporter or _os.getenv("OTEL_CONSOLE_EXPORT") == "1":
        try:

            class _SafeStream:
                def __init__(self, wrapped):
                    self._wrapped = wrapped

                def write(self, *a, **k):
                    try:
                        if self._wrapped and not getattr(self._wrapped, "closed", False):
                            return self._wrapped.write(*a, **k)
                    except Exception:
                        return None

                def flush(self):
                    try:
                        if self._wrapped and not getattr(self._wrapped, "closed", False):
                            return self._wrapped.flush()
                    except Exception:
                        return None

            exporter = ConsoleSpanExporter(out=_SafeStream(sys.stdout))
            console_processor = BatchSpanProcessor(exporter)
            provider.add_span_processor(console_processor)
        except Exception:
            # Proceed without console exporter
            pass

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
            print(f"✅ OTLP exporter configured for {otlp_endpoint} ({security_mode}, timeout={otlp_timeout}s)")
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

# Simple guard to avoid re-setting MeterProvider multiple times in one process
_metrics_provider_initialized = False


def configure_metrics(
    service_name: str = "fastapi-service",
    otlp_endpoint: Optional[str] = None,
    resource_attributes: Optional[Dict[str, Any]] = None,
    otlp_insecure: bool = False,
    otlp_timeout: int = 5,
) -> Optional[MeterProvider]:
    """Configure OpenTelemetry metrics with optional OTLP exporter.

    Returns the configured MeterProvider or None if exporter unavailable or not configured.
    """
    global _metrics_provider_initialized
    try:
        # We will not override the global provider if already set; still return a provider instance

        attributes = {SERVICE_NAME_KEY: service_name}
        if resource_attributes:
            attributes.update(resource_attributes)
        resource = Resource.create(attributes)

        readers = []
        if otlp_endpoint:
            # Choose exporter based on path: HTTP exporter uses /v1/metrics path, gRPC usually plain host:port
            try:
                endpoint_str = str(otlp_endpoint)
                if "/v1/metrics" in endpoint_str:
                    # HTTP exporter does not accept 'insecure'
                    exporter = _HttpMetricExporter(endpoint=otlp_endpoint, timeout=otlp_timeout)
                else:
                    # gRPC exporter typically at host:port or http://host:4317; supports 'insecure'
                    exporter = _GrpcMetricExporter(
                        endpoint=otlp_endpoint,
                        timeout=otlp_timeout,
                        insecure=otlp_insecure,
                    )
                reader = PeriodicExportingMetricReader(exporter)
                readers.append(reader)
            except Exception as exp:
                # Exporter failed to init; continue with provider without readers
                print(f"⚠️  OTEL metrics exporter init failed: {exp}")
        # No endpoint -> allow provider with no readers

        provider = MeterProvider(resource=resource, metric_readers=readers)
        try:
            if not _metrics_provider_initialized:
                set_meter_provider(provider)
                _metrics_provider_initialized = True
        except Exception:
            # Overriding existing MeterProvider is not allowed; proceed without setting global
            pass

        return provider
    except Exception as e:
        print(f"⚠️  Failed to configure OTEL metrics: {e}")
        return None
