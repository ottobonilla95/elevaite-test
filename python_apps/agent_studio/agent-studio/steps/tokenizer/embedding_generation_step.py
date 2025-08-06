"""
Embedding Generation Step for Tokenizer Workflows

Generates vector embeddings for text chunks using various providers:
- OpenAI (text-embedding-ada-002, text-embedding-3-small, text-embedding-3-large)
- Local sentence transformers models
- Custom embedding endpoints

Supports batch processing for efficiency and includes retry logic.
Highly configurable through API parameters.
"""

import os
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
import time

from steps.base_deterministic_step import (
    BaseDeterministicStep,
    StepConfig,
    StepResult,
    StepStatus,
    StepValidationResult,
    BatchProcessingStep,
)
from services.workflow_execution_context import DeterministicStepType
from fastapi_logger import ElevaiteLogger


class EmbeddingGenerationStepConfig(StepConfig):
    """Configuration for Embedding Generation Step"""
    step_type: DeterministicStepType = DeterministicStepType.DATA_PROCESSING
    batch_size: int = 50  # Default batch size for embeddings


class EmbeddingGenerationStep(BatchProcessingStep):
    """
    Generates embeddings for text chunks using various providers.
    
    Supported providers:
    - openai: OpenAI embedding models (text-embedding-ada-002, text-embedding-3-small, etc.)
    - sentence-transformers: Local Hugging Face models
    - custom: Custom API endpoint
    
    Configuration options:
    - provider: Embedding provider (openai, sentence-transformers, custom)
    - model: Model name (e.g., text-embedding-ada-002, all-MiniLM-L6-v2)
    - api_key: API key for provider (if required)
    - api_base: Custom API base URL
    - batch_size: Number of texts to process at once (default: 50)
    - max_retries: Maximum retry attempts (default: 3)
    - retry_delay: Delay between retries in seconds (default: 1)
    - timeout: Request timeout in seconds (default: 30)
    - rate_limit_rpm: Requests per minute limit (default: 3000)
    - dimension: Expected embedding dimension (for validation)
    - normalize: Whether to normalize embeddings (default: False)
    """
    
    def __init__(self, config: EmbeddingGenerationStepConfig):
        super().__init__(config)
        self.logger = ElevaiteLogger()
        self._client = None
        self._local_model = None
        self._request_timestamps = []  # For rate limiting
    
    def validate_config(self) -> StepValidationResult:
        """Validate embedding generation configuration"""
        result = StepValidationResult()
        
        config = self.config.config
        
        # Validate provider
        provider = config.get("provider", "openai")
        valid_providers = ["openai", "sentence-transformers", "custom"]
        if provider not in valid_providers:
            result.errors.append(f"'provider' must be one of: {valid_providers}")
        
        # Validate model
        model = config.get("model")
        if not model:
            result.errors.append("'model' is required")
        
        # Validate API key for OpenAI
        if provider == "openai":
            api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
            if not api_key:
                result.errors.append("OpenAI API key required (config.api_key or OPENAI_API_KEY env var)")
        
        # Validate custom endpoint
        if provider == "custom":
            api_base = config.get("api_base")
            if not api_base:
                result.errors.append("'api_base' is required for custom provider")
        
        # Validate batch size
        batch_size = config.get("batch_size", 50)
        if not isinstance(batch_size, int) or batch_size <= 0:
            result.errors.append("'batch_size' must be a positive integer")
        
        # Validate rate limiting
        rate_limit_rpm = config.get("rate_limit_rpm", 3000)
        if not isinstance(rate_limit_rpm, int) or rate_limit_rpm <= 0:
            result.errors.append("'rate_limit_rpm' must be a positive integer")
        
        # Validate timeout
        timeout = config.get("timeout", 30)
        if not isinstance(timeout, (int, float)) or timeout <= 0:
            result.errors.append("'timeout' must be a positive number")
        
        # Validate dimension (if specified)
        dimension = config.get("dimension")
        if dimension is not None:
            if not isinstance(dimension, int) or dimension <= 0:
                result.errors.append("'dimension' must be a positive integer")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def get_required_inputs(self) -> List[str]:
        """Required inputs for embedding generation step"""
        return ["chunks"]  # Expects chunks from chunking step
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Output schema for embedding generation step"""
        return {
            "type": "object",
            "properties": {
                "embeddings": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "chunk_id": {"type": "string"},
                            "embedding": {
                                "type": "array",
                                "items": {"type": "number"}
                            },
                            "dimension": {"type": "integer"},
                            "model": {"type": "string"},
                            "chunk_text": {"type": "string"},
                            "chunk_metadata": {"type": "object"},
                        }
                    }
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "total_chunks": {"type": "integer"},
                        "successful_embeddings": {"type": "integer"},
                        "failed_embeddings": {"type": "integer"},
                        "provider": {"type": "string"},
                        "model": {"type": "string"},
                        "embedding_dimension": {"type": "integer"},
                        "total_batches": {"type": "integer"},
                        "processing_time_seconds": {"type": "number"},
                        "average_time_per_chunk": {"type": "number"},
                        "processed_at": {"type": "string"},
                    }
                },
                "success": {"type": "boolean"},
                "error": {"type": "string"},
            },
            "required": ["embeddings", "metadata", "success"]
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute embedding generation step"""
        try:
            config = self.config.config
            
            # Get chunks from input
            chunks = input_data.get("chunks", [])
            if not chunks:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="No chunks provided for embedding generation"
                )
            
            start_time = time.time()
            provider = config.get("provider", "openai")
            model = config.get("model", "text-embedding-ada-002")
            
            self.logger.info(f"Generating embeddings for {len(chunks)} chunks using {provider}/{model}")
            
            # Initialize provider
            await self._initialize_provider(config)
            
            # Process chunks in batches
            result = await self.execute_batch(chunks, self._process_embedding_batch)
            
            if result.status != StepStatus.COMPLETED:
                return result
            
            # Extract embeddings and calculate metadata
            all_embeddings = []
            successful_count = 0
            failed_count = 0
            
            for batch_result in result.data["results"]:
                if "embeddings" in batch_result:
                    all_embeddings.extend(batch_result["embeddings"])
                    successful_count += batch_result.get("successful_count", 0)
                    failed_count += batch_result.get("failed_count", 0)
                else:
                    failed_count += batch_result.get("failed_count", len(chunks))
            
            # Calculate processing time
            processing_time = time.time() - start_time
            avg_time_per_chunk = processing_time / len(chunks) if chunks else 0
            
            # Get embedding dimension from first successful embedding
            embedding_dimension = 0
            if all_embeddings:
                embedding_dimension = len(all_embeddings[0]["embedding"])
            
            # Validate dimension if specified
            expected_dimension = config.get("dimension")
            if expected_dimension and embedding_dimension != expected_dimension:
                self.logger.warning(f"Embedding dimension {embedding_dimension} doesn't match expected {expected_dimension}")
            
            result_data = {
                "embeddings": all_embeddings,
                "metadata": {
                    "total_chunks": len(chunks),
                    "successful_embeddings": successful_count,
                    "failed_embeddings": failed_count,
                    "provider": provider,
                    "model": model,
                    "embedding_dimension": embedding_dimension,
                    "total_batches": result.data["summary"]["total_batches"],
                    "processing_time_seconds": round(processing_time, 2),
                    "average_time_per_chunk": round(avg_time_per_chunk, 3),
                    "processed_at": datetime.now().isoformat(),
                },
                "success": True,
            }
            
            self.logger.info(f"Generated {successful_count} embeddings, {failed_count} failed, dimension: {embedding_dimension}")
            
            return StepResult(
                status=StepStatus.COMPLETED,
                data=result_data
            )
            
        except Exception as e:
            self.logger.error(f"Error generating embeddings: {str(e)}")
            return StepResult(
                status=StepStatus.FAILED,
                error=f"Embedding generation error: {str(e)}"
            )
    
    async def _initialize_provider(self, config: Dict[str, Any]):
        """Initialize embedding provider"""
        provider = config.get("provider", "openai")
        
        if provider == "openai":
            await self._initialize_openai(config)
        elif provider == "sentence-transformers":
            await self._initialize_sentence_transformers(config)
        elif provider == "custom":
            await self._initialize_custom(config)
    
    async def _initialize_openai(self, config: Dict[str, Any]):
        """Initialize OpenAI client"""
        try:
            import openai
            
            api_key = config.get("api_key") or os.getenv("OPENAI_API_KEY")
            api_base = config.get("api_base") or "https://api.openai.com/v1"
            
            self._client = openai.AsyncOpenAI(
                api_key=api_key,
                base_url=api_base,
                timeout=config.get("timeout", 30)
            )
            
        except ImportError:
            raise Exception("OpenAI library not installed. Install with: pip install openai")
    
    async def _initialize_sentence_transformers(self, config: Dict[str, Any]):
        """Initialize sentence transformers model"""
        try:
            from sentence_transformers import SentenceTransformer
            import torch
            
            model_name = config.get("model", "all-MiniLM-L6-v2")
            
            # Use GPU if available
            device = "cuda" if torch.cuda.is_available() else "cpu"
            self._local_model = SentenceTransformer(model_name, device=device)
            
            self.logger.info(f"Loaded sentence transformer model: {model_name} on {device}")
            
        except ImportError:
            raise Exception("SentenceTransformers not installed. Install with: pip install sentence-transformers")
    
    async def _initialize_custom(self, config: Dict[str, Any]):
        """Initialize custom API client"""
        import httpx
        
        self._client = httpx.AsyncClient(
            base_url=config.get("api_base"),
            timeout=config.get("timeout", 30)
        )
    
    async def process_batch(self, batch_chunks: List[Any]) -> Dict[str, Any]:
        """Process a batch of chunks - required by BatchProcessingStep"""
        return await self._process_embedding_batch(batch_chunks)
    
    async def _process_embedding_batch(self, batch_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process a batch of chunks for embeddings"""
        config = self.config.config
        provider = config.get("provider", "openai")
        
        # Apply rate limiting
        await self._apply_rate_limiting(config)
        
        if provider == "openai":
            return await self._process_batch_openai(batch_chunks, config)
        elif provider == "sentence-transformers":
            return await self._process_batch_sentence_transformers(batch_chunks, config)
        elif provider == "custom":
            return await self._process_batch_custom(batch_chunks, config)
        else:
            raise Exception(f"Unknown provider: {provider}")
    
    async def _apply_rate_limiting(self, config: Dict[str, Any]):
        """Apply rate limiting to respect API limits"""
        rate_limit_rpm = config.get("rate_limit_rpm", 3000)
        if rate_limit_rpm <= 0:
            return
        
        current_time = time.time()
        
        # Remove timestamps older than 1 minute
        self._request_timestamps = [
            ts for ts in self._request_timestamps
            if current_time - ts < 60
        ]
        
        # If we're at the rate limit, wait
        if len(self._request_timestamps) >= rate_limit_rpm:
            sleep_time = 60 - (current_time - self._request_timestamps[0])
            if sleep_time > 0:
                await asyncio.sleep(sleep_time)
        
        # Record this request
        self._request_timestamps.append(current_time)
    
    async def _process_batch_openai(self, batch_chunks: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process batch using OpenAI API"""
        try:
            model = config.get("model", "text-embedding-ada-002")
            normalize = config.get("normalize", False)
            max_retries = config.get("max_retries", 3)
            retry_delay = config.get("retry_delay", 1)
            
            # Extract text from chunks
            texts = [chunk.get("content", "") for chunk in batch_chunks]
            
            # Retry logic
            for attempt in range(max_retries + 1):
                try:
                    response = await self._client.embeddings.create(
                        model=model,
                        input=texts,
                        encoding_format="float" if not normalize else "float"
                    )
                    
                    # Process response
                    embeddings = []
                    for i, embedding_data in enumerate(response.data):
                        chunk = batch_chunks[i]
                        embedding_vector = embedding_data.embedding
                        
                        # Normalize if requested
                        if normalize:
                            import numpy as np
                            embedding_vector = embedding_vector / np.linalg.norm(embedding_vector)
                            embedding_vector = embedding_vector.tolist()
                        
                        embeddings.append({
                            "chunk_id": chunk.get("id", f"chunk_{i}"),
                            "embedding": embedding_vector,
                            "dimension": len(embedding_vector),
                            "model": model,
                            "chunk_text": chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content", ""),
                            "chunk_metadata": {
                                "size": chunk.get("size", 0),
                                "word_count": chunk.get("word_count", 0),
                                "start_char": chunk.get("start_char", 0),
                                "end_char": chunk.get("end_char", 0),
                            }
                        })
                    
                    return {
                        "embeddings": embeddings,
                        "successful_count": len(embeddings),
                        "failed_count": 0,
                    }
                    
                except Exception as e:
                    if attempt < max_retries:
                        self.logger.warning(f"OpenAI embedding attempt {attempt + 1} failed: {e}, retrying in {retry_delay}s")
                        await asyncio.sleep(retry_delay)
                        continue
                    else:
                        raise e
                        
        except Exception as e:
            self.logger.error(f"OpenAI embedding batch failed: {e}")
            return {
                "embeddings": [],
                "successful_count": 0,
                "failed_count": len(batch_chunks),
                "error": str(e)
            }
    
    async def _process_batch_sentence_transformers(self, batch_chunks: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process batch using sentence transformers"""
        try:
            normalize = config.get("normalize", False)
            
            # Extract text from chunks
            texts = [chunk.get("content", "") for chunk in batch_chunks]
            
            # Generate embeddings (run in thread pool to avoid blocking)
            import asyncio
            import functools
            
            def generate_embeddings():
                return self._local_model.encode(texts, normalize_embeddings=normalize)
            
            # Run in thread pool
            loop = asyncio.get_event_loop()
            embedding_matrix = await loop.run_in_executor(None, generate_embeddings)
            
            # Process results
            embeddings = []
            for i, embedding_vector in enumerate(embedding_matrix):
                chunk = batch_chunks[i]
                
                embeddings.append({
                    "chunk_id": chunk.get("id", f"chunk_{i}"),
                    "embedding": embedding_vector.tolist(),
                    "dimension": len(embedding_vector),
                    "model": config.get("model", "sentence-transformers"),
                    "chunk_text": chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content", ""),
                    "chunk_metadata": {
                        "size": chunk.get("size", 0),
                        "word_count": chunk.get("word_count", 0),
                        "start_char": chunk.get("start_char", 0),
                        "end_char": chunk.get("end_char", 0),
                    }
                })
            
            return {
                "embeddings": embeddings,
                "successful_count": len(embeddings),
                "failed_count": 0,
            }
            
        except Exception as e:
            self.logger.error(f"Sentence transformers batch failed: {e}")
            return {
                "embeddings": [],
                "successful_count": 0,
                "failed_count": len(batch_chunks),
                "error": str(e)
            }
    
    async def _process_batch_custom(self, batch_chunks: List[Dict[str, Any]], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process batch using custom API"""
        try:
            # Extract text from chunks
            texts = [chunk.get("content", "") for chunk in batch_chunks]
            
            # Prepare request
            request_data = {
                "texts": texts,
                "model": config.get("model"),
                "normalize": config.get("normalize", False)
            }
            
            # Add any custom headers
            headers = config.get("headers", {})
            if config.get("api_key"):
                headers["Authorization"] = f"Bearer {config.get('api_key')}"
            
            # Make request
            response = await self._client.post(
                config.get("endpoint", "/embeddings"),
                json=request_data,
                headers=headers
            )
            response.raise_for_status()
            
            # Process response (assuming similar format to OpenAI)
            response_data = response.json()
            embeddings = []
            
            for i, embedding_data in enumerate(response_data.get("embeddings", [])):
                chunk = batch_chunks[i]
                embedding_vector = embedding_data.get("embedding", [])
                
                embeddings.append({
                    "chunk_id": chunk.get("id", f"chunk_{i}"),
                    "embedding": embedding_vector,
                    "dimension": len(embedding_vector),
                    "model": config.get("model"),
                    "chunk_text": chunk.get("content", "")[:200] + "..." if len(chunk.get("content", "")) > 200 else chunk.get("content", ""),
                    "chunk_metadata": {
                        "size": chunk.get("size", 0),
                        "word_count": chunk.get("word_count", 0),
                        "start_char": chunk.get("start_char", 0),
                        "end_char": chunk.get("end_char", 0),
                    }
                })
            
            return {
                "embeddings": embeddings,
                "successful_count": len(embeddings),
                "failed_count": 0,
            }
            
        except Exception as e:
            self.logger.error(f"Custom API batch failed: {e}")
            return {
                "embeddings": [],
                "successful_count": 0,
                "failed_count": len(batch_chunks),
                "error": str(e)
            }


# Factory function for easy creation
def create_embedding_generation_step(config: Dict[str, Any]) -> EmbeddingGenerationStep:
    """Create an EmbeddingGenerationStep with given configuration"""
    step_config = EmbeddingGenerationStepConfig(
        step_name=config.get("step_name", "Embedding Generation"),
        step_type=DeterministicStepType.BATCH_PROCESSING,
        batch_size=config.get("batch_size", 50),
        config=config
    )
    return EmbeddingGenerationStep(step_config)