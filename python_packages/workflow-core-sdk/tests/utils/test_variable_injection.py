"""
Unit tests for variable_injection utility.

Tests the {{variable}} template syntax for runtime value injection in prompts
and other workflow templates.
"""

from datetime import datetime
from unittest.mock import MagicMock

from workflow_core_sdk.utils.variable_injection import (
    inject_variables,
    extract_variables,
    resolve_variable,
    get_builtin_variables,
    VARIABLE_PATTERN,
)


class TestVariablePattern:
    """Tests for the regex pattern matching {{variable}} syntax."""

    def test_simple_variable(self):
        """Test matching a simple variable."""
        matches = VARIABLE_PATTERN.findall("Hello {{name}}")
        assert matches == ["name"]

    def test_multiple_variables(self):
        """Test matching multiple variables."""
        matches = VARIABLE_PATTERN.findall("{{greeting}} {{name}}, time is {{current_time}}")
        assert len(matches) == 3
        assert "greeting" in [m.strip() for m in matches]
        assert "name" in [m.strip() for m in matches]
        assert "current_time" in [m.strip() for m in matches]

    def test_variable_with_spaces(self):
        """Test variable with spaces around the name."""
        matches = VARIABLE_PATTERN.findall("Hello {{ name }}")
        assert len(matches) == 1
        assert matches[0].strip() == "name"

    def test_dot_notation_variable(self):
        """Test variable with dot notation."""
        matches = VARIABLE_PATTERN.findall("Data: {{step_1.output}}")
        assert len(matches) == 1
        assert matches[0].strip() == "step_1.output"

    def test_no_match_single_braces(self):
        """Test that single braces are not matched."""
        matches = VARIABLE_PATTERN.findall("Hello {name}")
        assert matches == []

    def test_no_match_triple_braces(self):
        """Test that triple braces only match inner pair."""
        matches = VARIABLE_PATTERN.findall("Hello {{{name}}}")
        assert len(matches) == 1


class TestExtractVariables:
    """Tests for extract_variables function."""

    def test_extract_single_variable(self):
        """Test extracting a single variable."""
        result = extract_variables("Hello {{name}}")
        assert result == ["name"]

    def test_extract_multiple_variables(self):
        """Test extracting multiple variables."""
        result = extract_variables("{{greeting}} {{name}}, time is {{current_time}}")
        assert len(result) == 3
        assert "greeting" in result
        assert "name" in result
        assert "current_time" in result

    def test_extract_with_duplicates(self):
        """Test that duplicates are preserved."""
        result = extract_variables("{{name}} and {{name}} again")
        assert result == ["name", "name"]

    def test_extract_from_empty_string(self):
        """Test extracting from empty string."""
        result = extract_variables("")
        assert result == []

    def test_extract_from_none(self):
        """Test extracting from None."""
        result = extract_variables(None)
        assert result == []

    def test_extract_no_variables(self):
        """Test string with no variables."""
        result = extract_variables("Hello world, no variables here")
        assert result == []


class TestGetBuiltinVariables:
    """Tests for get_builtin_variables function."""

    def test_builtin_variables_exist(self):
        """Test that expected built-in variables are defined."""
        builtins = get_builtin_variables()
        expected_keys = [
            "current_time",
            "current_date",
            "current_timestamp",
            "current_year",
            "current_month",
            "current_day",
            "uuid",
            "execution_id",
        ]
        for key in expected_keys:
            assert key in builtins, f"Missing built-in variable: {key}"

    def test_builtin_variables_are_callable(self):
        """Test that built-in variables are callable."""
        builtins = get_builtin_variables()
        for name, func in builtins.items():
            assert callable(func), f"Built-in {name} should be callable"

    def test_current_time_format(self):
        """Test that current_time returns ISO format."""
        builtins = get_builtin_variables()
        result = builtins["current_time"]()
        # Should be parseable as ISO datetime
        datetime.fromisoformat(result.replace("Z", "+00:00"))


