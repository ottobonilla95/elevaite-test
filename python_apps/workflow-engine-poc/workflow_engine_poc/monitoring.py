"""
Monitoring and Observability

Provides OpenTelemetry tracing, metrics collection, and structured logging
for production monitoring and debugging of workflow executions.
"""

import time
import logging
import os
from typing import Dict, Any, Optional, List
from contextlib import contextmanager
from dataclasses import dataclass, field


# OpenTelemetry imports with graceful fallback
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource

    # Try to import Jaeger exporter (separate package)
    try:
        from opentelemetry.exporter.jaeger.thrift import JaegerExporter

        JAEGER_AVAILABLE = True
    except ImportError:
        JAEGER_AVAILABLE = False

    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False
    JAEGER_AVAILABLE = False

# Prometheus metrics with graceful fallback
try:
    from prometheus_client import (
        Counter,
        Histogram,
        Gauge,
        CollectorRegistry,
        generate_latest,
    )

    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


logger = logging.getLogger(__name__)


@dataclass
class MetricData:
    """Container for metric data"""

    name: str
    value: float
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)


@dataclass
class TraceData:
    """Container for trace data"""

    trace_id: str
    span_id: str
    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "ok"
    tags: Dict[str, Any] = field(default_factory=dict)


class WorkflowMonitoring:
    """
    Comprehensive monitoring and observability for workflow engine.

    Provides OpenTelemetry tracing, Prometheus metrics, and structured logging.
    """

    def __init__(self, service_name: str = "workflow-engine"):
        self.service_name = service_name
        self.enabled = True

        # Initialize components
        self._init_tracing()
        self._init_metrics()
        self._init_logging()

        # Storage for fallback mode
        self.traces: List[TraceData] = []
        self.metrics_data: List[MetricData] = []

    def _init_tracing(self):
        """Initialize OpenTelemetry tracing"""
        if not OPENTELEMETRY_AVAILABLE:
            logger.warning("OpenTelemetry not available, using fallback tracing")
            self.tracer = None
            return

        try:
            # Configure resource
            resource = Resource.create(
                {
                    "service.name": self.service_name,
                    "service.version": "1.0.0",
                    "deployment.environment": os.getenv("ENVIRONMENT", "development"),
                }
            )

            # Set up tracer provider
            tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(tracer_provider)

            # Configure Jaeger exporter if endpoint is available
            jaeger_endpoint = os.getenv("JAEGER_ENDPOINT")
            if jaeger_endpoint and JAEGER_AVAILABLE:
                try:
                    jaeger_exporter = JaegerExporter(
                        agent_host_name=jaeger_endpoint.split("://")[1].split(":")[0],
                        agent_port=(
                            int(jaeger_endpoint.split(":")[-1])
                            if ":" in jaeger_endpoint
                            else 14268
                        ),
                    )
                    span_processor = BatchSpanProcessor(jaeger_exporter)
                    tracer_provider.add_span_processor(span_processor)
                    logger.info(f"Jaeger exporter configured for {jaeger_endpoint}")
                except Exception as e:
                    logger.warning(f"Failed to configure Jaeger exporter: {e}")
            else:
                # Fallback to console exporter for development
                console_exporter = ConsoleSpanExporter()
                span_processor = BatchSpanProcessor(console_exporter)
                tracer_provider.add_span_processor(span_processor)
                logger.info("Console span exporter configured")

            self.tracer = trace.get_tracer(self.service_name)
            logger.info("OpenTelemetry tracing initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize OpenTelemetry tracing: {e}")
            self.tracer = None

    def _init_metrics(self):
        """Initialize Prometheus metrics"""
        if not PROMETHEUS_AVAILABLE:
            logger.warning("Prometheus client not available, using fallback metrics")
            self.registry = None
            return

        try:
            # Create custom registry
            self.registry = CollectorRegistry()

            # Workflow execution metrics
            self.workflow_executions_total = Counter(
                "workflow_executions_total",
                "Total number of workflow executions",
                ["workflow_id", "status"],
                registry=self.registry,
            )

            self.workflow_execution_duration = Histogram(
                "workflow_execution_duration_seconds",
                "Workflow execution duration in seconds",
                ["workflow_id"],
                registry=self.registry,
            )

            # Step execution metrics
            self.step_executions_total = Counter(
                "step_executions_total",
                "Total number of step executions",
                ["step_type", "status"],
                registry=self.registry,
            )

            self.step_execution_duration = Histogram(
                "step_execution_duration_seconds",
                "Step execution duration in seconds",
                ["step_type"],
                registry=self.registry,
            )

            # Error metrics
            self.errors_total = Counter(
                "errors_total",
                "Total number of errors",
                ["component", "error_type"],
                registry=self.registry,
            )

            # Active executions gauge
            self.active_executions = Gauge(
                "active_executions",
                "Number of currently active workflow executions",
                registry=self.registry,
            )

            logger.info("Prometheus metrics initialized")

        except Exception as e:
            logger.warning(f"Failed to initialize Prometheus metrics: {e}")
            self.registry = None

    def _init_logging(self):
        """Initialize structured logging"""
        # Configure structured logging format
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - "
            "[%(trace_id)s] [%(span_id)s] - %(message)s",
            defaults={"trace_id": "N/A", "span_id": "N/A"},
        )

        # Apply to workflow engine loggers
        for logger_name in ["workflow_engine_poc", "workflow_engine", "step_registry"]:
            log = logging.getLogger(logger_name)
            if log.handlers:
                for handler in log.handlers:
                    handler.setFormatter(formatter)

    @contextmanager
    def trace_workflow_execution(self, workflow_id: str, execution_id: str):
        """Context manager for tracing workflow execution"""
        start_time = time.time()
        trace_data = None

        if self.tracer:
            with self.tracer.start_as_current_span(
                "workflow_execution",
                attributes={
                    "workflow.id": workflow_id,
                    "execution.id": execution_id,
                    "component": "workflow_engine",
                },
            ) as span:
                try:
                    yield span
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    if self.registry:
                        self.workflow_executions_total.labels(
                            workflow_id=workflow_id, status="completed"
                        ).inc()
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    if self.registry:
                        self.workflow_executions_total.labels(
                            workflow_id=workflow_id, status="failed"
                        ).inc()
                    raise
                finally:
                    duration = time.time() - start_time
                    if self.registry:
                        self.workflow_execution_duration.labels(
                            workflow_id=workflow_id
                        ).observe(duration)
        else:
            # Fallback tracing
            trace_data = TraceData(
                trace_id=execution_id,
                span_id=f"workflow-{execution_id[:8]}",
                operation_name="workflow_execution",
                start_time=start_time,
                tags={"workflow.id": workflow_id, "execution.id": execution_id},
            )

            try:
                yield trace_data
                trace_data.status = "ok"
                self._record_metric(
                    "workflow_executions_total",
                    1,
                    {"workflow_id": workflow_id, "status": "completed"},
                )
            except Exception as e:
                trace_data.status = "error"
                trace_data.tags["error"] = str(e)
                self._record_metric(
                    "workflow_executions_total",
                    1,
                    {"workflow_id": workflow_id, "status": "failed"},
                )
                raise
            finally:
                trace_data.end_time = time.time()
                trace_data.duration_ms = (
                    trace_data.end_time - trace_data.start_time
                ) * 1000
                self.traces.append(trace_data)

                duration = trace_data.end_time - trace_data.start_time
                self._record_metric(
                    "workflow_execution_duration_seconds",
                    duration,
                    {"workflow_id": workflow_id},
                )

    @contextmanager
    def trace_step_execution(self, step_id: str, step_type: str, execution_id: str):
        """Context manager for tracing step execution"""
        start_time = time.time()

        if self.tracer:
            with self.tracer.start_as_current_span(
                "step_execution",
                attributes={
                    "step.id": step_id,
                    "step.type": step_type,
                    "execution.id": execution_id,
                    "component": "step_registry",
                },
            ) as span:
                try:
                    yield span
                    span.set_status(trace.Status(trace.StatusCode.OK))
                    if self.registry:
                        self.step_executions_total.labels(
                            step_type=step_type, status="completed"
                        ).inc()
                except Exception as e:
                    span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                    span.record_exception(e)
                    if self.registry:
                        self.step_executions_total.labels(
                            step_type=step_type, status="failed"
                        ).inc()
                    raise
                finally:
                    duration = time.time() - start_time
                    if self.registry:
                        self.step_execution_duration.labels(
                            step_type=step_type
                        ).observe(duration)
        else:
            # Fallback tracing
            trace_data = TraceData(
                trace_id=execution_id,
                span_id=f"step-{step_id[:8]}",
                operation_name="step_execution",
                start_time=start_time,
                tags={"step.id": step_id, "step.type": step_type},
            )

            try:
                yield trace_data
                trace_data.status = "ok"
                self._record_metric(
                    "step_executions_total",
                    1,
                    {"step_type": step_type, "status": "completed"},
                )
            except Exception as e:
                trace_data.status = "error"
                trace_data.tags["error"] = str(e)
                self._record_metric(
                    "step_executions_total",
                    1,
                    {"step_type": step_type, "status": "failed"},
                )
                raise
            finally:
                trace_data.end_time = time.time()
                trace_data.duration_ms = (
                    trace_data.end_time - trace_data.start_time
                ) * 1000
                self.traces.append(trace_data)

                duration = trace_data.end_time - trace_data.start_time
                self._record_metric(
                    "step_execution_duration_seconds",
                    duration,
                    {"step_type": step_type},
                )

    def record_error(self, component: str, error_type: str, error_message: str):
        """Record an error for monitoring"""
        if self.registry:
            self.errors_total.labels(component=component, error_type=error_type).inc()
        else:
            self._record_metric(
                "errors_total", 1, {"component": component, "error_type": error_type}
            )

        logger.error(f"Error in {component}: {error_type} - {error_message}")

    def update_active_executions(self, count: int):
        """Update the count of active executions"""
        if self.registry:
            self.active_executions.set(count)
        else:
            self._record_metric("active_executions", count, {})

    def _record_metric(self, name: str, value: float, labels: Dict[str, str]):
        """Record metric in fallback mode"""
        metric = MetricData(name=name, value=value, labels=labels)
        self.metrics_data.append(metric)

    def get_metrics(self) -> str:
        """Get Prometheus metrics in text format"""
        if self.registry:
            return generate_latest(self.registry).decode("utf-8")
        else:
            # Return fallback metrics
            lines = []
            for metric in self.metrics_data:
                labels_str = ",".join(f'{k}="{v}"' for k, v in metric.labels.items())
                if labels_str:
                    lines.append(f"{metric.name}{{{labels_str}}} {metric.value}")
                else:
                    lines.append(f"{metric.name} {metric.value}")
            return "\n".join(lines)

    def get_traces(self) -> List[Dict[str, Any]]:
        """Get trace data for debugging"""
        return [
            {
                "trace_id": trace.trace_id,
                "span_id": trace.span_id,
                "operation_name": trace.operation_name,
                "start_time": trace.start_time,
                "end_time": trace.end_time,
                "duration_ms": trace.duration_ms,
                "status": trace.status,
                "tags": trace.tags,
            }
            for trace in self.traces
        ]

    def get_monitoring_summary(self) -> Dict[str, Any]:
        """Get monitoring summary for health checks"""
        return {
            "monitoring_enabled": self.enabled,
            "opentelemetry_available": OPENTELEMETRY_AVAILABLE,
            "prometheus_available": PROMETHEUS_AVAILABLE,
            "traces_collected": len(self.traces),
            "metrics_collected": len(self.metrics_data),
            "service_name": self.service_name,
        }


# Global monitoring instance
monitoring = WorkflowMonitoring()
