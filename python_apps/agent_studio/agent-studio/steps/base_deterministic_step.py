"""
Base classes for deterministic workflow steps.

Provides the foundation for all deterministic workflow step implementations,
including configuration validation, progress tracking, error handling,
and data flow management.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable
from enum import Enum
import asyncio
import uuid
from pydantic import BaseModel, Field, validator

from services.workflow_execution_context import DeterministicStepType, ExecutionPattern


class StepStatus(str, Enum):
    """Status of a deterministic workflow step"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class StepValidationResult(BaseModel):
    """Result of step configuration validation"""
    is_valid: bool = True
    errors: List[str] = []
    warnings: List[str] = []


class StepProgressInfo(BaseModel):
    """Progress information for step execution"""
    total_items: int = 0
    processed_items: int = 0
    successful_items: int = 0
    failed_items: int = 0
    current_batch: int = 0
    total_batches: int = 0
    progress_percentage: float = 0.0
    estimated_completion: Optional[datetime] = None
    current_operation: Optional[str] = None


class StepResult(BaseModel):
    """Result of step execution"""
    status: StepStatus
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    progress: Optional[StepProgressInfo] = None
    metadata: Dict[str, Any] = {}
    rollback_data: Optional[Dict[str, Any]] = None


class StepConfig(BaseModel):
    """Base configuration for all deterministic steps"""
    step_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_name: str
    step_type: DeterministicStepType
    
    # Execution configuration
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Dependencies
    dependencies: List[str] = []
    execution_pattern: ExecutionPattern = ExecutionPattern.SEQUENTIAL
    
    # Data flow
    input_mapping: Dict[str, str] = {}  # Map input fields to previous step outputs
    
    # Batch processing
    batch_size: Optional[int] = None
    parallel_batches: bool = False
    
    # Rollback configuration
    rollback_enabled: bool = False
    rollback_config: Optional[Dict[str, Any]] = None
    
    # Step-specific configuration (to be overridden by subclasses)
    config: Dict[str, Any] = {}


