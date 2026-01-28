import sys
import io
import unittest
from unittest import mock

sys.path.insert(0, "..")

from tests.test_files import sample_decorated
from fastapi_logger import ElevaiteLogger


class TestDecoratorIntegration(unittest.TestCase):
    def setUp(self):
        self.log_output = io.StringIO()
        self.mock_logger = ElevaiteLogger(
            name="test-integration", stream=self.log_output
        )

        self.patcher = mock.patch(
            "tests.test_files.sample_decorated.elevaite_logger", self.mock_logger
        )
        self.patcher.start()
        self.patcher2 = mock.patch(
            "tests.test_files.sample_decorated.logger", self.mock_logger.get_logger()
        )
        self.patcher2.start()

    def tearDown(self):
        self.patcher.stop()
        self.patcher2.stop()

    def test_add_function_decorator(self):
        result = sample_decorated.add_numbers(10, 20)
        log_content = self.log_output.getvalue()

        self.assertEqual(result, 30)
        self.assertIn("Function add_numbers called with", log_content)
        self.assertIn("Function add_numbers returned: 30", log_content)

    def test_process_user_with_watch(self):
        result = sample_decorated.process_user("Bob", 25)
        log_content = self.log_output.getvalue()

        self.assertEqual(result, "Bob is 25 years old")
        self.assertIn("Function process_user called with", log_content)
        self.assertIn("Processing user Bob with age 25", log_content)
        self.assertIn("Function process_user returned", log_content)

    def test_calculate_with_snapshots(self):
        result = sample_decorated.calculate_values(5, 7)
        log_content = self.log_output.getvalue()

        self.assertEqual(result["product"], 35)
        self.assertEqual(result["sum"], 12)
        self.assertIn("Function calculate_values called with", log_content)
        self.assertIn("Variable: product = 35", log_content)
        self.assertIn("Variable: sum_value = 12", log_content)
        self.assertIn("Function calculate_values returned", log_content)


if __name__ == "__main__":
    unittest.main()
