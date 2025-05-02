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

    Args:
        source_code: The source code to parse
        logger_name: Optional name of the logger variable to match

    Returns:
        List of found annotations
    """
    annotations = []

    try:
        # Parse the source code
        tree = ast.parse(source_code)

        # Find all decorator expressions (@elevaite_logger.X)
        for node in ast.walk(tree):
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Attribute):
                    attr = node.value.func
                    if (
                        isinstance(attr.value, ast.Name)
                        and (
                            not logger_name
                            or attr.value.id == logger_name
                            or attr.value.id.endswith("_logger")
                        )
                        and attr.attr in ["capture", "watch", "snapshot"]
                    ):

                        kind = attr.attr
                        line_number = node.lineno

                        # Get the expression being logged
                        if len(node.value.args) > 0:
                            value = ast.unparse(node.value.args[0])
                            annotations.append(LogAnnotation(kind, value, line_number))

    except (SyntaxError, AttributeError) as e:
        pass  # Log parse error - handled by calling code

    return annotations
