"""Unit tests for the code validator."""

from code_execution_service.services.validator import CodeValidator


class TestCodeValidator:
    """Tests for CodeValidator class."""

    def test_valid_simple_code(self, validator: CodeValidator):
        """Test that simple, safe code passes validation."""
        code = "print('Hello, World!')"
        result = validator.validate(code)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_valid_math_code(self, validator: CodeValidator):
        """Test that math operations pass validation."""
        code = """
import math
import json

result = math.sqrt(16) + math.pi
data = json.dumps({"result": result})
print(data)
"""
        result = validator.validate(code)
        assert result.is_valid

    # === Edge Cases ===

    def test_empty_code(self, validator: CodeValidator):
        """Test that empty code passes validation (no dangerous content)."""
        code = ""
        result = validator.validate(code)
        assert result.is_valid

    def test_whitespace_only_code(self, validator: CodeValidator):
        """Test that whitespace-only code passes validation."""
        code = "   \n\t\n   "
        result = validator.validate(code)
        assert result.is_valid

    def test_comments_only_code(self, validator: CodeValidator):
        """Test that comment-only code passes validation."""
        code = "# This is a comment\n# Another comment"
        result = validator.validate(code)
        assert result.is_valid

    def test_nested_module_import_blocked(self, validator: CodeValidator):
        """Test that nested module imports are blocked (e.g., os.path)."""
        code = "import os.path"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("os" in error for error in result.errors)

    def test_aliased_blocked_import(self, validator: CodeValidator):
        """Test that aliased blocked imports are caught."""
        code = "import os as operating_system"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("os" in error for error in result.errors)

    def test_aliased_from_import(self, validator: CodeValidator):
        """Test that aliased from imports are caught."""
        code = "from subprocess import run as execute"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("subprocess" in error for error in result.errors)

    def test_multiple_patterns_same_line(self, validator: CodeValidator):
        """Test that multiple blocked patterns on same line are all caught."""
        code = "x = obj.__class__.__mro__.__subclasses__()"
        result = validator.validate(code)
        assert not result.is_valid
        # Should catch __class__, __mro__, and __subclasses__
        assert len(result.errors) >= 3

    def test_blocked_import_os(self, validator: CodeValidator):
        """Test that os import is blocked."""
        code = "import os\nos.system('ls')"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("os" in error for error in result.errors)

    def test_blocked_import_subprocess(self, validator: CodeValidator):
        """Test that subprocess import is blocked."""
        code = "import subprocess\nsubprocess.run(['ls'])"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("subprocess" in error for error in result.errors)

    def test_blocked_import_socket(self, validator: CodeValidator):
        """Test that socket import is blocked."""
        code = "import socket\ns = socket.socket()"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("socket" in error for error in result.errors)

    def test_blocked_from_import(self, validator: CodeValidator):
        """Test that 'from x import y' for blocked modules is caught."""
        code = "from os import system\nsystem('ls')"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("os" in error for error in result.errors)

    def test_blocked_function_eval(self, validator: CodeValidator):
        """Test that eval() is blocked."""
        code = "eval('print(1)')"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("eval" in error for error in result.errors)

    def test_blocked_function_exec(self, validator: CodeValidator):
        """Test that exec() is blocked."""
        code = "exec('print(1)')"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("exec" in error for error in result.errors)

    def test_blocked_function_open(self, validator: CodeValidator):
        """Test that open() is blocked."""
        code = "f = open('/etc/passwd', 'r')"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("open" in error for error in result.errors)

    def test_blocked_pattern_dunder_class(self, validator: CodeValidator):
        """Test that __class__ access is blocked."""
        code = "x = ''.__class__"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("__class__" in error for error in result.errors)

    def test_blocked_pattern_dunder_globals(self, validator: CodeValidator):
        """Test that __globals__ access is blocked."""
        code = "x = (lambda: 0).__globals__"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("__globals__" in error for error in result.errors)

    def test_blocked_pattern_dunder_subclasses(self, validator: CodeValidator):
        """Test that __subclasses__ is blocked."""
        code = "x = object.__subclasses__()"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("__subclasses__" in error for error in result.errors)

    def test_syntax_error(self, validator: CodeValidator):
        """Test that syntax errors are caught."""
        code = "def foo(\nprint('incomplete')"
        result = validator.validate(code)
        assert not result.is_valid
        assert any("Syntax error" in error for error in result.errors)

    def test_allowed_pandas_import(self, validator: CodeValidator):
        """Test that pandas import is allowed."""
        code = "import pandas as pd\ndf = pd.DataFrame({'a': [1, 2, 3]})"
        result = validator.validate(code)
        assert result.is_valid

    def test_allowed_numpy_import(self, validator: CodeValidator):
        """Test that numpy import is allowed."""
        code = "import numpy as np\narr = np.array([1, 2, 3])"
        result = validator.validate(code)
        assert result.is_valid

    def test_multiple_errors(self, validator: CodeValidator):
        """Test that multiple errors are collected."""
        code = "import os\nimport subprocess\neval('1')"
        result = validator.validate(code)
        assert not result.is_valid
        assert len(result.errors) >= 3
