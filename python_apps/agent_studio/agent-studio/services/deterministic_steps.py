"""
Basic step implementations for deterministic workflows.

This module provides basic implementations for common deterministic workflow steps
that can be used as building blocks for more complex workflows.
"""

import json
import time
from typing import Dict, Any, Optional
from datetime import datetime
from fastapi_logger import ElevaiteLogger


class DeterministicStepImplementations:
    """Collection of basic step implementations for deterministic workflows."""

    def __init__(self):
        self.logger = ElevaiteLogger()

    async def data_input_step(
        self,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle data input step - processes and validates input data.

        Args:
            step_config: Configuration for this step
            input_data: Input data from previous steps or workflow input
            execution_context: Current execution context

        Returns:
            Processed input data
        """
        self.logger.info(
            f"Executing data_input step: {step_config.get('step_name', 'Unknown')}"
        )

        config = step_config.get("config", {})
        input_source = config.get("input_source", "user_query")
        validation_rules = config.get("validation_rules", [])

        # Extract data based on input source
        if input_source == "user_query":
            data = input_data.get("query", "")
        elif input_source == "chat_history":
            data = input_data.get("chat_history", [])
        elif input_source == "runtime_overrides":
            data = input_data.get("runtime_overrides", {})
        else:
            data = input_data

        # Apply validation rules
        for rule in validation_rules:
            if rule == "required" and not data:
                raise ValueError(f"Required input data is missing for {input_source}")
            elif rule == "non_empty" and isinstance(data, str) and not data.strip():
                raise ValueError(f"Input data cannot be empty for {input_source}")

        result = {
            "input_source": input_source,
            "data": data,
            "validated": True,
            "timestamp": datetime.now().isoformat(),
            "validation_rules_applied": validation_rules,
        }

        self.logger.info(f"Data input step completed successfully")
        return result

    async def transformation_step(
        self,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle data transformation step - applies transformations to input data.

        Args:
            step_config: Configuration for this step
            input_data: Input data from previous steps
            execution_context: Current execution context

        Returns:
            Transformed data
        """
        self.logger.info(
            f"Executing transformation step: {step_config.get('step_name', 'Unknown')}"
        )

        config = step_config.get("config", {})
        transformation_type = config.get("transformation_type", "text_processing")
        operations = config.get("operations", [])

        # Get input data from previous step
        data = input_data.get("data", "")

        # Apply transformations based on type
        if transformation_type == "text_processing" and isinstance(data, str):
            transformed_data = data

            for operation in operations:
                if operation == "lowercase":
                    transformed_data = transformed_data.lower()
                elif operation == "uppercase":
                    transformed_data = transformed_data.upper()
                elif operation == "trim":
                    transformed_data = transformed_data.strip()
                elif operation == "normalize":
                    # Basic normalization - remove extra whitespace
                    transformed_data = " ".join(transformed_data.split())
                elif operation == "remove_punctuation":
                    import string

                    transformed_data = transformed_data.translate(
                        str.maketrans("", "", string.punctuation)
                    )

        elif transformation_type == "json_processing" and isinstance(
            data, (dict, list)
        ):
            transformed_data = data
            # Add JSON-specific transformations here if needed

        else:
            # Default: return data as-is
            transformed_data = data

        result = {
            "original_data": data,
            "transformed_data": transformed_data,
            "transformation_type": transformation_type,
            "operations_applied": operations,
            "timestamp": datetime.now().isoformat(),
        }

        self.logger.info(f"Transformation step completed successfully")
        return result

    async def data_output_step(
        self,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle data output step - formats and outputs final results.

        Args:
            step_config: Configuration for this step
            input_data: Input data from previous steps
            execution_context: Current execution context

        Returns:
            Formatted output data
        """
        self.logger.info(
            f"Executing data_output step: {step_config.get('step_name', 'Unknown')}"
        )

        config = step_config.get("config", {})
        output_format = config.get("output_format", "json")
        include_metadata = config.get("include_metadata", True)

        # Get processed data from previous step
        processed_data = input_data.get(
            "transformed_data", input_data.get("data", input_data)
        )

        # Format output based on configuration
        if output_format == "json":
            if include_metadata:
                output = {
                    "result": processed_data,
                    "metadata": {
                        "workflow_execution_id": execution_context.get("execution_id"),
                        "step_name": step_config.get("step_name"),
                        "timestamp": datetime.now().isoformat(),
                        "format": output_format,
                    },
                }
            else:
                output = {"result": processed_data}

        elif output_format == "text":
            if isinstance(processed_data, str):
                output = processed_data
            else:
                output = str(processed_data)

        elif output_format == "raw":
            output = processed_data

        else:
            # Default to JSON
            output = {"result": processed_data}

        self.logger.info(f"Data output step completed successfully")
        return output

    async def validation_step(
        self,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle validation step - validates data against specified rules.

        Args:
            step_config: Configuration for this step
            input_data: Input data from previous steps
            execution_context: Current execution context

        Returns:
            Validation results
        """
        self.logger.info(
            f"Executing validation step: {step_config.get('step_name', 'Unknown')}"
        )

        config = step_config.get("config", {})
        validation_rules = config.get("validation_rules", [])
        data_field = config.get("data_field", "data")

        # Get data to validate
        data = input_data.get(data_field, input_data)

        validation_results = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "data": data,
            "rules_checked": validation_rules,
        }

        # Apply validation rules
        for rule in validation_rules:
            if rule == "not_empty" and not data:
                validation_results["is_valid"] = False
                validation_results["errors"].append("Data cannot be empty")

            elif rule == "min_length" and isinstance(data, str):
                min_len = config.get("min_length", 1)
                if len(data) < min_len:
                    validation_results["is_valid"] = False
                    validation_results["errors"].append(
                        f"Data must be at least {min_len} characters"
                    )

            elif rule == "max_length" and isinstance(data, str):
                max_len = config.get("max_length", 1000)
                if len(data) > max_len:
                    validation_results["is_valid"] = False
                    validation_results["errors"].append(
                        f"Data must be no more than {max_len} characters"
                    )

            elif rule == "contains_keywords":
                keywords = config.get("required_keywords", [])
                for keyword in keywords:
                    if keyword.lower() not in str(data).lower():
                        validation_results["warnings"].append(
                            f"Missing recommended keyword: {keyword}"
                        )

        if not validation_results["is_valid"]:
            raise ValueError(
                f"Validation failed: {'; '.join(validation_results['errors'])}"
            )

        self.logger.info(f"Validation step completed successfully")
        return validation_results

    async def data_processing_step(
        self,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        execution_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle generic data processing step.

        Args:
            step_config: Configuration for this step
            input_data: Input data from previous steps
            execution_context: Current execution context

        Returns:
            Processed data
        """
        self.logger.info(
            f"Executing data_processing step: {step_config.get('step_name', 'Unknown')}"
        )

        config = step_config.get("config", {})
        processing_type = config.get("processing_type", "passthrough")

        if processing_type == "passthrough":
            # Simply pass data through
            result = input_data

        elif processing_type == "count_words":
            # Count words in text data
            text = str(input_data.get("data", ""))
            word_count = len(text.split())
            result = {
                "original_data": input_data,
                "word_count": word_count,
                "character_count": len(text),
                "processing_type": processing_type,
            }

        elif processing_type == "extract_metadata":
            # Extract metadata from input
            result = {
                "data": input_data,
                "metadata": {
                    "data_type": type(input_data).__name__,
                    "size": len(str(input_data)),
                    "timestamp": datetime.now().isoformat(),
                    "processing_type": processing_type,
                },
            }

        else:
            # Default processing
            result = {
                "processed_data": input_data,
                "processing_type": processing_type,
                "timestamp": datetime.now().isoformat(),
            }

        self.logger.info(f"Data processing step completed successfully")
        return result


# Global instance for easy access
step_implementations = DeterministicStepImplementations()
