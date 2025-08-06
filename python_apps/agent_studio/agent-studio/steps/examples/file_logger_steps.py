"""
File Logger Workflow Example Steps

Simple deterministic workflow example for testing the framework.
Demonstrates input, transformation, validation, batch processing, and output steps.

Workflow: Accept log messages → Format → Validate → Batch → Write to files
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

from steps.base_deterministic_step import (
    BaseDeterministicStep, DataInputStep, TransformationStep, 
    ValidationStep, BatchProcessingStep, DataOutputStep,
    StepConfig, StepResult, StepStatus, StepValidationResult,
    DeterministicStepType
)


class LogMessageInputConfig(StepConfig):
    """Configuration for log message input step"""
    step_type: DeterministicStepType = DeterministicStepType.DATA_INPUT
    
    # Input configuration
    max_messages: int = 1000
    default_level: str = "INFO"
    source_name: str = "system"


class LogMessageInputStep(DataInputStep):
    """
    Accept log messages for processing.
    
    Input: List of log messages or single message
    Output: Standardized list of log message dictionaries
    """
    
    def validate_config(self) -> StepValidationResult:
        result = StepValidationResult()
        
        config = self.config.config
        if config.get("max_messages", 1000) <= 0:
            result.errors.append("max_messages must be positive")
        
        valid_levels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
        default_level = config.get("default_level", "INFO")
        if default_level not in valid_levels:
            result.errors.append(f"default_level must be one of {valid_levels}")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def get_required_inputs(self) -> List[str]:
        return ["messages"]
    
    def get_output_schema(self) -> Dict[str, Any]:
        return {
            "messages": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "timestamp": {"type": "string"},
                        "level": {"type": "string"},
                        "message": {"type": "string"},
                        "source": {"type": "string"},
                        "metadata": {"type": "object"}
                    }
                }
            },
            "total_count": {"type": "integer"}
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        config = self.config.config
        max_messages = config.get("max_messages", 1000)
        default_level = config.get("default_level", "INFO")
        source_name = config.get("source_name", "system")
        
        raw_messages = input_data.get("messages", [])
        
        # Handle single message
        if isinstance(raw_messages, str):
            raw_messages = [raw_messages]
        elif isinstance(raw_messages, dict):
            raw_messages = [raw_messages]
        
        # Limit message count
        if len(raw_messages) > max_messages:
            raw_messages = raw_messages[:max_messages]
        
        processed_messages = []
        
        for i, raw_message in enumerate(raw_messages):
            if isinstance(raw_message, str):
                # Simple string message
                processed_message = {
                    "id": f"msg_{i}_{datetime.now().timestamp()}",
                    "timestamp": datetime.now().isoformat(),
                    "level": default_level,
                    "message": raw_message,
                    "source": source_name,
                    "metadata": {}
                }
            elif isinstance(raw_message, dict):
                # Structured message
                processed_message = {
                    "id": raw_message.get("id", f"msg_{i}_{datetime.now().timestamp()}"),
                    "timestamp": raw_message.get("timestamp", datetime.now().isoformat()),
                    "level": raw_message.get("level", default_level),
                    "message": raw_message.get("message", ""),
                    "source": raw_message.get("source", source_name),
                    "metadata": raw_message.get("metadata", {})
                }
            else:
                # Convert to string
                processed_message = {
                    "id": f"msg_{i}_{datetime.now().timestamp()}",
                    "timestamp": datetime.now().isoformat(),
                    "level": default_level,
                    "message": str(raw_message),
                    "source": source_name,
                    "metadata": {}
                }
            
            processed_messages.append(processed_message)
        
        return StepResult(
            status=StepStatus.COMPLETED,
            data={
                "messages": processed_messages,
                "total_count": len(processed_messages)
            },
            metadata={
                "input_count": len(raw_messages),
                "processed_count": len(processed_messages)
            }
        )


class LogFormatterStep(TransformationStep):
    """
    Format log messages into specified output format.
    
    Input: List of standardized log messages
    Output: List of formatted log messages
    """
    
    def validate_config(self) -> StepValidationResult:
        result = StepValidationResult()
        
        config = self.config.config
        format_type = config.get("format", "json")
        valid_formats = ["json", "text", "csv"]
        
        if format_type not in valid_formats:
            result.errors.append(f"format must be one of {valid_formats}")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def get_required_inputs(self) -> List[str]:
        return ["messages"]
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        config = self.config.config
        format_type = config.get("format", "json")
        include_metadata = config.get("include_metadata", True)
        
        messages = input_data.get("messages", [])
        formatted_messages = []
        
        for message in messages:
            if format_type == "json":
                # JSON format
                formatted_data = message.copy()
                if not include_metadata:
                    formatted_data.pop("metadata", None)
                formatted_message = json.dumps(formatted_data)
                
            elif format_type == "text":
                # Text format: [timestamp] LEVEL source: message
                timestamp = message.get("timestamp", "")
                level = message.get("level", "INFO")
                source = message.get("source", "")
                msg_text = message.get("message", "")
                
                formatted_message = f"[{timestamp}] {level} {source}: {msg_text}"
                
                if include_metadata and message.get("metadata"):
                    metadata_str = json.dumps(message["metadata"])
                    formatted_message += f" | {metadata_str}"
                    
            elif format_type == "csv":
                # CSV format
                timestamp = message.get("timestamp", "").replace(",", ";")
                level = message.get("level", "INFO")
                source = message.get("source", "").replace(",", ";")
                msg_text = message.get("message", "").replace(",", ";")
                metadata_str = json.dumps(message.get("metadata", {})).replace(",", ";") if include_metadata else ""
                
                formatted_message = f"{timestamp},{level},{source},{msg_text},{metadata_str}"
            
            formatted_messages.append({
                "id": message.get("id"),
                "original": message,
                "formatted": formatted_message
            })
        
        return StepResult(
            status=StepStatus.COMPLETED,
            data={
                "formatted_messages": formatted_messages,
                "format_type": format_type,
                "total_count": len(formatted_messages)
            }
        )


class LogValidatorStep(ValidationStep):
    """
    Validate log messages for quality and consistency.
    
    Input: List of formatted log messages
    Output: List of valid messages (invalid ones filtered out)
    """
    
    def validate_config(self) -> StepValidationResult:
        result = StepValidationResult()
        
        config = self.config.config
        max_message_length = config.get("max_message_length", 10000)
        
        if max_message_length <= 0:
            result.errors.append("max_message_length must be positive")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        config = self.config.config
        max_message_length = config.get("max_message_length", 10000)
        required_fields = config.get("required_fields", ["id", "timestamp", "message"])
        allowed_levels = config.get("allowed_levels", ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"])
        
        formatted_messages = input_data.get("formatted_messages", [])
        valid_messages = []
        invalid_messages = []
        
        for msg_data in formatted_messages:
            original = msg_data.get("original", {})
            formatted = msg_data.get("formatted", "")
            
            is_valid = True
            validation_errors = []
            
            # Check required fields
            for field in required_fields:
                if not original.get(field):
                    is_valid = False
                    validation_errors.append(f"Missing required field: {field}")
            
            # Check message length
            if len(formatted) > max_message_length:
                is_valid = False
                validation_errors.append(f"Message too long: {len(formatted)} > {max_message_length}")
            
            # Check log level
            level = original.get("level", "")
            if level not in allowed_levels:
                is_valid = False
                validation_errors.append(f"Invalid log level: {level}")
            
            # Check timestamp format (basic check)
            timestamp = original.get("timestamp", "")
            try:
                datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                is_valid = False
                validation_errors.append(f"Invalid timestamp format: {timestamp}")
            
            if is_valid:
                valid_messages.append(msg_data)
            else:
                invalid_messages.append({
                    **msg_data,
                    "validation_errors": validation_errors
                })
        
        return StepResult(
            status=StepStatus.COMPLETED,
            data={
                "valid_messages": valid_messages,
                "invalid_messages": invalid_messages,
                "valid_count": len(valid_messages),
                "invalid_count": len(invalid_messages),
                "total_count": len(formatted_messages)
            }
        )


class LogBatchProcessorStep(BatchProcessingStep):
    """
    Group log messages into batches for efficient file writing.
    
    Input: List of valid formatted messages
    Output: Batched messages ready for writing
    """
    
    def validate_config(self) -> StepValidationResult:
        """Validate batch processor configuration"""
        result = StepValidationResult()
        config = self.config.config
        
        if config.get("batch_size", 10) <= 0:
            result.errors.append("batch_size must be positive")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    async def process_batch(self, batch_items: List[Any]) -> Dict[str, Any]:
        """Process a batch of log messages"""
        config = self.config.config
        batch_id = f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        
        # Group by log level if configured
        group_by_level = config.get("group_by_level", False)
        
        if group_by_level:
            level_groups = {}
            for item in batch_items:
                original = item.get("original", {})
                level = original.get("level", "INFO")
                if level not in level_groups:
                    level_groups[level] = []
                level_groups[level].append(item)
            
            return {
                "batch_id": batch_id,
                "batch_size": len(batch_items),
                "level_groups": level_groups,
                "successful_count": len(batch_items)
            }
        else:
            return {
                "batch_id": batch_id,
                "batch_size": len(batch_items),
                "messages": batch_items,
                "successful_count": len(batch_items)
            }


class LogFileWriterStep(DataOutputStep):
    """
    Write log messages to files with rotation support.
    
    Input: Batched log messages
    Output: File writing results
    """
    
    def validate_config(self) -> StepValidationResult:
        result = StepValidationResult()
        
        config = self.config.config
        output_directory = config.get("output_directory")
        
        if not output_directory:
            result.errors.append("output_directory is required")
        elif not isinstance(output_directory, str):
            result.errors.append("output_directory must be a string")
        
        max_file_size = config.get("max_file_size_mb", 10)
        if max_file_size <= 0:
            result.errors.append("max_file_size_mb must be positive")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        config = self.config.config
        output_directory = config.get("output_directory")
        max_file_size_mb = config.get("max_file_size_mb", 10)
        file_prefix = config.get("file_prefix", "log")
        
        # Ensure output directory exists
        Path(output_directory).mkdir(parents=True, exist_ok=True)
        
        results = input_data.get("results", [])
        files_written = []
        total_messages = 0
        
        for batch_result in results:
            if "level_groups" in batch_result:
                # Process level groups
                for level, messages in batch_result["level_groups"].items():
                    filename = f"{file_prefix}_{level.lower()}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                    filepath = Path(output_directory) / filename
                    
                    written_count = await self._write_messages_to_file(
                        filepath, messages, max_file_size_mb
                    )
                    
                    files_written.append({
                        "filepath": str(filepath),
                        "level": level,
                        "messages_written": written_count
                    })
                    total_messages += written_count
            else:
                # Process all messages together
                messages = batch_result.get("messages", [])
                filename = f"{file_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
                filepath = Path(output_directory) / filename
                
                written_count = await self._write_messages_to_file(
                    filepath, messages, max_file_size_mb
                )
                
                files_written.append({
                    "filepath": str(filepath),
                    "messages_written": written_count
                })
                total_messages += written_count
        
        return StepResult(
            status=StepStatus.COMPLETED,
            data={
                "files_written": files_written,
                "total_messages": total_messages,
                "output_directory": output_directory
            },
            rollback_data={
                "files_to_delete": [f["filepath"] for f in files_written]
            }
        )
    
    async def _write_messages_to_file(
        self, 
        filepath: Path, 
        messages: List[Dict[str, Any]], 
        max_file_size_mb: int
    ) -> int:
        """Write messages to a file with size rotation"""
        max_file_size_bytes = max_file_size_mb * 1024 * 1024
        written_count = 0
        current_file_index = 1
        current_filepath = filepath
        
        # Check if we need to rotate files
        while current_filepath.exists() and current_filepath.stat().st_size >= max_file_size_bytes:
            current_file_index += 1
            name_parts = filepath.stem.split('.')
            current_filepath = filepath.parent / f"{name_parts[0]}_{current_file_index:03d}.{filepath.suffix}"
        
        with open(current_filepath, "a", encoding="utf-8") as f:
            for msg_data in messages:
                formatted_message = msg_data.get("formatted", "")
                f.write(formatted_message + "\n")
                written_count += 1
                
                # Check file size and rotate if needed
                if f.tell() >= max_file_size_bytes:
                    f.close()
                    current_file_index += 1
                    name_parts = filepath.stem.split('.')
                    current_filepath = filepath.parent / f"{name_parts[0]}_{current_file_index:03d}.{filepath.suffix}"
                    f = open(current_filepath, "w", encoding="utf-8")
        
        return written_count
    
    async def _execute_rollback(self, rollback_data: Optional[Dict[str, Any]]) -> bool:
        """Delete files that were created during execution"""
        if not rollback_data or "files_to_delete" not in rollback_data:
            return True
        
        files_to_delete = rollback_data["files_to_delete"]
        success = True
        
        for filepath in files_to_delete:
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                print(f"Failed to delete file {filepath}: {e}")
                success = False
        
        return success