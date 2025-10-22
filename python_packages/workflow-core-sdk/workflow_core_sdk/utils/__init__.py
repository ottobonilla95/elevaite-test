"""Utility modules for workflow-core-sdk"""

from typing import Any

from .condition_evaluator import ConditionEvaluator
from .schema_utils import (
    python_type_to_json_type,
    function_to_openai_schema,
    create_step_input_schema,
    create_step_output_schema,
    infer_output_schema_from_function,
    extract_output_fields,
)


def ensure_uuid_str(value: Any) -> str:
    s = str(value)
    return s


__all__ = [
    "ConditionEvaluator",
    "python_type_to_json_type",
    "function_to_openai_schema",
    "create_step_input_schema",
    "create_step_output_schema",
    "infer_output_schema_from_function",
    "extract_output_fields",
    "ensure_uuid_str",
]
