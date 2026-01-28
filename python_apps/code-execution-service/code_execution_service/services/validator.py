"""Pre-execution code validator using AST parsing and blocklists.

This module provides defense-in-depth validation before code reaches the Nsjail sandbox.
"""

import ast
import re
from dataclasses import dataclass, field

# Blocked imports - dangerous modules that could escape sandbox
BLOCKED_IMPORTS: set[str] = {
    "os",
    "subprocess",
    "socket",
    "requests",
    "urllib",
    "http",
    "sys",
    "ctypes",
    "multiprocessing",
    "threading",
    "signal",
    "shutil",
    "pathlib",
    "glob",
    "tempfile",
    "importlib",
    "builtins",
    "code",
    "codeop",
    "pickle",
    "marshal",
    "shelve",
    "dbm",
    "sqlite3",
    "pty",
    "tty",
    "fcntl",
    "resource",
    "syslog",
    "asyncio",  # Could be used for network operations
    "aiohttp",
    "httpx",
    "ssl",
    "ftplib",
    "smtplib",
    "poplib",
    "imaplib",
    "telnetlib",
    "webbrowser",
    "pdb",
    "trace",
    "gc",
}

# Blocked function calls
BLOCKED_FUNCTIONS: set[str] = {
    "eval",
    "exec",
    "compile",
    "open",
    "__import__",
    "getattr",
    "setattr",
    "delattr",
    "globals",
    "locals",
    "vars",
    "dir",
    "type",
    "isinstance",  # Can be used for introspection attacks
    "issubclass",
    "hasattr",
    "id",
    "memoryview",
    "bytearray",
    "breakpoint",
    "input",  # Blocks on stdin which could cause hangs
    "help",
    "exit",
    "quit",
}

# Blocked patterns in code (regex patterns)
BLOCKED_PATTERNS: list[tuple[str, str]] = [
    (r"__class__", "Access to __class__ attribute"),
    (r"__globals__", "Access to __globals__ attribute"),
    (r"__subclasses__", "Access to __subclasses__ method"),
    (r"__mro__", "Access to __mro__ attribute"),
    (r"__code__", "Access to __code__ attribute"),
    (r"__dict__", "Access to __dict__ attribute"),
    (r"__bases__", "Access to __bases__ attribute"),
    (r"__import__", "Use of __import__ function"),
    (r"__builtins__", "Access to __builtins__"),
    (r"__loader__", "Access to __loader__"),
    (r"__spec__", "Access to __spec__"),
    (r"__file__", "Access to __file__"),
    (r"__name__", "Access to __name__"),
    (r"__package__", "Access to __package__"),
]


@dataclass
class ValidationResult:
    """Result of code validation."""

    is_valid: bool
    errors: list[str] = field(default_factory=list)


class CodeValidator:
    """Validates Python code for safety before execution."""

    def __init__(
        self,
        blocked_imports: set[str] | None = None,
        blocked_functions: set[str] | None = None,
        blocked_patterns: list[tuple[str, str]] | None = None,
    ):
        self.blocked_imports = blocked_imports or BLOCKED_IMPORTS
        self.blocked_functions = blocked_functions or BLOCKED_FUNCTIONS
        self.blocked_patterns = blocked_patterns or BLOCKED_PATTERNS

    def validate(self, code: str) -> ValidationResult:
        """Validate code for security issues.

        Args:
            code: Python code to validate

        Returns:
            ValidationResult with is_valid and list of errors
        """
        errors: list[str] = []

        # Check for syntax errors first
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return ValidationResult(is_valid=False, errors=[f"Syntax error: {e}"])

        # AST-based validation
        errors.extend(self._check_imports(tree))
        errors.extend(self._check_function_calls(tree))

        # Pattern-based validation
        errors.extend(self._check_patterns(code))

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    def _check_imports(self, tree: ast.AST) -> list[str]:
        """Check for blocked imports."""
        errors: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split(".")[0]
                    if module_name in self.blocked_imports:
                        errors.append(f"Blocked import: {alias.name}")
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split(".")[0]
                    if module_name in self.blocked_imports:
                        errors.append(f"Blocked import: from {node.module}")

        return errors

    def _check_function_calls(self, tree: ast.AST) -> list[str]:
        """Check for blocked function calls."""
        errors: list[str] = []

        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                func_name = self._get_function_name(node.func)
                if func_name and func_name in self.blocked_functions:
                    errors.append(f"Blocked function: {func_name}")

        return errors

    def _get_function_name(self, node: ast.expr) -> str | None:
        """Extract function name from a Call node's func attribute."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    def _check_patterns(self, code: str) -> list[str]:
        """Check for blocked patterns using regex."""
        errors: list[str] = []

        for pattern, description in self.blocked_patterns:
            if re.search(pattern, code):
                errors.append(f"Blocked pattern: {description}")

        return errors
