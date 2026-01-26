import re
import time
import logging
from typing import Optional, Any

from opentelemetry import trace


class CloudWatchHandler:
    """Handles sending logs to AWS CloudWatch."""

    def __init__(
        self,
        cloudwatch_client: Any,
        log_group: str,
        log_stream: str,
        filter_fastapi: bool = False,
        tracer: Optional[trace.Tracer] = None,
    ):
        """
        Initialize CloudWatch handler.

        Args:
            cloudwatch_client: Boto3 CloudWatch client
            log_group: CloudWatch log group name
            log_stream: CloudWatch log stream name
            filter_fastapi: Whether to filter out standard FastAPI logs
            tracer: OpenTelemetry tracer for span creation
        """
        self.cloudwatch_client = cloudwatch_client
        self.log_group = log_group
        self.log_stream = log_stream
        self.filter_fastapi = filter_fastapi
        self.tracer = tracer or trace.get_tracer(__name__)

    def setup_handler(self, handler: logging.Handler) -> None:
        """Set up the CloudWatch handler by extending the existing handler."""
        original_emit = handler.emit

        def new_emit(record):
            # Call the original emit function first
            original_emit(record)

            formatter = handler.formatter
            if formatter:
                # Extract the log message
                log_message = formatter.format(record)

                # Process the log message
                processed_log = self._process_log(log_message)

                # Only send to CloudWatch if the log wasn't filtered out
                if processed_log is not None:
                    # Wrap the CloudWatch send in a span to capture trace details
                    with self.tracer.start_as_current_span("cloudwatch_log_send"):
                        self._send_log_to_cloudwatch(processed_log)

        # Replace the emit function
        handler.emit = new_emit

    def _process_log(self, log: str) -> Optional[str]:
        """
        Processes a log string by:
          1. Removing the bracketed prefix.
          2. Optionally filtering out regular FastAPI logs (if filter_fastapi is True).

        Args:
            log (str): The log string to process.

        Returns:
            Optional[str]: The cleaned log string, or None if it was filtered out.
        """
        # Remove leading square-bracketed prefix
        cleaned = re.sub(r"^\[[^\]]*\]\s*", "", log)

        if self.filter_fastapi:
            # Check for standard HTTP methods at the start of the cleaned log message
            if re.match(r"^(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s", cleaned):
                # If it's a typical FastAPI log message, return None to indicate it's ignored
                return None

        return cleaned

    def _send_log_to_cloudwatch(self, log: str) -> None:
        """
        Sends a given log string to AWS CloudWatch Logs.

        Args:
            log (str): The log message to send.
        """
        try:
            # Retrieve the upload sequence token for the log stream
            response = self.cloudwatch_client.describe_log_streams(
                logGroupName=self.log_group, logStreamNamePrefix=self.log_stream
            )
            if response["logStreams"]:
                sequence_token = response["logStreams"][0].get("uploadSequenceToken")
            else:
                return
        except Exception:
            return

        # Create a log event with the current timestamp (in milliseconds)
        timestamp = int(time.time() * 1000)
        log_event = {"timestamp": timestamp, "message": log}

        # Prepare the parameters for sending the log event
        params = {
            "logGroupName": self.log_group,
            "logStreamName": self.log_stream,
            "logEvents": [log_event],
        }
        if sequence_token:
            params["sequenceToken"] = sequence_token

        # Send the log event to CloudWatch
        try:
            self.cloudwatch_client.put_log_events(**params)
        except Exception:
            pass  # Already logging errors would cause recursion
