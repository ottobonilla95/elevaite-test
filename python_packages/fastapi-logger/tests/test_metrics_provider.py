import unittest
from unittest import mock

from fastapi_logger.core.telemetry import configure_metrics


class TestMetricsProvider(unittest.TestCase):
    def test_configure_metrics_no_endpoint_returns_provider(self):
        provider = configure_metrics(service_name="svc-no-endpoint")
        # Should return a provider even if no exporter configured
        self.assertIsNotNone(provider)

    def test_configure_metrics_grpc_exporter_valid_params(self):
        # Patch the symbol actually used inside telemetry module
        with mock.patch(
            "fastapi_logger.core.telemetry._GrpcMetricExporter"
        ) as export_cls:
            provider = configure_metrics(
                service_name="svc-grpc",
                otlp_endpoint="localhost:4317",
                otlp_insecure=True,
                otlp_timeout=3,
            )
            self.assertIsNotNone(provider)
            export_cls.assert_called()  # Ensure exporter constructed
            # Validate we passed the right kwargs
            kwargs = export_cls.call_args.kwargs
            self.assertIn("endpoint", kwargs)
            self.assertIn("timeout", kwargs)
            # insecure is valid for gRPC exporter
            self.assertIn("insecure", kwargs)

    def test_configure_metrics_http_exporter_valid_params(self):
        # Patch the HTTP exporter symbol used by telemetry
        with mock.patch(
            "fastapi_logger.core.telemetry._HttpMetricExporter"
        ) as http_export_cls:
            # Simulate using http by providing an http endpoint
            provider = configure_metrics(
                service_name="svc-http",
                otlp_endpoint="http://collector:4318/v1/metrics",
                otlp_timeout=2,
            )
            self.assertIsNotNone(provider)
            http_export_cls.assert_called()
            kwargs = http_export_cls.call_args.kwargs
            # http exporter does not accept 'insecure'; ensure we only passed supported params
            self.assertIn("endpoint", kwargs)
            self.assertIn("timeout", kwargs)
            self.assertNotIn("insecure", kwargs)

    def test_configure_metrics_handles_exporter_failure(self):
        with mock.patch(
            "fastapi_logger.core.telemetry._GrpcMetricExporter",
            side_effect=Exception("boom"),
        ):
            provider = configure_metrics(
                service_name="svc-grpc",
                otlp_endpoint="localhost:4317",
            )
            # Should still return a provider (no readers) on failure
            self.assertIsNotNone(provider)


if __name__ == "__main__":
    unittest.main()
