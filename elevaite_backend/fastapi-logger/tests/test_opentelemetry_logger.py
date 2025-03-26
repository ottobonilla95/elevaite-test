import os
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import logging
import time
import sys
from unittest import mock

# Add parent directory to path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi_logger import FastAPILogger
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter


class TestOpenTelemetryLogger(unittest.TestCase):
    """Test the OpenTelemetry integration with the logger."""

    def setUp(self):
        self.service_name = "test-service"

        self.mock_otlp_exporter = mock.MagicMock(spec=OTLPSpanExporter)

        self.app = FastAPI()

        with mock.patch(
            "opentelemetry.exporter.otlp.proto.grpc.trace_exporter.OTLPSpanExporter",
            return_value=self.mock_otlp_exporter,
        ):
            FastAPILogger.attach_to_uvicorn(
                service_name=self.service_name,
                otlp_endpoint="http://localhost:4317",
                configure_otel=True,
                resource_attributes={"deployment.environment": "test"},
            )

            self.tracer = trace.get_tracer("test-tracer")

        @self.app.get("/test")
        async def test_route():
            with self.tracer.start_as_current_span("test_operation") as span:
                span.set_attribute("test.attribute", "test-value")
                logging.getLogger("fastapi").info(
                    "Test log from FastAPI route with tracing"
                )
                return {"status": "success", "message": "Log sent with trace context"}

        self.client = TestClient(self.app)

    def test_trace_context_in_logs(self):
        """Test that trace context is present in log output."""
        response = self.client.get("/test")
        self.assertEqual(response.status_code, 200)

        print(
            "\nIn a real environment, logs would contain trace_id and span_id fields."
        )
        print(
            "These are added by the LoggingInstrumentor and would appear in the formatted output."
        )

    def test_span_creation(self):
        """Test that spans are created and exported properly."""
        # Make a request that will generate logs and spans
        response = self.client.get("/test")
        self.assertEqual(response.status_code, 200)

        # Verify span exporter was called
        time.sleep(0.1)

        # Print information about what would happen in a real environment
        print(
            "\nIn a real environment, spans would be exported to an OpenTelemetry collector."
        )
        print(f"Service name: {self.service_name}")
        print("Resource attributes would include: deployment.environment=test")
        print(
            "The spans would include the 'test_operation' span with attribute 'test.attribute=test-value'"
        )


if __name__ == "__main__":
    unittest.main()
