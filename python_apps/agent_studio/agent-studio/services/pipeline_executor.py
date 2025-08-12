"""
Pipeline Executor Service for Agent Studio

This service orchestrates the execution of document processing pipelines using
the steps-based architecture. It replaces the direct elevaite_ingestion calls
with a modular, configurable approach.
"""

import logging
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from steps.base_deterministic_step import StepResult, StepStatus
from services.dynamic_config_manager import config_manager, PipelineConfig
from services.tokenizer_steps_registry import TokenizerStepsRegistry


logger = logging.getLogger(__name__)


@dataclass
class PipelineExecutionContext:
    """Context for pipeline execution"""

    pipeline_id: str
    config: PipelineConfig
    file_paths: List[str]
    temp_directory: str
    progress_callback: Optional[Callable[[str, str, str], None]] = None
    metadata: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class PipelineExecutionResult:
    """Result of pipeline execution"""

    pipeline_id: str
    status: str
    message: str
    steps_completed: List[str]
    total_steps: int
    results: Dict[str, Any]
    error: Optional[str] = None


class PipelineExecutor:
    """
    Orchestrates the execution of document processing pipelines using
    the steps-based architecture.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.steps_registry = TokenizerStepsRegistry()

        # Define the standard pipeline stages
        self.standard_stages = [
            ("load", "file_reader"),
            ("parse", "file_reader"),  # File reader handles parsing
            ("chunk", "text_chunking"),
            ("embed", "embedding_generation"),
            ("store", "vector_storage"),
        ]

    async def execute_pipeline(
        self,
        pipeline_id: str,
        steps_config: List[Dict[str, Any]],
        file_ids: List[str],
        progress_callback: Optional[Callable[[str, str, str], None]] = None,
    ) -> PipelineExecutionResult:
        """
        Execute a complete document processing pipeline.

        Args:
            pipeline_id: Unique identifier for this pipeline execution
            steps_config: List of step configurations from API request
            file_ids: List of file IDs to process
            progress_callback: Optional callback for progress updates

        Returns:
            PipelineExecutionResult with execution outcome
        """
        try:
            # Create configuration from steps
            config = config_manager.create_config_from_steps(steps_config)

            # Validate configuration
            validation_errors = config_manager.validate_config(config)
            if validation_errors:
                return PipelineExecutionResult(
                    pipeline_id=pipeline_id,
                    status="failed",
                    message=f"Configuration validation failed: {'; '.join(validation_errors)}",
                    steps_completed=[],
                    total_steps=len(self.standard_stages),
                    results={},
                    error=f"Validation errors: {validation_errors}",
                )

            # Get file paths from file IDs
            file_paths = await self._resolve_file_paths(file_ids)
            if not file_paths:
                return PipelineExecutionResult(
                    pipeline_id=pipeline_id,
                    status="failed",
                    message="No valid file paths found",
                    steps_completed=[],
                    total_steps=len(self.standard_stages),
                    results={},
                    error="No files to process",
                )

            # Create temporary directory for processing
            with tempfile.TemporaryDirectory() as temp_dir:
                # Create execution context
                context = PipelineExecutionContext(
                    pipeline_id=pipeline_id,
                    config=config,
                    file_paths=file_paths,
                    temp_directory=temp_dir,
                    progress_callback=progress_callback,
                )

                # Execute pipeline stages
                return await self._execute_stages(context, steps_config)

        except Exception as e:
            self.logger.error(f"Pipeline execution failed: {str(e)}", exc_info=True)
            return PipelineExecutionResult(
                pipeline_id=pipeline_id,
                status="failed",
                message=f"Pipeline execution failed: {str(e)}",
                steps_completed=[],
                total_steps=len(self.standard_stages),
                results={},
                error=str(e),
            )

    async def _execute_stages(
        self, context: PipelineExecutionContext, steps_config: List[Dict[str, Any]]
    ) -> PipelineExecutionResult:
        """Execute all pipeline stages in sequence"""
        steps_completed = []
        pipeline_data = {"files": context.file_paths}

        try:
            for stage_name, step_type in self.standard_stages:
                self.logger.info(f"Executing stage: {stage_name}")

                # Notify progress start
                if context.progress_callback:
                    context.progress_callback(
                        context.pipeline_id, stage_name, "started"
                    )

                # Find step configuration for this stage
                step_config = self._find_step_config(steps_config, stage_name)

                # Execute the step
                result = await self._execute_step(
                    step_type, step_config, pipeline_data, context
                )

                if result.status != StepStatus.COMPLETED:
                    # Step failed
                    if context.progress_callback:
                        context.progress_callback(
                            context.pipeline_id, stage_name, "failed"
                        )

                    return PipelineExecutionResult(
                        pipeline_id=context.pipeline_id,
                        status="failed",
                        message=f"Stage {stage_name} failed: {result.error}",
                        steps_completed=steps_completed,
                        total_steps=len(self.standard_stages),
                        results={"pipeline_data": pipeline_data},
                        error=result.error,
                    )

                # Step completed successfully
                steps_completed.append(stage_name)
                pipeline_data.update(result.data or {})

                # Notify progress completion
                if context.progress_callback:
                    context.progress_callback(
                        context.pipeline_id, stage_name, "completed"
                    )

                self.logger.info(f"Stage {stage_name} completed successfully")

            # All stages completed
            return PipelineExecutionResult(
                pipeline_id=context.pipeline_id,
                status="completed",
                message="Pipeline execution completed successfully",
                steps_completed=steps_completed,
                total_steps=len(self.standard_stages),
                results={"pipeline_data": pipeline_data},
            )

        except Exception as e:
            self.logger.error(f"Stage execution failed: {str(e)}", exc_info=True)
            return PipelineExecutionResult(
                pipeline_id=context.pipeline_id,
                status="failed",
                message=f"Stage execution failed: {str(e)}",
                steps_completed=steps_completed,
                total_steps=len(self.standard_stages),
                results={"pipeline_data": pipeline_data},
                error=str(e),
            )

    def _find_step_config(
        self, steps_config: List[Dict[str, Any]], stage_name: str
    ) -> Dict[str, Any]:
        """Find step configuration for a given stage"""
        for step in steps_config:
            if step.get("step_type") == stage_name:
                return step.get("config", {})
        return {}

    async def _execute_step(
        self,
        step_type: str,
        step_config: Dict[str, Any],
        input_data: Dict[str, Any],
        context: PipelineExecutionContext,
    ) -> StepResult:
        """Execute a single pipeline step"""
        try:
            # Get step executor from registry
            if not self.steps_registry.has_step(step_type):
                raise ValueError(f"Unknown step type: {step_type}")

            step_executor = self.steps_registry.get_step_implementation(step_type)
            if step_executor is None:
                raise ValueError(f"No implementation found for step type: {step_type}")

            # Prepare execution context for the step
            execution_context = {
                "pipeline_id": context.pipeline_id,
                "temp_directory": context.temp_directory,
                "config": context.config.to_dict(),
                "metadata": context.metadata,
            }

            # For file_reader step, add file paths to step config
            if step_type == "file_reader" and context.file_paths:
                step_config = step_config.copy()
                step_config["file_path"] = context.file_paths[
                    0
                ]  # Use first file for now
                step_config["file_paths"] = context.file_paths

            # Execute the step
            result = await step_executor(step_config, input_data, execution_context)

            # Convert dictionary result to StepResult if needed (for compatibility with tokenizer steps)
            if isinstance(result, dict):
                # Convert dict back to StepResult
                status = StepStatus(result.get("status", "failed"))
                step_result = StepResult(
                    status=status,
                    data=result.get("data"),
                    error=result.get("error"),
                    metadata=result.get("metadata"),
                    rollback_data=result.get("rollback_data"),
                )
                return step_result

            return result

        except Exception as e:
            self.logger.error(
                f"Step {step_type} execution failed: {str(e)}", exc_info=True
            )
            return StepResult(
                status=StepStatus.FAILED, error=f"Step execution failed: {str(e)}"
            )

    async def _resolve_file_paths(self, file_ids: List[str]) -> List[str]:
        """
        Resolve file IDs to actual file paths.
        Since files are not stored in database, we need to check the file system and S3.
        """
        import os
        import boto3
        from botocore.exceptions import ClientError

        file_paths = []

        for file_id in file_ids:
            # First check if it's already a valid path
            if Path(file_id).exists():
                file_paths.append(file_id)
                self.logger.info(f"File ID {file_id} is already a valid local path")
                continue

            # Check if it's an S3 URL
            if file_id.startswith("s3://"):
                file_paths.append(file_id)
                self.logger.info(f"File ID {file_id} is already an S3 URL")
                continue

            # Try to find the file in local upload directories
            upload_dirs = [
                "/tmp/uploads",
                "./uploads",
                "/app/uploads",
                os.path.expanduser("~/uploads"),
            ]

            found_local = False
            for upload_dir in upload_dirs:
                if not os.path.exists(upload_dir):
                    continue

                # Look for files that start with the file_id
                for filename in os.listdir(upload_dir):
                    if filename.startswith(file_id):
                        local_path = os.path.join(upload_dir, filename)
                        if os.path.isfile(local_path):
                            file_paths.append(local_path)
                            self.logger.info(
                                f"Resolved file ID {file_id} to local path: {local_path}"
                            )
                            found_local = True
                            break

                if found_local:
                    break

            if found_local:
                continue

            # Try to find the file in S3 (check default bucket)
            try:
                s3_client = boto3.client("s3")
                bucket_name = os.getenv("S3_BUCKET_NAME", "kb-check-pdf")

                # Try different possible S3 keys
                possible_s3_keys = [
                    f"{file_id}.pdf",
                    f"{file_id}.txt",
                    f"{file_id}.docx",
                    f"{file_id}.doc",
                    f"{file_id}.md",
                    file_id,  # Maybe it's already the full key
                ]

                found_s3 = False
                for s3_key in possible_s3_keys:
                    try:
                        # Check if object exists in S3
                        s3_client.head_object(Bucket=bucket_name, Key=s3_key)
                        s3_url = f"s3://{bucket_name}/{s3_key}"
                        file_paths.append(s3_url)
                        self.logger.info(
                            f"Resolved file ID {file_id} to S3 path: {s3_url}"
                        )
                        found_s3 = True
                        break
                    except ClientError as e:
                        if e.response["Error"]["Code"] != "404":
                            self.logger.warning(f"S3 error checking {s3_key}: {e}")
                        continue

                if found_s3:
                    continue

            except Exception as e:
                self.logger.warning(f"Could not check S3 for file {file_id}: {e}")

            # If we get here, we couldn't resolve the file ID
            self.logger.warning(f"Could not resolve file ID: {file_id}")

        return file_paths


# Global instance
pipeline_executor = PipelineExecutor()
