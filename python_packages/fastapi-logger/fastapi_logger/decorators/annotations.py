import ast
from dataclasses import dataclass
from typing import Any, List


@dataclass
class LogAnnotation:
    """Represents a log annotation in code."""

    kind: str  # Annotation type: 'capture', 'watch', 'snapshot', etc.
    value: Any  # The code being annotated
    line_number: int  # Line number in the source file


def parse_annotations(
    source_code: str, logger_name: str = "logger"
) -> List[LogAnnotation]:
    """
    Parse function source code to find annotations.

    Supports two styles:
    - Call expressions (elevaite_logger.watch("...")) via AST
    - Test-friendly pseudo-annotations using lines like:
        @elevaite_logger.watch
        f"..."
      where we pair the marker with the next non-empty line
    """
    annotations: List[LogAnnotation] = []

    # First attempt: AST-based parsing for call expressions
    try:
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                func = node.value.func
                if isinstance(func, ast.Attribute) and isinstance(func.value, ast.Name):
                    var = func.value.id
                    kind = func.attr
                    if kind in ["capture", "watch", "snapshot"] and (
                        not logger_name or var == logger_name or var.endswith("_logger")
                    ):
                        if node.value.args:
                            try:
                                value = ast.unparse(node.value.args[0])
                            except Exception:
                                value = ""
                            annotations.append(LogAnnotation(kind, value, node.lineno))
    except SyntaxError:
        # Fall back to line parsing
        pass
    except Exception:
        pass

    # Fallback: line-based pairing for test pseudo-annotations
    if not annotations:
        lines = source_code.splitlines()
        total = len(lines)
        i = 0
        while i < total:
            stripped = lines[i].strip()
            if stripped.startswith("@"):
                marker = stripped[1:]
                # Expect pattern like elevaite_logger.watch
                parts = marker.split(".")
                if len(parts) == 2:
                    var, kind = parts[0].strip(), parts[1].strip()
                    if kind in ["capture", "watch", "snapshot"] and (
                        not logger_name or var == logger_name or var.endswith("_logger")
                    ):
                        # Find next non-empty line as the value
                        j = i + 1
                        while j < total and lines[j].strip() == "":
                            j += 1
                        if j < total:
                            value = lines[j].strip()
                            annotations.append(LogAnnotation(kind, value, j + 1))
                            i = j
                            continue
            i += 1

    return annotations
