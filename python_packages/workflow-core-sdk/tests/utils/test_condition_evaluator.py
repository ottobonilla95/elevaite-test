"""
Unit tests for condition_evaluator

Tests condition evaluation logic for workflow branching.
"""

import pytest
from workflow_core_sdk.utils.condition_evaluator import (
    ConditionEvaluator,
    Condition,
    ConditionalExpression,
    ConditionOperator,
    LogicalOperator,
)


@pytest.fixture
def evaluator():
    """Create a condition evaluator instance"""
    return ConditionEvaluator()


@pytest.fixture
def context():
    """Create a sample execution context"""
    return {
        "step1": {
            "output": {
                "status": "success",
                "count": 42,
                "message": "Hello World",
                "items": ["a", "b", "c"],
                "data": {"key": "value"},
            }
        },
        "step2": {
            "output": {
                "status": "failed",
                "count": 0,
                "message": "",
                "items": [],
                "data": None,
            }
        },
    }


class TestComparisonOperators:
    """Tests for comparison operators"""

    def test_equals_true(self, evaluator, context):
        """Test equals operator with matching values"""
        condition = Condition(
            left_operand="step1.output.status",
            operator=ConditionOperator.EQUALS,
            right_operand="success",
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_equals_false(self, evaluator, context):
        """Test equals operator with non-matching values"""
        condition = Condition(
            left_operand="step1.output.status",
            operator=ConditionOperator.EQUALS,
            right_operand="failed",
        )
        assert evaluator.evaluate_condition(condition, context) is False

    def test_not_equals(self, evaluator, context):
        """Test not equals operator"""
        condition = Condition(
            left_operand="step1.output.status",
            operator=ConditionOperator.NOT_EQUALS,
            right_operand="failed",
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_greater_than(self, evaluator, context):
        """Test greater than operator"""
        condition = Condition(
            left_operand="step1.output.count",
            operator=ConditionOperator.GREATER_THAN,
            right_operand=40,
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_greater_than_or_equal(self, evaluator, context):
        """Test greater than or equal operator"""
        condition = Condition(
            left_operand="step1.output.count",
            operator=ConditionOperator.GREATER_THAN_OR_EQUAL,
            right_operand=42,
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_less_than(self, evaluator, context):
        """Test less than operator"""
        condition = Condition(
            left_operand="step2.output.count",
            operator=ConditionOperator.LESS_THAN,
            right_operand=10,
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_less_than_or_equal(self, evaluator, context):
        """Test less than or equal operator"""
        condition = Condition(
            left_operand="step2.output.count",
            operator=ConditionOperator.LESS_THAN_OR_EQUAL,
            right_operand=0,
        )
        assert evaluator.evaluate_condition(condition, context) is True


class TestStringOperators:
    """Tests for string operators"""

    def test_contains(self, evaluator, context):
        """Test contains operator"""
        condition = Condition(
            left_operand="step1.output.message",
            operator=ConditionOperator.CONTAINS,
            right_operand="World",
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_not_contains(self, evaluator, context):
        """Test not contains operator"""
        condition = Condition(
            left_operand="step1.output.message",
            operator=ConditionOperator.NOT_CONTAINS,
            right_operand="Goodbye",
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_starts_with(self, evaluator, context):
        """Test starts with operator"""
        condition = Condition(
            left_operand="step1.output.message",
            operator=ConditionOperator.STARTS_WITH,
            right_operand="Hello",
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_ends_with(self, evaluator, context):
        """Test ends with operator"""
        condition = Condition(
            left_operand="step1.output.message",
            operator=ConditionOperator.ENDS_WITH,
            right_operand="World",
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_regex_match(self, evaluator, context):
        """Test regex match operator"""
        condition = Condition(
            left_operand="step1.output.message",
            operator=ConditionOperator.REGEX_MATCH,
            right_operand=r"Hello\s+\w+",
        )
        assert evaluator.evaluate_condition(condition, context) is True


class TestCollectionOperators:
    """Tests for collection operators"""

    def test_in_operator(self, evaluator, context):
        """Test in operator"""
        condition = Condition(
            left_operand="step1.output.status",
            operator=ConditionOperator.IN,
            right_operand=["success", "pending", "running"],
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_not_in_operator(self, evaluator, context):
        """Test not in operator"""
        condition = Condition(
            left_operand="step1.output.status",
            operator=ConditionOperator.NOT_IN,
            right_operand=["failed", "error"],
        )
        assert evaluator.evaluate_condition(condition, context) is True


class TestNullAndEmptyOperators:
    """Tests for null and empty operators"""

    def test_is_null(self, evaluator, context):
        """Test is null operator"""
        condition = Condition(
            left_operand="step2.output.data",
            operator=ConditionOperator.IS_NULL,
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_is_not_null(self, evaluator, context):
        """Test is not null operator"""
        condition = Condition(
            left_operand="step1.output.data",
            operator=ConditionOperator.IS_NOT_NULL,
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_is_empty_string(self, evaluator, context):
        """Test is empty operator with empty string"""
        condition = Condition(
            left_operand="step2.output.message",
            operator=ConditionOperator.IS_EMPTY,
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_is_empty_list(self, evaluator, context):
        """Test is empty operator with empty list"""
        condition = Condition(
            left_operand="step2.output.items",
            operator=ConditionOperator.IS_EMPTY,
        )
        assert evaluator.evaluate_condition(condition, context) is True

    def test_is_not_empty(self, evaluator, context):
        """Test is not empty operator"""
        condition = Condition(
            left_operand="step1.output.message",
            operator=ConditionOperator.IS_NOT_EMPTY,
        )
        assert evaluator.evaluate_condition(condition, context) is True


class TestLogicalOperators:
    """Tests for logical operators (AND, OR, NOT)"""

    def test_and_operator_both_true(self, evaluator, context):
        """Test AND operator with both conditions true"""
        expression = ConditionalExpression(
            conditions=[
                Condition("step1.output.status", ConditionOperator.EQUALS, "success"),
                Condition("step1.output.count", ConditionOperator.GREATER_THAN, 40),
            ],
            logical_operator=LogicalOperator.AND,
        )
        assert evaluator.evaluate_expression(expression, context) is True

    def test_and_operator_one_false(self, evaluator, context):
        """Test AND operator with one condition false"""
        expression = ConditionalExpression(
            conditions=[
                Condition("step1.output.status", ConditionOperator.EQUALS, "success"),
                Condition("step1.output.count", ConditionOperator.LESS_THAN, 40),
            ],
            logical_operator=LogicalOperator.AND,
        )
        assert evaluator.evaluate_expression(expression, context) is False

    def test_or_operator_one_true(self, evaluator, context):
        """Test OR operator with one condition true"""
        expression = ConditionalExpression(
            conditions=[
                Condition("step1.output.status", ConditionOperator.EQUALS, "failed"),
                Condition("step1.output.count", ConditionOperator.GREATER_THAN, 40),
            ],
            logical_operator=LogicalOperator.OR,
        )
        assert evaluator.evaluate_expression(expression, context) is True

    def test_or_operator_both_false(self, evaluator, context):
        """Test OR operator with both conditions false"""
        expression = ConditionalExpression(
            conditions=[
                Condition("step1.output.status", ConditionOperator.EQUALS, "failed"),
                Condition("step1.output.count", ConditionOperator.LESS_THAN, 40),
            ],
            logical_operator=LogicalOperator.OR,
        )
        assert evaluator.evaluate_expression(expression, context) is False


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_missing_variable(self, evaluator, context):
        """Test condition with missing variable"""
        condition = Condition(
            left_operand="step3.output.status",
            operator=ConditionOperator.EQUALS,
            right_operand="success",
        )
        # Should return False when variable doesn't exist
        assert evaluator.evaluate_condition(condition, context) is False

    def test_nested_variable_access(self, evaluator, context):
        """Test accessing nested variables"""
        condition = Condition(
            left_operand="step1.output.data.key",
            operator=ConditionOperator.EQUALS,
            right_operand="value",
        )
        assert evaluator.evaluate_condition(condition, context) is True

