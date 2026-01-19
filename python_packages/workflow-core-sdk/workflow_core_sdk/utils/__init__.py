"""Utility modules for workflow-core-sdk"""

from typing import Any

from .condition_evaluator import ConditionEvaluator
from .crypto import (
    ENCRYPTION_KEY_ENV,
    decrypt_credentials,
    decrypt_if_encrypted,
    encrypt_credentials,
    encrypt_if_configured,
    generate_encryption_key,
    get_encryption_key,
    is_encrypted,
)
from .schema_utils import (
    python_type_to_json_type,
    function_to_openai_schema,
    create_step_input_schema,
    create_step_output_schema,
    infer_output_schema_from_function,
    extract_output_fields,
)
from .variable_injection import (
    inject_variables,
    extract_variables,
    resolve_variable,
    get_builtin_variables,
    VARIABLE_PATTERN,
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
    # Crypto utilities
    "ENCRYPTION_KEY_ENV",
    "decrypt_credentials",
    "decrypt_if_encrypted",
    "encrypt_credentials",
    "encrypt_if_configured",
    "generate_encryption_key",
    "get_encryption_key",
    "is_encrypted",
    # Variable injection utilities
    "inject_variables",
    "extract_variables",
    "resolve_variable",
    "get_builtin_variables",
    "VARIABLE_PATTERN",
]