class BaseDeterministicStep(ABC):
    """
    Abstract base class for all deterministic workflow steps.
    
    Provides common functionality for:
    - Configuration validation
    - Progress tracking and reporting
    - Error handling and rollback
    - Data input/output management
    - Batch processing support
    """
    
    def __init__(self, config: StepConfig):
        self.config = config
        self.step_id = config.step_id
        self.step_name = config.step_name
        self.step_type = config.step_type
        
        # Runtime state
        self._status = StepStatus.PENDING
        self._start_time: Optional[datetime] = None
        self._end_time: Optional[datetime] = None
        self._progress = StepProgressInfo()
        self._error: Optional[str] = None
        self._result_data: Optional[Dict[str, Any]] = None
        self._rollback_data: Optional[Dict[str, Any]] = None
        
        # Progress callbacks
        self._progress_callbacks: List[Callable[[StepProgressInfo], None]] = []
    
    @property
    def status(self) -> StepStatus:
        return self._status
    
    @property
    def progress(self) -> StepProgressInfo:
        return self._progress
    
    @property
    def duration_ms(self) -> Optional[int]:
        if self._start_time and self._end_time:
            return int((self._end_time - self._start_time).total_seconds() * 1000)
        return None
    
    def add_progress_callback(self, callback: Callable[[StepProgressInfo], None]) -> None:
        """Add a callback to be called when progress is updated"""
        self._progress_callbacks.append(callback)
    
    def _update_progress(self, **kwargs) -> None:
        """Update progress and notify callbacks"""
        for key, value in kwargs.items():
            if hasattr(self._progress, key):
                setattr(self._progress, key, value)
        
        # Calculate progress percentage
        if self._progress.total_items > 0:
            self._progress.progress_percentage = (
                self._progress.processed_items / self._progress.total_items * 100
            )
        
        # Notify callbacks
        for callback in self._progress_callbacks:
            try:
                callback(self._progress)
            except Exception as e:
                # Don't let callback errors break execution
                print(f"Progress callback error: {e}")
    
    @abstractmethod
    def validate_config(self) -> StepValidationResult:
        """
        Validate step configuration.
        
        Returns:
            StepValidationResult with validation errors/warnings
        """
        pass
    
    @abstractmethod
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """
        Execute the step with given input data.
        
        Args:
            input_data: Input data from previous steps and step configuration
            
        Returns:
            StepResult with execution outcome
        """
        pass
    
    async def rollback(self, rollback_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Rollback changes made by this step.
        
        Args:
            rollback_data: Data needed to rollback step changes
            
        Returns:
            True if rollback successful, False otherwise
        """
        if not self.config.rollback_enabled:
            return True  # No rollback needed
        
        try:
            return await self._execute_rollback(rollback_data or self._rollback_data)
        except Exception as e:
            print(f"Rollback failed for step {self.step_name}: {e}")
            return False
    
    async def _execute_rollback(self, rollback_data: Optional[Dict[str, Any]]) -> bool:
        """
        Execute rollback logic. Override in subclasses if rollback is supported.
        
        Args:
            rollback_data: Data needed for rollback
            
        Returns:
            True if rollback successful
        """
        # Default implementation - no rollback logic
        return True
    
    def get_required_inputs(self) -> List[str]:
        """
        Get list of required input fields for this step.
        Override in subclasses to specify required inputs.
        """
        return []
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get schema describing the output data structure.
        Override in subclasses to specify output schema.
        """
        return {}
    
    async def _execute_with_tracking(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute step with status tracking and error handling"""
        self._status = StepStatus.RUNNING
        self._start_time = datetime.now()
        self._error = None
        
        try:
            # Validate inputs
            validation_result = self._validate_inputs(input_data)
            if not validation_result.is_valid:
                raise ValueError(f"Input validation failed: {', '.join(validation_result.errors)}")
            
            # Execute with retry logic
            result = await self._execute_with_retries(input_data)
            
            self._status = StepStatus.COMPLETED
            self._result_data = result.data
            self._rollback_data = result.rollback_data
            
            return result
            
        except Exception as e:
            self._status = StepStatus.FAILED
            self._error = str(e)
            
            return StepResult(
                status=StepStatus.FAILED,
                error=str(e),
                progress=self._progress
            )
        
        finally:
            self._end_time = datetime.now()
    
    async def _execute_with_retries(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute with retry logic"""
        last_error = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                if attempt > 0:
                    # Add retry delay
                    delay = min(2 ** attempt, 30)  # Exponential backoff, max 30 seconds
                    await asyncio.sleep(delay)
                
                return await self.execute(input_data)
                
            except Exception as e:
                last_error = e
                if attempt < self.config.max_retries:
                    print(f"Step {self.step_name} attempt {attempt + 1} failed: {e}, retrying...")
                    continue
                else:
                    raise e
        
        # Should never reach here, but just in case
        raise last_error or Exception("Unknown error during step execution")
    
    def _validate_inputs(self, input_data: Dict[str, Any]) -> StepValidationResult:
        """Validate input data against required inputs"""
        result = StepValidationResult()
        required_inputs = self.get_required_inputs()
        
        for required_field in required_inputs:
            if required_field not in input_data:
                result.errors.append(f"Required input '{required_field}' not provided")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    async def execute_batch(
        self, 
        items: List[Any], 
        batch_processor: Callable[[List[Any]], Dict[str, Any]]
    ) -> StepResult:
        """
        Execute step with batch processing support.
        
        Args:
            items: List of items to process
            batch_processor: Function to process a batch of items
            
        Returns:
            StepResult with aggregated results
        """
        batch_size = self.config.batch_size or len(items)
        total_items = len(items)
        total_batches = (total_items + batch_size - 1) // batch_size
        
        self._update_progress(
            total_items=total_items,
            total_batches=total_batches,
            processed_items=0,
            successful_items=0,
            failed_items=0
        )
        
        results = []
        processed_items = 0
        successful_items = 0
        failed_items = 0
        
        for batch_index in range(total_batches):
            start_idx = batch_index * batch_size
            end_idx = min(start_idx + batch_size, total_items)
            batch_items = items[start_idx:end_idx]
            
            self._update_progress(
                current_batch=batch_index + 1,
                current_operation=f"Processing batch {batch_index + 1}/{total_batches}"
            )
            
            try:
                batch_result = await batch_processor(batch_items)
                results.append(batch_result)
                
                # Update counters
                batch_processed = len(batch_items)
                batch_successful = batch_result.get("successful_count", batch_processed)
                processed_items += batch_processed
                successful_items += batch_successful
                failed_items += (batch_processed - batch_successful)
                
            except Exception as e:
                # Handle batch failure
                batch_processed = len(batch_items)
                processed_items += batch_processed
                failed_items += batch_processed
                
                results.append({
                    "error": str(e),
                    "failed_count": batch_processed
                })
            
            # Update progress
            self._update_progress(
                processed_items=processed_items,
                successful_items=successful_items,
                failed_items=failed_items
            )
        
        return StepResult(
            status=StepStatus.COMPLETED if failed_items == 0 else StepStatus.FAILED,
            data={
                "results": results,
                "summary": {
                    "total_items": total_items,
                    "processed_items": processed_items,
                    "successful_items": successful_items,
                    "failed_items": failed_items,
                    "total_batches": total_batches
                }
            },
            progress=self._progress
        )


class DataInputStep(BaseDeterministicStep):
    """Base class for data input steps (file readers, API clients, etc.)"""
    
    def __init__(self, config: StepConfig):
        super().__init__(config)
        if self.step_type != DeterministicStepType.DATA_INPUT:
            raise ValueError("DataInputStep must have step_type=DATA_INPUT")


class DataOutputStep(BaseDeterministicStep):
    """Base class for data output steps (file writers, database savers, etc.)"""
    
    def __init__(self, config: StepConfig):
        super().__init__(config)
        if self.step_type != DeterministicStepType.DATA_OUTPUT:
            raise ValueError("DataOutputStep must have step_type=DATA_OUTPUT")


class TransformationStep(BaseDeterministicStep):
    """Base class for data transformation steps (processors, converters, etc.)"""
    
    def __init__(self, config: StepConfig):
        super().__init__(config)
        if self.step_type != DeterministicStepType.TRANSFORMATION:
            raise ValueError("TransformationStep must have step_type=TRANSFORMATION")


class ValidationStep(BaseDeterministicStep):
    """Base class for validation steps (data validators, quality checkers, etc.)"""
    
    def __init__(self, config: StepConfig):
        super().__init__(config)
        if self.step_type != DeterministicStepType.VALIDATION:
            raise ValueError("ValidationStep must have step_type=VALIDATION")


class BatchProcessingStep(BaseDeterministicStep):
    """Base class for batch processing steps with built-in batch handling"""
    
    def __init__(self, config: StepConfig):
        super().__init__(config)
        if self.step_type != DeterministicStepType.BATCH_PROCESSING:
            raise ValueError("BatchProcessingStep must have step_type=BATCH_PROCESSING")
        
        # Ensure batch configuration
        if not self.config.batch_size:
            self.config.batch_size = 100
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute with automatic batch processing"""
        items = input_data.get("items", [])
        if not items:
            return StepResult(
                status=StepStatus.COMPLETED,
                data={"message": "No items to process"}
            )
        
        return await self.execute_batch(items, self.process_batch)
    
    @abstractmethod
    async def process_batch(self, batch_items: List[Any]) -> Dict[str, Any]:
        """
        Process a batch of items. Must be implemented by subclasses.
        
        Args:
            batch_items: List of items in this batch
            
        Returns:
            Dictionary with batch processing results
        """
        pass


# Convenience function for creating step instances
def create_step(step_type: DeterministicStepType, config: Dict[str, Any]) -> BaseDeterministicStep:
    """
    Factory function to create step instances.
    
    Args:
        step_type: Type of step to create
        config: Step configuration dictionary
        
    Returns:
        Step instance of appropriate type
    """
    step_config = StepConfig(step_type=step_type, **config)
    
    if step_type == DeterministicStepType.DATA_INPUT:
        return DataInputStep(step_config)
    elif step_type == DeterministicStepType.DATA_OUTPUT:
        return DataOutputStep(step_config)
    elif step_type == DeterministicStepType.TRANSFORMATION:
        return TransformationStep(step_config)
    elif step_type == DeterministicStepType.VALIDATION:
        return ValidationStep(step_config)
    elif step_type == DeterministicStepType.BATCH_PROCESSING:
        return BatchProcessingStep(step_config)
    else:
        # For other step types, return base class
        return BaseDeterministicStep(step_config)