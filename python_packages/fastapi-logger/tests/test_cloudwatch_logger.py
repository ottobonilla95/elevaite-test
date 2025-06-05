import os
import unittest
from fastapi import FastAPI
from fastapi.testclient import TestClient
import logging
import time
import sys

# Add parent directory to path so we can import the package
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi_logger import ElevaiteLogger


class TestCloudWatchLogger(unittest.TestCase):
    """Test the CloudWatch Logger integration."""

    def setUp(self):
        # AWS CloudWatch configuration
        self.log_group = os.environ.get(
            "AWS_LOG_GROUP", "elevaite-fastapi-logger-test-logs"
        )
        self.log_stream = os.environ.get("AWS_LOG_STREAM", "test")

        # Create our FastAPI app
        self.app = FastAPI()

        # Configure the logger with CloudWatch enabled
        ElevaiteLogger.attach_to_uvicorn(
            cloudwatch_enabled=True,
            log_group=self.log_group,
            log_stream=self.log_stream,
            filter_fastapi=True,  # Filter out standard FastAPI logs
        )

        # Set up a test route that generates logs
        @self.app.get("/test")
        async def test_route():
            logging.getLogger("fastapi").info("Test log from FastAPI route")
            return {"status": "success", "message": "Log sent to CloudWatch"}

        # Create a test client
        self.client = TestClient(self.app)

    def test_cloudwatch_logging(self):
        """Test that logs are sent to CloudWatch."""
        # Generate a unique identifier for this test run
        test_id = f"test-{int(time.time())}"

        # Make a request that will generate logs
        response = self.client.get("/test")
        self.assertEqual(response.status_code, 200)

        # Log a message with our test ID
        logger = logging.getLogger("fastapi")
        logger.info(f"CloudWatch test message with ID: {test_id}")

        # Since CloudWatch logs are asynchronous, we'll just print the information
        # needed to manually verify the logs
        print(f"\nTest ID: {test_id}")
        print(f"Log Group: {self.log_group}")
        print(f"Log Stream: {self.log_stream}")
        print("\nTo view these logs, visit:")
        print(
            f"https://console.aws.amazon.com/cloudwatch/home?region={os.environ.get('AWS_REGION', 'us-east-1')}#logsV2:log-groups/log-group/{self.log_group}/log-events/{self.log_stream}"
        )
        print("\nYou should see log entries including the test ID above.")
        print("Note: It may take a few seconds for logs to appear in CloudWatch.")

        # Sleep briefly to allow logs to be sent
        time.sleep(2)


if __name__ == "__main__":
    # Ensure AWS credentials are properly configured before running this test
    if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get(
        "AWS_SECRET_ACCESS_KEY"
    ):
        print("WARNING: AWS credentials not found in environment variables.")
        print(
            "Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_REGION to run this test."
        )
        sys.exit(1)

    unittest.main()
