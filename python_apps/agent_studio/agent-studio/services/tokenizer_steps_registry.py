"""
Tokenizer Steps Registry

Registers and provides access to tokenizer-specific step implementations.
These steps are designed for RAG workflows: file reading, text chunking,
embedding generation, and vector storage.
"""

from typing import Dict, Any, Callable, Optional
from fastapi_logger import ElevaiteLogger


class TokenizerStepsRegistry:
    """Registry for tokenizer workflow steps"""

    def __init__(self):
        self.logger = ElevaiteLogger()
        self._step_implementations: Dict[str, Callable] = {}
        self._step_factories: Dict[str, Callable] = {}
        self._register_tokenizer_steps()

    def _register_tokenizer_steps(self):
        """Register all tokenizer step implementations"""
        try:
            # Import step implementations
            from steps.tokenizer.file_reader_step import create_file_reader_step
            from steps.tokenizer.text_chunking_step import create_text_chunking_step
            from steps.tokenizer.embedding_generation_step import (
                create_embedding_generation_step,
            )
            from steps.tokenizer.vector_storage_step import create_vector_storage_step

            # Register factory functions for creating step instances
            self._step_factories["file_reader"] = create_file_reader_step
            self._step_factories["text_chunking"] = create_text_chunking_step
            self._step_factories["embedding_generation"] = (
                create_embedding_generation_step
            )
            self._step_factories["vector_storage"] = create_vector_storage_step

            # Register async step execution functions (compatible with workflow execution context)
            self._step_implementations["file_reader"] = (
                self._create_file_reader_executor()
            )
            self._step_implementations["text_chunking"] = (
                self._create_text_chunking_executor()
            )
            self._step_implementations["embedding_generation"] = (
                self._create_embedding_generation_executor()
            )
            self._step_implementations["vector_storage"] = (
                self._create_vector_storage_executor()
            )

            self.logger.info(
                "Registered tokenizer step implementations: file_reader, text_chunking, embedding_generation, vector_storage"
            )

        except ImportError as e:
            self.logger.warning(f"Could not import tokenizer step implementations: {e}")

    def has_step(self, step_type: str) -> bool:
        """Check if step type is available"""
        return step_type in self._step_implementations

    def get_step_implementation(self, step_type: str) -> Optional[Callable]:
        """Get step implementation by type"""
        return self._step_implementations.get(step_type)

    def get_step_factory(self, step_type: str) -> Optional[Callable]:
        """Get step factory by type"""
        return self._step_factories.get(step_type)

    def list_available_steps(self) -> list:
        """List all available tokenizer step types"""
        return list(self._step_implementations.keys())

    def _create_file_reader_executor(self) -> Callable:
        """Create file reader step executor"""

        async def execute_file_reader_step(
            step_config: Dict[str, Any],
            input_data: Dict[str, Any],
            execution_context: Dict[str, Any],
        ) -> Dict[str, Any]:
            # DEBUG: Log what we're receiving
            self.logger.info("🔍 DEBUG file_reader_step:")
            self.logger.info(f"   step_config: {step_config}")
            self.logger.info(f"   input_data: {input_data}")
            self.logger.info(
                f"   execution_context keys: {list(execution_context.keys())}"
            )

            # Check for uploaded file in execution context
            enhanced_input_data = input_data.copy()

            # If no file_path in config or input, check for uploaded file
            config = step_config.get("config", {})
            self.logger.info(f"   config.file_path: {config.get('file_path')}")
            self.logger.info(
                f"   input_data.file_path: {enhanced_input_data.get('file_path')}"
            )

            if not config.get("file_path") and not enhanced_input_data.get("file_path"):
                # Look for uploaded file in execution context (from runtime_overrides)
                runtime_overrides = execution_context.get("runtime_overrides", {})
                uploaded_file = runtime_overrides.get("uploaded_file", {})

                self.logger.info(f"   runtime_overrides: {runtime_overrides}")
                self.logger.info(f"   uploaded_file: {uploaded_file}")

                if uploaded_file.get("file_path"):
                    # Inject uploaded file path into input data
                    enhanced_input_data["file_path"] = uploaded_file["file_path"]
                    enhanced_input_data["file_name"] = uploaded_file.get(
                        "file_name", "uploaded_file"
                    )

                    self.logger.info(
                        f"🔄 Using uploaded file for file_reader: {uploaded_file['file_path']}"
                    )
                else:
                    self.logger.warning(
                        "❌ No file_path found in config, input_data, or runtime_overrides!"
                    )
            else:
                self.logger.info("✅ Found file_path in config or input_data")

            # Create step instance
            from steps.tokenizer.file_reader_step import create_file_reader_step

            # step_config is already the config dict, not a wrapper
            step = create_file_reader_step(step_config)

            # Execute step with enhanced input data
            result = await step.execute(enhanced_input_data)

            # Convert StepResult to Dict for compatibility
            return {
                "status": result.status.value,
                "data": result.data,
                "error": result.error,
                "progress": result.progress.model_dump() if result.progress else None,
                "metadata": result.metadata,
                "rollback_data": result.rollback_data,
            }

        return execute_file_reader_step

    def _create_text_chunking_executor(self) -> Callable:
        """Create text chunking step executor"""

        async def execute_text_chunking_step(
            step_config: Dict[str, Any],
            input_data: Dict[str, Any],
            _execution_context: Dict[str, Any],
        ) -> Dict[str, Any]:
            # Create step instance
            from steps.tokenizer.text_chunking_step import create_text_chunking_step

            step = create_text_chunking_step(step_config)

            # Execute step
            result = await step.execute(input_data)

            # Convert StepResult to Dict for compatibility
            return {
                "status": result.status.value,
                "data": result.data,
                "error": result.error,
                "progress": result.progress.model_dump() if result.progress else None,
                "metadata": result.metadata,
                "rollback_data": result.rollback_data,
            }

        return execute_text_chunking_step

    def _create_embedding_generation_executor(self) -> Callable:
        """Create embedding generation step executor"""

        async def execute_embedding_generation_step(
            step_config: Dict[str, Any],
            input_data: Dict[str, Any],
            _execution_context: Dict[str, Any],
        ) -> Dict[str, Any]:
            # Create step instance
            from steps.tokenizer.embedding_generation_step import (
                create_embedding_generation_step,
            )

            step = create_embedding_generation_step(step_config)

            # Execute step
            result = await step.execute(input_data)

            # Convert StepResult to Dict for compatibility
            return {
                "status": result.status.value,
                "data": result.data,
                "error": result.error,
                "progress": result.progress.model_dump() if result.progress else None,
                "metadata": result.metadata,
                "rollback_data": result.rollback_data,
            }

        return execute_embedding_generation_step

    def _create_vector_storage_executor(self) -> Callable:
        """Create vector storage step executor"""

        async def execute_vector_storage_step(
            step_config: Dict[str, Any],
            input_data: Dict[str, Any],
            _execution_context: Dict[str, Any],
        ) -> Dict[str, Any]:
            # Create step instance
            from steps.tokenizer.vector_storage_step import create_vector_storage_step

            step = create_vector_storage_step(step_config)

            # Execute step
            result = await step.execute(input_data)

            # Convert StepResult to Dict for compatibility
            return {
                "status": result.status.value,
                "data": result.data,
                "error": result.error,
                "progress": result.progress.model_dump() if result.progress else None,
                "metadata": result.metadata,
                "rollback_data": result.rollback_data,
            }

        return execute_vector_storage_step


# Global instance
tokenizer_steps_registry = TokenizerStepsRegistry()
