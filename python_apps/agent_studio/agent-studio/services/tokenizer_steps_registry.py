"""
Tokenizer Steps Registry

Registers and provides access to tokenizer-specific step implementations.
These steps are designed for RAG workflows: file reading, text chunking,
embedding generation, and vector storage.
"""

from typing import Dict, Any, Callable
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
            from steps.tokenizer.embedding_generation_step import create_embedding_generation_step
            from steps.tokenizer.vector_storage_step import create_vector_storage_step
            
            # Register factory functions for creating step instances
            self._step_factories["file_reader"] = create_file_reader_step
            self._step_factories["text_chunking"] = create_text_chunking_step
            self._step_factories["embedding_generation"] = create_embedding_generation_step
            self._step_factories["vector_storage"] = create_vector_storage_step
            
            # Register async step execution functions (compatible with workflow execution context)
            self._step_implementations["file_reader"] = self._create_file_reader_executor()
            self._step_implementations["text_chunking"] = self._create_text_chunking_executor()
            self._step_implementations["embedding_generation"] = self._create_embedding_generation_executor()
            self._step_implementations["vector_storage"] = self._create_vector_storage_executor()
            
            self.logger.info("Registered tokenizer step implementations: file_reader, text_chunking, embedding_generation, vector_storage")
            
        except ImportError as e:
            self.logger.warning(f"Could not import tokenizer step implementations: {e}")
    
    def get_step_implementation(self, step_type: str) -> Callable:
        """Get step implementation by type"""
        return self._step_implementations.get(step_type)
    
    def get_step_factory(self, step_type: str) -> Callable:
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
            execution_context: Dict[str, Any]
        ) -> Dict[str, Any]:
            # Create step instance
            from steps.tokenizer.file_reader_step import create_file_reader_step
            step = create_file_reader_step(step_config.get("config", {}))
            
            # Execute step
            result = await step.execute(input_data)
            
            # Return result data
            if result.status.value == "completed":
                return result.data
            else:
                raise Exception(result.error or "File reader step failed")
        
        return execute_file_reader_step
    
    def _create_text_chunking_executor(self) -> Callable:
        """Create text chunking step executor"""
        async def execute_text_chunking_step(
            step_config: Dict[str, Any],
            input_data: Dict[str, Any],
            execution_context: Dict[str, Any]
        ) -> Dict[str, Any]:
            # Create step instance
            from steps.tokenizer.text_chunking_step import create_text_chunking_step
            step = create_text_chunking_step(step_config.get("config", {}))
            
            # Execute step
            result = await step.execute(input_data)
            
            # Return result data
            if result.status.value == "completed":
                return result.data
            else:
                raise Exception(result.error or "Text chunking step failed")
        
        return execute_text_chunking_step
    
    def _create_embedding_generation_executor(self) -> Callable:
        """Create embedding generation step executor"""
        async def execute_embedding_generation_step(
            step_config: Dict[str, Any],
            input_data: Dict[str, Any],
            execution_context: Dict[str, Any]
        ) -> Dict[str, Any]:
            # Create step instance
            from steps.tokenizer.embedding_generation_step import create_embedding_generation_step
            step = create_embedding_generation_step(step_config.get("config", {}))
            
            # Execute step
            result = await step.execute(input_data)
            
            # Return result data
            if result.status.value == "completed":
                return result.data
            else:
                raise Exception(result.error or "Embedding generation step failed")
        
        return execute_embedding_generation_step
    
    def _create_vector_storage_executor(self) -> Callable:
        """Create vector storage step executor"""
        async def execute_vector_storage_step(
            step_config: Dict[str, Any],
            input_data: Dict[str, Any],
            execution_context: Dict[str, Any]
        ) -> Dict[str, Any]:
            # Create step instance
            from steps.tokenizer.vector_storage_step import create_vector_storage_step
            step = create_vector_storage_step(step_config.get("config", {}))
            
            # Execute step
            result = await step.execute(input_data)
            
            # Return result data
            if result.status.value == "completed":
                return result.data
            else:
                raise Exception(result.error or "Vector storage step failed")
        
        return execute_vector_storage_step


# Global instance
tokenizer_steps_registry = TokenizerStepsRegistry()