class TestResolveVariable:
    """Tests for resolve_variable function."""

    def test_resolve_custom_variable(self):
        """Test resolving a custom variable."""
        result = resolve_variable("name", {"name": "Alice"})
        assert result == "Alice"

    def test_resolve_builtin_variable(self):
        """Test resolving a built-in variable."""
        result = resolve_variable("current_year")
        assert result == str(datetime.now().year)

    def test_resolve_unknown_variable(self):
        """Test resolving an unknown variable returns None."""
        result = resolve_variable("unknown_var", {})
        assert result is None

    def test_resolve_dot_notation_with_context(self):
        """Test resolving dot notation with execution context."""
        mock_context = MagicMock()
        mock_context.step_io_data = {"step_1": {"output": "step output value", "count": 42}}
        result = resolve_variable("step_1.output", {}, mock_context)
        assert result == "step output value"

    def test_resolve_execution_id_from_context(self):
        """Test resolving execution_id from execution context."""
        mock_context = MagicMock()
        mock_context.execution_id = "exec-123"
        result = resolve_variable("execution_id", {}, mock_context)
        assert result == "exec-123"

    def test_custom_takes_priority_over_builtin(self):
        """Test that custom variables take priority over built-ins."""
        result = resolve_variable("current_time", {"current_time": "custom_time"})
        assert result == "custom_time"


class TestInjectVariables:
    """Tests for inject_variables function."""

    def test_inject_single_variable(self):
        """Test injecting a single variable."""
        result = inject_variables("Hello {{name}}", {"name": "Alice"})
        assert result == "Hello Alice"

    def test_inject_multiple_variables(self):
        """Test injecting multiple variables."""
        result = inject_variables("{{greeting}} {{name}}!", {"greeting": "Hello", "name": "Bob"})
        assert result == "Hello Bob!"

    def test_inject_builtin_variable(self):
        """Test injecting a built-in variable."""
        result = inject_variables("Year: {{current_year}}")
        assert result == f"Year: {datetime.now().year}"

    def test_inject_mixed_custom_and_builtin(self):
        """Test injecting both custom and built-in variables."""
        result = inject_variables("Hello {{name}}, year is {{current_year}}", {"name": "Alice"})
        assert "Hello Alice" in result
        assert str(datetime.now().year) in result

    def test_inject_unresolved_preserve(self):
        """Test preserving unresolved variables."""
        result = inject_variables("Hello {{unknown}}", {}, preserve_unresolved=True)
        assert result == "Hello {{unknown}}"

    def test_inject_unresolved_replace_empty(self):
        """Test replacing unresolved variables with empty string."""
        result = inject_variables("Hello {{unknown}}", {}, preserve_unresolved=False)
        assert result == "Hello "

    def test_inject_empty_string(self):
        """Test injecting into empty string."""
        result = inject_variables("", {"name": "Alice"})
        assert result == ""

    def test_inject_none_returns_none(self):
        """Test that None input returns None."""
        result = inject_variables(None, {"name": "Alice"})
        assert result is None

    def test_inject_no_variables_returns_original(self):
        """Test that string without variables is returned unchanged."""
        original = "Hello world"
        result = inject_variables(original, {"name": "Alice"})
        assert result == original

    def test_inject_with_execution_context(self):
        """Test injecting with execution context for step data."""
        mock_context = MagicMock()
        mock_context.step_io_data = {"step_1": {"result": "success"}}

        result = inject_variables("Status: {{step_1.result}}", {}, execution_context=mock_context)
        assert result == "Status: success"

    def test_inject_numeric_value(self):
        """Test injecting numeric values."""
        result = inject_variables("Count: {{count}}", {"count": 42})
        assert result == "Count: 42"

    def test_inject_complex_prompt(self):
        """Test injecting into a complex prompt template."""
        template = """You are an assistant. Current time: {{current_time}}.
User name: {{user_name}}.
Previous step output: {{prev_step.data}}."""

        mock_context = MagicMock()
        mock_context.step_io_data = {"prev_step": {"data": "important info"}}

        result = inject_variables(template, {"user_name": "Alice"}, execution_context=mock_context)

        assert "User name: Alice" in result
        assert "Previous step output: important info" in result
        # current_time should be replaced with actual time
        assert "{{current_time}}" not in result
