import sys
import logging
import io
from unittest import TestCase, mock

sys.path.insert(0, "..")

from fastapi_logger import BaseLogger


class TestBaseLogger(TestCase):
    def setUp(self):
        self.log_output = io.StringIO()
        self.logger = BaseLogger(stream=self.log_output, name="test-base-logger")

    def test_logger_initialization(self):
        logger_instance = self.logger.get_logger()
        self.assertIsInstance(logger_instance, logging.Logger)
        self.assertEqual(logger_instance.name, "test-base-logger")
        self.assertEqual(logger_instance.level, logging.DEBUG)

    def test_basic_logging(self):
        output = io.StringIO()
        test_logger = BaseLogger(name="test-logger", stream=output)
        logger_instance = test_logger.get_logger()
        logger_instance.info("Test basic message")

        log_content = output.getvalue()
        self.assertIn("Test basic message", log_content)
        self.assertIn("[elevAIte Logger]", log_content)
        self.assertIn("INFO", log_content)

    @mock.patch("boto3.client")
    def test_cloudwatch_validation(self, mock_boto3):
        with self.assertRaises(ValueError):
            BaseLogger(
                cloudwatch_enabled=True, log_group=None, log_stream="test-stream"
            )

        with self.assertRaises(ValueError):
            BaseLogger(cloudwatch_enabled=True, log_group="test-group", log_stream=None)

        with mock.patch("boto3.client"):
            logger = BaseLogger(
                cloudwatch_enabled=True,
                log_group="test-group",
                log_stream="test-stream",
            )
        self.assertTrue(logger.cloudwatch_enabled)
        self.assertEqual(logger.log_group, "test-group")
        self.assertEqual(logger.log_stream, "test-stream")

    @mock.patch("logging.getLogger")
    def test_attach_to_uvicorn(self, mock_get_logger):
        mock_uvicorn_logger = mock.MagicMock()
        mock_fastapi_logger = mock.MagicMock()

        def get_logger_side_effect(name):
            if name == "uvicorn" or name == "uvicorn.access" or name == "uvicorn.error":
                return mock_uvicorn_logger
            elif name == "fastapi":
                return mock_fastapi_logger
            else:
                return mock.MagicMock()

        mock_get_logger.side_effect = get_logger_side_effect

        BaseLogger.attach_to_uvicorn()

        self.assertGreaterEqual(mock_get_logger.call_count, 4)
        mock_uvicorn_logger.setLevel.assert_called_with(logging.DEBUG)
        mock_fastapi_logger.setLevel.assert_called_with(logging.DEBUG)
