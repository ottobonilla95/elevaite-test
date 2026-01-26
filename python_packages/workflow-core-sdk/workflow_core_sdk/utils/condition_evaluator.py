"""
Conditional Execution Logic

Provides expression evaluation for dynamic workflow branching based on step results.
Supports complex conditions, comparisons, and logical operations.
"""

import re
import json
import logging
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from dataclasses import dataclass


logger = logging.getLogger(__name__)


class ConditionOperator(str, Enum):
    """Supported condition operators"""

    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    REGEX_MATCH = "regex_match"
    IS_EMPTY = "is_empty"
    IS_NOT_EMPTY = "is_not_empty"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions"""

    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class Condition:
    """Single condition definition"""

    left_operand: str  # Variable reference like "step1.output.status"
    operator: ConditionOperator
    right_operand: Any = None  # Value to compare against
    description: Optional[str] = None


@dataclass
class ConditionalExpression:
    """Complex conditional expression with logical operators"""

    conditions: List[Union[Condition, "ConditionalExpression"]]
    logical_operator: LogicalOperator = LogicalOperator.AND
    description: Optional[str] = None


class ConditionEvaluator:
    """Evaluates conditional expressions against execution context"""

    def __init__(self):
        self.variable_pattern = re.compile(
            r"^([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)"
        )

    def evaluate_condition(self, condition: Condition, context: Dict[str, Any]) -> bool:
        """
        Evaluate a single condition against the context.

        Args:
            condition: Condition to evaluate
            context: Execution context with step results

        Returns:
            Boolean result of condition evaluation
        """
        try:
            # Get left operand value
            left_value = self._resolve_variable(condition.left_operand, context)

            # Evaluate based on operator
            if condition.operator == ConditionOperator.EQUALS:
                return left_value == condition.right_operand

            elif condition.operator == ConditionOperator.NOT_EQUALS:
                return left_value != condition.right_operand

            elif condition.operator == ConditionOperator.GREATER_THAN:
                return self._safe_compare(
                    left_value, condition.right_operand, lambda a, b: a > b
                )

            elif condition.operator == ConditionOperator.GREATER_THAN_OR_EQUAL:
                return self._safe_compare(
                    left_value, condition.right_operand, lambda a, b: a >= b
                )

            elif condition.operator == ConditionOperator.LESS_THAN:
                return self._safe_compare(
                    left_value, condition.right_operand, lambda a, b: a < b
                )

            elif condition.operator == ConditionOperator.LESS_THAN_OR_EQUAL:
                return self._safe_compare(
                    left_value, condition.right_operand, lambda a, b: a <= b
                )

            elif condition.operator == ConditionOperator.CONTAINS:
                return self._safe_contains(left_value, condition.right_operand)

            elif condition.operator == ConditionOperator.NOT_CONTAINS:
                return not self._safe_contains(left_value, condition.right_operand)

            elif condition.operator == ConditionOperator.IN:
                return (
                    left_value in condition.right_operand
                    if condition.right_operand
                    else False
                )

            elif condition.operator == ConditionOperator.NOT_IN:
                return (
                    left_value not in condition.right_operand
                    if condition.right_operand
                    else True
                )

            elif condition.operator == ConditionOperator.STARTS_WITH:
                return str(left_value).startswith(str(condition.right_operand))

            elif condition.operator == ConditionOperator.ENDS_WITH:
                return str(left_value).endswith(str(condition.right_operand))

            elif condition.operator == ConditionOperator.REGEX_MATCH:
                return bool(re.search(str(condition.right_operand), str(left_value)))

            elif condition.operator == ConditionOperator.IS_EMPTY:
                return self._is_empty(left_value)

            elif condition.operator == ConditionOperator.IS_NOT_EMPTY:
                return not self._is_empty(left_value)

            elif condition.operator == ConditionOperator.IS_NULL:
                return left_value is None

            elif condition.operator == ConditionOperator.IS_NOT_NULL:
                return left_value is not None

            else:
                logger.warning(f"Unknown operator: {condition.operator}")
                return False

        except Exception as e:
            logger.error(f"Error evaluating condition {condition}: {e}")
            return False

    def evaluate_expression(
        self, expression: ConditionalExpression, context: Dict[str, Any]
    ) -> bool:
        """
        Evaluate a complex conditional expression.

        Args:
            expression: Conditional expression to evaluate
            context: Execution context with step results

        Returns:
            Boolean result of expression evaluation
        """
        try:
            if not expression.conditions:
                return True

            results = []

            for condition_or_expr in expression.conditions:
                if isinstance(condition_or_expr, Condition):
                    result = self.evaluate_condition(condition_or_expr, context)
                elif isinstance(condition_or_expr, ConditionalExpression):
                    result = self.evaluate_expression(condition_or_expr, context)
                else:
                    logger.warning(f"Unknown condition type: {type(condition_or_expr)}")
                    result = False

                results.append(result)

            # Apply logical operator
            if expression.logical_operator == LogicalOperator.AND:
                return all(results)
            elif expression.logical_operator == LogicalOperator.OR:
                return any(results)
            elif expression.logical_operator == LogicalOperator.NOT:
                # For NOT, we negate the first result
                return not results[0] if results else True
            else:
                logger.warning(
                    f"Unknown logical operator: {expression.logical_operator}"
                )
                return False

        except Exception as e:
            logger.error(f"Error evaluating expression {expression}: {e}")
            return False

    def parse_condition_string(self, condition_str: str) -> Optional[Condition]:
        """
        Parse a condition string into a Condition object.

        Examples:
            "step1.output.status == 'success'"
            "step2.result.count > 10"
            "step3.data contains 'error'"
        """
        try:
            # Simple parsing for common patterns
            for op in ConditionOperator:
                if op.value in condition_str:
                    parts = condition_str.split(op.value, 1)
                    if len(parts) == 2:
                        left = parts[0].strip()
                        right = parts[1].strip()

                        # Parse right operand
                        right_value = self._parse_value(right)

                        return Condition(
                            left_operand=left, operator=op, right_operand=right_value
                        )

            # Handle unary operators
            if condition_str.strip().endswith(" is_empty"):
                left = condition_str.replace(" is_empty", "").strip()
                return Condition(left_operand=left, operator=ConditionOperator.IS_EMPTY)

            if condition_str.strip().endswith(" is_not_empty"):
                left = condition_str.replace(" is_not_empty", "").strip()
                return Condition(
                    left_operand=left, operator=ConditionOperator.IS_NOT_EMPTY
                )

            if condition_str.strip().endswith(" is_null"):
                left = condition_str.replace(" is_null", "").strip()
                return Condition(left_operand=left, operator=ConditionOperator.IS_NULL)

            if condition_str.strip().endswith(" is_not_null"):
                left = condition_str.replace(" is_not_null", "").strip()
                return Condition(
                    left_operand=left, operator=ConditionOperator.IS_NOT_NULL
                )

            logger.warning(f"Could not parse condition string: {condition_str}")
            return None

        except Exception as e:
            logger.error(f"Error parsing condition string '{condition_str}': {e}")
            return None

    def _resolve_variable(self, variable_path: str, context: Dict[str, Any]) -> Any:
        """Resolve a variable path like 'step1.output.status' from context"""
        try:
            parts = variable_path.split(".")
            current = context

            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif hasattr(current, part):
                    current = getattr(current, part)
                else:
                    return None

            return current

        except Exception as e:
            logger.error(f"Error resolving variable '{variable_path}': {e}")
            return None

    def _parse_value(self, value_str: str) -> Any:
        """Parse a string value into appropriate Python type"""
        value_str = value_str.strip()

        # Remove quotes for strings
        if (value_str.startswith('"') and value_str.endswith('"')) or (
            value_str.startswith("'") and value_str.endswith("'")
        ):
            return value_str[1:-1]

        # Try to parse as number
        try:
            if "." in value_str:
                return float(value_str)
            else:
                return int(value_str)
        except ValueError:
            pass

        # Try to parse as boolean
        if value_str.lower() == "true":
            return True
        elif value_str.lower() == "false":
            return False
        elif value_str.lower() == "null" or value_str.lower() == "none":
            return None

        # Try to parse as JSON (for lists/objects)
        try:
            return json.loads(value_str)
        except json.JSONDecodeError:
            pass

        # Return as string if all else fails
        return value_str

    def _safe_compare(self, left: Any, right: Any, comparator) -> bool:
        """Safely compare two values with type conversion if needed"""
        try:
            # Try direct comparison first
            return comparator(left, right)
        except TypeError:
            # Try converting to same type
            try:
                if isinstance(left, str) and isinstance(right, (int, float)):
                    return comparator(float(left), right)
                elif isinstance(right, str) and isinstance(left, (int, float)):
                    return comparator(left, float(right))
                else:
                    return comparator(str(left), str(right))
            except (ValueError, TypeError):
                return False

    def _safe_contains(self, container: Any, item: Any) -> bool:
        """Safely check if container contains item"""
        try:
            if isinstance(container, (str, list, tuple, dict)):
                return item in container
            else:
                return item in str(container)
        except TypeError:
            return False

    def _is_empty(self, value: Any) -> bool:
        """Check if a value is considered empty"""
        if value is None:
            return True
        if isinstance(value, (str, list, tuple, dict)):
            return len(value) == 0
        return False


# Global condition evaluator instance
condition_evaluator = ConditionEvaluator()
