"""
Text Chunking Step for Tokenizer Workflows

Chunks text using various strategies leveraging the existing TextChunker infrastructure:
- Semantic chunking (using sentence embeddings and clustering)
- Fixed size chunking
- Sliding window chunking with overlap
- Sentence-based chunking
- Paragraph-based chunking

Highly configurable through API parameters.
"""

import sys
import os
from typing import Dict, Any, List, Optional
from datetime import datetime

# Add path to access existing TextChunker
sys.path.append('/home/johnbelly/work/elevaite/python_apps/arlo_backend')

from steps.base_deterministic_step import (
    BaseDeterministicStep,
    StepConfig,
    StepResult,
    StepStatus,
    StepValidationResult,
    TransformationStep,
)
from services.workflow_execution_context import DeterministicStepType
from fastapi_logger import ElevaiteLogger


class TextChunkingStepConfig(StepConfig):
    """Configuration for Text Chunking Step"""
    step_type: DeterministicStepType = DeterministicStepType.TRANSFORMATION


class TextChunkingStep(TransformationStep):
    """
    Chunks text using various strategies via the existing TextChunker class.
    
    Chunking strategies available:
    - semantic: Groups semantically similar sentences using embeddings
    - fixed_size: Fixed character-based chunks
    - sliding_window: Overlapping chunks with configurable overlap
    - sentence: Split by sentence boundaries
    - paragraph: Split by paragraph boundaries
    
    Configuration options:
    - chunk_strategy: Strategy to use (semantic, fixed_size, sliding_window, sentence, paragraph)
    - chunk_size: Size for fixed_size and sliding_window strategies (default: 1000)
    - overlap: Overlap fraction for sliding_window (0.0-1.0, default: 0.2)
    - n_clusters: Number of clusters for semantic chunking (default: 5)
    - semantic_model: Model for semantic chunking (default: 'paraphrase-MiniLM-L6-v2')
    - min_chunk_size: Minimum chunk size to keep (default: 50)
    - max_chunk_size: Maximum chunk size allowed (default: 4000)
    - preserve_structure: Whether to respect paragraph boundaries (default: True)
    """
    
    def __init__(self, config: TextChunkingStepConfig):
        super().__init__(config)
        self.logger = ElevaiteLogger()
        self._text_chunker = None
    
    def _get_text_chunker(self):
        """Lazy load TextChunker to avoid import issues during initialization"""
        if self._text_chunker is None:
            try:
                from arlo_modules.components.chunking.textchunker import TextChunker
                config = self.config.config
                semantic_model = config.get('semantic_model', 'paraphrase-MiniLM-L6-v2')
                self._text_chunker = TextChunker(semantic_model=semantic_model)
            except ImportError as e:
                self.logger.error(f"Could not import TextChunker: {e}")
                raise Exception(f"TextChunker not available: {e}")
        return self._text_chunker
    
    def validate_config(self) -> StepValidationResult:
        """Validate text chunking configuration"""
        result = StepValidationResult()
        
        config = self.config.config
        
        # Validate chunk strategy
        chunk_strategy = config.get("chunk_strategy", "sliding_window")
        valid_strategies = ["semantic", "fixed_size", "sliding_window", "sentence", "paragraph"]
        if chunk_strategy not in valid_strategies:
            result.errors.append(f"'chunk_strategy' must be one of: {valid_strategies}")
        
        # Validate chunk size
        chunk_size = config.get("chunk_size", 1000)
        if not isinstance(chunk_size, int) or chunk_size <= 0:
            result.errors.append("'chunk_size' must be a positive integer")
        
        # Validate overlap for sliding window
        if chunk_strategy == "sliding_window":
            overlap = config.get("overlap", 0.2)
            if not isinstance(overlap, (int, float)) or overlap < 0 or overlap >= 1:
                result.errors.append("'overlap' must be a number between 0.0 and 1.0")
        
        # Validate n_clusters for semantic chunking
        if chunk_strategy == "semantic":
            n_clusters = config.get("n_clusters", 5)
            if not isinstance(n_clusters, int) or n_clusters <= 0:
                result.errors.append("'n_clusters' must be a positive integer")
        
        # Validate size limits
        min_chunk_size = config.get("min_chunk_size", 50)
        max_chunk_size = config.get("max_chunk_size", 4000)
        if not isinstance(min_chunk_size, int) or min_chunk_size <= 0:
            result.errors.append("'min_chunk_size' must be a positive integer")
        if not isinstance(max_chunk_size, int) or max_chunk_size <= min_chunk_size:
            result.errors.append("'max_chunk_size' must be greater than 'min_chunk_size'")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def get_required_inputs(self) -> List[str]:
        """Required inputs for text chunking step"""
        return ["content"]  # Expects text content from previous step
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Output schema for text chunking step"""
        return {
            "type": "object",
            "properties": {
                "chunks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "content": {"type": "string"},
                            "start_char": {"type": "integer"},
                            "end_char": {"type": "integer"},
                            "size": {"type": "integer"},
                            "word_count": {"type": "integer"},
                            "cluster_id": {"type": "integer"},  # For semantic chunking
                        }
                    }
                },
                "metadata": {
                    "type": "object",
                    "properties": {
                        "original_length": {"type": "integer"},
                        "total_chunks": {"type": "integer"},
                        "chunk_strategy": {"type": "string"},
                        "average_chunk_size": {"type": "number"},
                        "min_chunk_size": {"type": "integer"},
                        "max_chunk_size": {"type": "integer"},
                        "overlap_used": {"type": "number"},
                        "processed_at": {"type": "string"},
                    }
                },
                "success": {"type": "boolean"},
                "error": {"type": "string"},
            },
            "required": ["chunks", "metadata", "success"]
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute text chunking step"""
        try:
            config = self.config.config
            
            # Get text content from input
            content = input_data.get("content", "")
            if not content:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="No text content provided for chunking"
                )
            
            if not isinstance(content, str):
                content = str(content)
            
            original_length = len(content)
            chunk_strategy = config.get("chunk_strategy", "sliding_window")
            
            self._update_progress(
                current_operation=f"Chunking text using {chunk_strategy} strategy",
                total_items=1,
                processed_items=0
            )
            
            # Execute chunking based on strategy
            chunks_text = []
            
            if chunk_strategy == "semantic":
                chunks_text = await self._chunk_semantic(content, config)
            elif chunk_strategy == "fixed_size":
                chunks_text = await self._chunk_fixed_size(content, config)
            elif chunk_strategy == "sliding_window":
                chunks_text = await self._chunk_sliding_window(content, config)
            elif chunk_strategy == "sentence":
                chunks_text = await self._chunk_sentence(content, config)
            elif chunk_strategy == "paragraph":
                chunks_text = await self._chunk_paragraph(content, config)
            else:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"Unknown chunk strategy: {chunk_strategy}"
                )
            
            # Filter chunks by size if configured
            min_chunk_size = config.get("min_chunk_size", 50)
            max_chunk_size = config.get("max_chunk_size", 4000)
            
            filtered_chunks = []
            for chunk_text in chunks_text:
                chunk_size = len(chunk_text)
                if min_chunk_size <= chunk_size <= max_chunk_size:
                    filtered_chunks.append(chunk_text)
            
            # Create chunk objects with metadata
            chunks = []
            current_pos = 0
            
            for i, chunk_text in enumerate(filtered_chunks):
                chunk_size = len(chunk_text)
                word_count = len(chunk_text.split())
                
                # Find position in original text (approximate)
                start_char = content.find(chunk_text[:100], current_pos) if len(chunk_text) > 100 else content.find(chunk_text, current_pos)
                if start_char == -1:
                    start_char = current_pos
                end_char = start_char + chunk_size
                current_pos = end_char
                
                chunk_obj = {
                    "id": f"chunk_{i:04d}",
                    "content": chunk_text,
                    "start_char": start_char,
                    "end_char": end_char,
                    "size": chunk_size,
                    "word_count": word_count,
                }
                
                # Add cluster_id for semantic chunking
                if chunk_strategy == "semantic":
                    chunk_obj["cluster_id"] = i % config.get("n_clusters", 5)
                
                chunks.append(chunk_obj)
            
            # Calculate metadata
            chunk_sizes = [chunk["size"] for chunk in chunks]
            avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            min_actual_size = min(chunk_sizes) if chunk_sizes else 0
            max_actual_size = max(chunk_sizes) if chunk_sizes else 0
            
            overlap_used = config.get("overlap", 0.0) if chunk_strategy == "sliding_window" else 0.0
            
            result_data = {
                "chunks": chunks,
                "metadata": {
                    "original_length": original_length,
                    "total_chunks": len(chunks),
                    "chunk_strategy": chunk_strategy,
                    "average_chunk_size": round(avg_chunk_size, 2),
                    "min_chunk_size": min_actual_size,
                    "max_chunk_size": max_actual_size,
                    "overlap_used": overlap_used,
                    "processed_at": datetime.now().isoformat(),
                },
                "success": True,
            }
            
            self._update_progress(
                processed_items=1,
                total_items=1,
                progress_percentage=100
            )
            
            self.logger.info(f"Successfully chunked text: {original_length} chars -> {len(chunks)} chunks (avg: {avg_chunk_size:.0f} chars)")
            
            return StepResult(
                status=StepStatus.COMPLETED,
                data=result_data
            )
            
        except Exception as e:
            self.logger.error(f"Error chunking text: {str(e)}")
            return StepResult(
                status=StepStatus.FAILED,
                error=f"Text chunking error: {str(e)}"
            )
    
    async def _chunk_semantic(self, content: str, config: Dict[str, Any]) -> List[str]:
        """Chunk text semantically using TextChunker"""
        try:
            text_chunker = self._get_text_chunker()
            n_clusters = config.get("n_clusters", 5)
            
            chunks = text_chunker.semantic_chunk(content, n_clusters=n_clusters)
            return chunks
        except Exception as e:
            self.logger.warning(f"Semantic chunking failed, falling back to sentence chunking: {e}")
            # Fallback to sentence chunking if semantic fails
            return await self._chunk_sentence(content, config)
    
    async def _chunk_fixed_size(self, content: str, config: Dict[str, Any]) -> List[str]:
        """Chunk text with fixed size using TextChunker"""
        try:
            text_chunker = self._get_text_chunker()
            chunk_size = config.get("chunk_size", 1000)
            
            chunks = text_chunker.fixed_size_chunk(content, chunk_size=chunk_size)
            return chunks
        except Exception as e:
            # Simple fallback implementation
            chunk_size = config.get("chunk_size", 1000)
            chunks = []
            for i in range(0, len(content), chunk_size):
                chunks.append(content[i:i + chunk_size])
            return chunks
    
    async def _chunk_sliding_window(self, content: str, config: Dict[str, Any]) -> List[str]:
        """Chunk text with sliding window using TextChunker"""
        try:
            text_chunker = self._get_text_chunker()
            chunk_size = config.get("chunk_size", 1000)
            overlap = config.get("overlap", 0.2)
            
            chunks = text_chunker.sliding_window_chunk(content, window_size=chunk_size, overlap=overlap)
            return chunks
        except Exception as e:
            # Simple fallback implementation
            chunk_size = config.get("chunk_size", 1000)
            overlap = config.get("overlap", 0.2)
            step = int(chunk_size * (1 - overlap))
            
            chunks = []
            for i in range(0, len(content) - chunk_size + 1, step):
                chunks.append(content[i:i + chunk_size])
            
            # Add final chunk if needed
            if len(content) % step != 0:
                chunks.append(content[-chunk_size:])
            
            return chunks
    
    async def _chunk_sentence(self, content: str, config: Dict[str, Any]) -> List[str]:
        """Chunk text by sentences using TextChunker"""
        try:
            text_chunker = self._get_text_chunker()
            chunks = text_chunker.sentence_chunk(content)
            return chunks
        except Exception as e:
            # Simple fallback using basic sentence splitting
            import re
            sentences = re.split(r'[.!?]+', content)
            return [sent.strip() for sent in sentences if sent.strip()]
    
    async def _chunk_paragraph(self, content: str, config: Dict[str, Any]) -> List[str]:
        """Chunk text by paragraphs using TextChunker"""
        try:
            text_chunker = self._get_text_chunker()
            chunks = text_chunker.paragraph_chunk(content)
            return chunks
        except Exception as e:
            # Simple fallback using paragraph splitting
            paragraphs = content.split('\n\n')
            return [para.strip() for para in paragraphs if para.strip()]


# Factory function for easy creation
def create_text_chunking_step(config: Dict[str, Any]) -> TextChunkingStep:
    """Create a TextChunkingStep with given configuration"""
    step_config = TextChunkingStepConfig(
        step_name=config.get("step_name", "Text Chunking"),
        config=config
    )
    return TextChunkingStep(step_config)