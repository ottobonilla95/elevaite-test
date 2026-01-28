"""Unit tests for the sandbox executor."""

from code_execution_service.services.sandbox import SandboxExecutor


class TestSandboxExecutor:
    """Tests for SandboxExecutor class."""

    def test_wrapper_code_with_input_data(self, sandbox: SandboxExecutor):
        """Test that wrapper code correctly injects input_data."""
        code = "print(input_data['key'])"
        input_data = {"key": "value", "number": 42}

        wrapper = sandbox._create_wrapper_code(code, input_data)

        # Should contain the JSON-serialized input_data
        assert "input_data = " in wrapper
        assert '"key"' in wrapper
        assert '"value"' in wrapper
        assert "42" in wrapper
        # Should contain the user code
        assert "print(input_data['key'])" in wrapper

    def test_wrapper_code_without_input_data(self, sandbox: SandboxExecutor):
        """Test that wrapper code handles None input_data."""
        code = "print('hello')"

        wrapper = sandbox._create_wrapper_code(code, None)

        # Should set input_data to None
        assert "input_data = None" in wrapper
        # Should contain the user code
        assert "print('hello')" in wrapper

    def test_wrapper_code_with_empty_input_data(self, sandbox: SandboxExecutor):
        """Test that wrapper code handles empty dict input_data."""
        code = "print('hello')"

        wrapper = sandbox._create_wrapper_code(code, {})

        # Should contain empty dict
        assert "input_data = {}" in wrapper

    def test_wrapper_code_with_nested_input_data(self, sandbox: SandboxExecutor):
        """Test that wrapper code handles nested input_data."""
        code = "print(input_data)"
        input_data = {
            "nested": {"deep": {"value": 123}},
            "list": [1, 2, 3],
        }

        wrapper = sandbox._create_wrapper_code(code, input_data)

        # Should contain the nested structure
        assert '"nested"' in wrapper
        assert '"deep"' in wrapper
        assert "123" in wrapper

    def test_wrapper_code_preserves_user_code(self, sandbox: SandboxExecutor):
        """Test that wrapper code preserves multi-line user code."""
        code = """def calculate(x):
    return x * 2

result = calculate(21)
print(result)"""

        wrapper = sandbox._create_wrapper_code(code, None)

        # Should preserve the function definition
        assert "def calculate(x):" in wrapper
        assert "return x * 2" in wrapper
        assert "result = calculate(21)" in wrapper

    def test_is_available_returns_bool(self, sandbox: SandboxExecutor):
        """Test that is_available returns a boolean."""
        result = sandbox.is_available()
        assert isinstance(result, bool)

    def test_sandbox_with_custom_paths(self):
        """Test that sandbox accepts custom paths."""
        sandbox = SandboxExecutor(
            nsjail_path="/custom/nsjail",
            nsjail_config_path="/custom/config.cfg",
            sandbox_python_path="/custom/python",
            sandbox_tmp_dir="/custom/tmp",
        )

        assert sandbox.nsjail_path == "/custom/nsjail"
        assert sandbox.nsjail_config_path == "/custom/config.cfg"
        assert sandbox.sandbox_python_path == "/custom/python"
        assert sandbox.sandbox_tmp_dir == "/custom/tmp"

    def test_sandbox_uses_default_settings(self, sandbox: SandboxExecutor):
        """Test that sandbox uses settings defaults when not specified."""
        from code_execution_service.core.config import settings

        assert sandbox.nsjail_path == settings.nsjail_path
        assert sandbox.nsjail_config_path == settings.nsjail_config_path
        assert sandbox.sandbox_python_path == settings.sandbox_python_path
        assert sandbox.sandbox_tmp_dir == settings.sandbox_tmp_dir

