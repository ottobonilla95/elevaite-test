"""
Enhanced Text Chunking Step for Tokenizer Workflows

Chunks text using various strategies with support for both simple and advanced modes:

Simple Mode (backward compatible):
- Semantic chunking (using existing TextChunker)
- Fixed size chunking
- Sliding window chunking with overlap
- Sentence-based chunking
- Paragraph-based chunking

Advanced Mode (enhanced capabilities):
- Semantic chunking with breakpoint detection
- MDStructure chunking for markdown content
- Enhanced sentence chunking with spaCy support
- Intelligent strategy auto-selection
- Structured content preservation

Highly configurable through API parameters with automatic strategy selection.
"""

import sys
from typing import Dict, Any, List
from datetime import datetime

# Add path to access existing TextChunker
sys.path.append("/home/johnbelly/work/elevaite/python_apps/arlo_backend")

from steps.base_deterministic_step import (
    StepConfig,
    StepResult,
    StepStatus,
    StepValidationResult,
    TransformationStep,
)
from services.workflow_execution_context import DeterministicStepType
from fastapi_logger import ElevaiteLogger

# Enhanced configuration and chunker imports
from .enhanced_config import ExecutionMode
from .config_migrator import ConfigDetector, ConfigMigrator
from .chunkers.chunker_factory import ChunkerFactory


class TextChunkingStepConfig(StepConfig):
    """Configuration for Text Chunking Step"""

    step_type: DeterministicStepType = DeterministicStepType.TRANSFORMATION


class TextChunkingStep(TransformationStep):
    """
    Enhanced text chunking step that supports both simple and advanced modes.

    Simple Mode (backward compatible):
    - semantic: Groups semantically similar sentences using existing TextChunker
    - fixed_size: Fixed character-based chunks
    - sliding_window: Overlapping chunks with configurable overlap
    - sentence: Split by sentence boundaries
    - paragraph: Split by paragraph boundaries

    Advanced Mode (enhanced capabilities):
    - semantic_chunking: Advanced semantic chunking with breakpoint detection
    - mdstructure: Markdown structure-aware chunking
    - sentence_chunking: Enhanced sentence chunking with spaCy support
    - auto: Intelligent strategy auto-selection based on content

    Configuration options:
    - execution_mode: 'simple', 'advanced', or 'elevaite_direct'
    - chunk_strategy: Strategy to use (varies by mode)
    - chunk_size: Size for size-based strategies (default: 1000)
    - overlap: Overlap fraction for sliding_window (0.0-1.0, default: 0.2)
    - advanced_chunking: Advanced chunking configuration (advanced mode)
    - min_chunk_size: Minimum chunk size to keep (default: 50)
    - max_chunk_size: Maximum chunk size allowed (default: 4000)
    - preserve_structure: Whether to respect boundaries (default: True)
    """

    def __init__(self, config: TextChunkingStepConfig):
        super().__init__(config)
        self.logger = ElevaiteLogger()
        self._text_chunker = None

        # Initialize chunker factory for advanced mode
        self.chunker_factory = ChunkerFactory()

        # Detect and migrate configuration
        self.enhanced_config = self._prepare_enhanced_config(config.config)

    def _prepare_enhanced_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare enhanced configuration from input config"""
        try:
            # Detect execution mode
            execution_mode = ConfigDetector.detect_mode(config)

            # Migrate to enhanced format if needed
            if execution_mode == ExecutionMode.ELEVAITE_DIRECT:
                enhanced_config = ConfigMigrator.from_elevaite_config(config)
                return enhanced_config.dict()
            elif execution_mode == ExecutionMode.SIMPLE:
                enhanced_config = ConfigMigrator.from_simple_config(config)
                return enhanced_config.dict()
            else:
                # Already in enhanced format
                return config

        except Exception as e:
            self.logger.warning(f"Config migration failed, using simple mode: {e}")
            return {"execution_mode": ExecutionMode.SIMPLE, "simple_config": config}

    def _get_execution_mode(self) -> ExecutionMode:
        """Get the execution mode from enhanced config"""
        mode_str = self.enhanced_config.get("execution_mode", "simple")
        try:
            return ExecutionMode(mode_str)
        except ValueError:
            return ExecutionMode.SIMPLE

    def _get_text_chunker(self):
        """Lazy load TextChunker to avoid import issues during initialization"""
        if self._text_chunker is None:
            try:
                from arlo_modules.components.chunking.textchunker import TextChunker

                config = self.config.config
                semantic_model = config.get("semantic_model", "paraphrase-MiniLM-L6-v2")
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
        valid_strategies = [
            "semantic",
            "fixed_size",
            "sliding_window",
            "sentence",
            "paragraph",
        ]
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
            result.errors.append(
                "'max_chunk_size' must be greater than 'min_chunk_size'"
            )

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
                        },
                    },
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
                    },
                },
                "success": {"type": "boolean"},
                "error": {"type": "string"},
            },
            "required": ["chunks", "metadata", "success"],
        }

    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute text chunking step with support for both simple and advanced modes"""
        try:
            # Determine execution mode
            execution_mode = self._get_execution_mode()

            self.logger.info(f"Executing TextChunkingStep in {execution_mode} mode")

            # Route to appropriate execution method
            if execution_mode == ExecutionMode.ADVANCED:
                return await self._execute_advanced_mode(input_data)
            elif execution_mode == ExecutionMode.ELEVAITE_DIRECT:
                return await self._execute_elevaite_mode(input_data)
            else:
                return await self._execute_simple_mode(input_data)

        except Exception as e:
            self.logger.error(f"Error in TextChunkingStep execution: {str(e)}")
            return StepResult(
                status=StepStatus.FAILED, error=f"Text chunking error: {str(e)}"
            )

    async def _execute_simple_mode(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute text chunking in simple mode (backward compatible)"""
        try:
            config = self.config.config

            # Get text content from input
            content = input_data.get("content", "")
            if not content:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="No text content provided for chunking",
                )

            if not isinstance(content, str):
                content = str(content)

            original_length = len(content)
            chunk_strategy = config.get("chunk_strategy", "sliding_window")

            self._update_progress(
                current_operation=f"Chunking text using {chunk_strategy} strategy",
                total_items=1,
                processed_items=0,
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
                    error=f"Unknown chunk strategy: {chunk_strategy}",
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
                start_char = (
                    content.find(chunk_text[:100], current_pos)
                    if len(chunk_text) > 100
                    else content.find(chunk_text, current_pos)
                )
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

            overlap_used = (
                config.get("overlap", 0.0)
                if chunk_strategy == "sliding_window"
                else 0.0
            )

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
                processed_items=1, total_items=1, progress_percentage=100
            )

            self.logger.info(
                f"Successfully chunked text: {original_length} chars -> {len(chunks)} chunks (avg: {avg_chunk_size:.0f} chars)"
            )

            return StepResult(status=StepStatus.COMPLETED, data=result_data)

        except Exception as e:
            self.logger.error(f"Error chunking text: {str(e)}")
            return StepResult(
                status=StepStatus.FAILED, error=f"Text chunking error: {str(e)}"
            )

    async def _execute_advanced_mode(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute text chunking in advanced mode with intelligent strategy selection"""
        try:
            # Get text content from input
            content = input_data.get("content", "")
            if not content:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="No text content provided for chunking",
                )

            if not isinstance(content, str):
                content = str(content)

            original_length = len(content)

            # Get the best chunker for this content
            chunker, strategy_name = await self.chunker_factory.get_best_chunker(
                content, self.enhanced_config
            )

            self.logger.info(f"Using {strategy_name} chunker for advanced mode")

            # Update progress
            self._update_progress(
                current_operation=f"Chunking text using {strategy_name} strategy (advanced)",
                total_items=1,
                processed_items=0,
            )

            # Execute chunking with the selected strategy
            if strategy_name == "semantic":
                chunks = await chunker.chunk_semantic(
                    content, self.enhanced_config.get("advanced_chunking", {})
                )
            elif strategy_name == "mdstructure":
                chunks = await chunker.chunk_mdstructure(
                    content, self.enhanced_config.get("advanced_chunking", {})
                )
            elif strategy_name == "sentence":
                chunks = await chunker.chunk_sentence(
                    content, self.enhanced_config.get("advanced_chunking", {})
                )
            elif strategy_name in ["fixed_size", "sliding_window", "paragraph"]:
                # Use legacy chunkers for these strategies
                method_name = f"chunk_{strategy_name}"
                if hasattr(chunker, method_name):
                    chunks = await getattr(chunker, method_name)(
                        content, self.enhanced_config.get("advanced_chunking", {})
                    )
                else:
                    # Fallback to simple mode for these strategies
                    return await self._execute_simple_mode(input_data)
            else:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"Unknown advanced chunking strategy: {strategy_name}",
                )

            if not chunks:
                return StepResult(
                    status=StepStatus.FAILED, error="Chunking produced no results"
                )

            # Enhance metadata with advanced information
            chunk_sizes = [chunk["size"] for chunk in chunks]
            avg_chunk_size = sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0
            min_actual_size = min(chunk_sizes) if chunk_sizes else 0
            max_actual_size = max(chunk_sizes) if chunk_sizes else 0

            # Calculate advanced metrics
            advanced_metrics = self._calculate_advanced_metrics(chunks, strategy_name)

            result_data = {
                "chunks": chunks,
                "metadata": {
                    "original_length": original_length,
                    "total_chunks": len(chunks),
                    "chunk_strategy": strategy_name,
                    "average_chunk_size": round(avg_chunk_size, 2),
                    "min_chunk_size": min_actual_size,
                    "max_chunk_size": max_actual_size,
                    "execution_mode": "advanced",
                    "chunker_used": strategy_name,
                    "processed_at": datetime.now().isoformat(),
                    **advanced_metrics,
                },
                "success": True,
            }

            self._update_progress(
                processed_items=1, total_items=1, progress_percentage=100
            )

            self.logger.info(
                f"Successfully chunked text with {strategy_name}: {original_length} chars -> {len(chunks)} chunks (avg: {avg_chunk_size:.0f} chars)"
            )

            return StepResult(status=StepStatus.COMPLETED, data=result_data)

        except Exception as e:
            self.logger.error(f"Error in advanced mode text chunking: {str(e)}")
            return StepResult(
                status=StepStatus.FAILED,
                error=f"Advanced text chunking error: {str(e)}",
            )

    async def _execute_elevaite_mode(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute text chunking in elevaite_ingestion compatibility mode"""
        # For now, delegate to advanced mode with elevaite-style config
        return await self._execute_advanced_mode(input_data)

    def _calculate_advanced_metrics(
        self, chunks: List[Dict[str, Any]], strategy_name: str
    ) -> Dict[str, Any]:
        """Calculate advanced metrics for chunked content"""
        metrics = {}

        # Strategy-specific metrics
        if strategy_name == "semantic":
            semantic_scores = [chunk.get("semantic_score", 0.0) for chunk in chunks]
            if semantic_scores:
                metrics["avg_semantic_score"] = sum(semantic_scores) / len(
                    semantic_scores
                )
                metrics["min_semantic_score"] = min(semantic_scores)
                metrics["max_semantic_score"] = max(semantic_scores)

        elif strategy_name == "mdstructure":
            header_counts = [len(chunk.get("headers", [])) for chunk in chunks]
            structure_levels = [chunk.get("structure_level", 0) for chunk in chunks]
            if header_counts:
                metrics["avg_headers_per_chunk"] = sum(header_counts) / len(
                    header_counts
                )
                metrics["max_structure_level"] = (
                    max(structure_levels) if structure_levels else 0
                )

        elif strategy_name == "sentence":
            sentence_counts = [chunk.get("sentence_count", 0) for chunk in chunks]
            confidences = [
                chunk.get("avg_sentence_confidence", 0.0) for chunk in chunks
            ]
            if sentence_counts:
                metrics["avg_sentences_per_chunk"] = sum(sentence_counts) / len(
                    sentence_counts
                )
                metrics["total_sentences"] = sum(sentence_counts)
            if confidences:
                metrics["avg_sentence_confidence"] = sum(confidences) / len(confidences)

        # General advanced metrics
        word_counts = [chunk.get("word_count", 0) for chunk in chunks]
        if word_counts:
            metrics["total_words"] = sum(word_counts)
            metrics["avg_words_per_chunk"] = sum(word_counts) / len(word_counts)

        # Chunk distribution analysis
        chunk_sizes = [chunk["size"] for chunk in chunks]
        if len(chunk_sizes) > 1:
            import statistics

            metrics["chunk_size_std_dev"] = statistics.stdev(chunk_sizes)
            metrics["chunk_size_variance"] = statistics.variance(chunk_sizes)

        return metrics

    async def _chunk_semantic(self, content: str, config: Dict[str, Any]) -> List[str]:
        """Chunk text semantically using TextChunker"""
        try:
            text_chunker = self._get_text_chunker()
            n_clusters = config.get("n_clusters", 5)

            chunks = text_chunker.semantic_chunk(content, n_clusters=n_clusters)
            return chunks
        except Exception as e:
            self.logger.warning(
                f"Semantic chunking failed, falling back to sentence chunking: {e}"
            )
            # Fallback to sentence chunking if semantic fails
            return await self._chunk_sentence(content, config)

    async def _chunk_fixed_size(
        self, content: str, config: Dict[str, Any]
    ) -> List[str]:
        """Chunk text with fixed size using TextChunker"""
        try:
            text_chunker = self._get_text_chunker()
            chunk_size = config.get("chunk_size", 1000)

            chunks = text_chunker.fixed_size_chunk(content, chunk_size=chunk_size)
            return chunks
        except Exception:
            # Simple fallback implementation
            chunk_size = config.get("chunk_size", 1000)
            chunks = []
            for i in range(0, len(content), chunk_size):
                chunks.append(content[i : i + chunk_size])
            return chunks

    async def _chunk_sliding_window(
        self, content: str, config: Dict[str, Any]
    ) -> List[str]:
        """Chunk text with sliding window using TextChunker"""
        try:
            text_chunker = self._get_text_chunker()
            chunk_size = config.get("chunk_size", 1000)
            overlap = config.get("overlap", 0.2)

            chunks = text_chunker.sliding_window_chunk(
                content, window_size=chunk_size, overlap=overlap
            )
            return chunks
        except Exception:
            # Simple fallback implementation
            chunk_size = config.get("chunk_size", 1000)
            overlap = config.get("overlap", 0.2)
            step = int(chunk_size * (1 - overlap))

            chunks = []
            for i in range(0, len(content) - chunk_size + 1, step):
                chunks.append(content[i : i + chunk_size])

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
        except Exception:
            # Simple fallback using basic sentence splitting
            import re

            sentences = re.split(r"[.!?]+", content)
            return [sent.strip() for sent in sentences if sent.strip()]

    async def _chunk_paragraph(self, content: str, config: Dict[str, Any]) -> List[str]:
        """Chunk text by paragraphs using TextChunker"""
        try:
            text_chunker = self._get_text_chunker()
            chunks = text_chunker.paragraph_chunk(content)
            return chunks
        except Exception:
            # Simple fallback using paragraph splitting
            paragraphs = content.split("\n\n")
            return [para.strip() for para in paragraphs if para.strip()]


# Factory function for easy creation
def create_text_chunking_step(config: Dict[str, Any]) -> TextChunkingStep:
    """Create a TextChunkingStep with given configuration"""
    step_config = TextChunkingStepConfig(
        step_name=config.get("step_name", "Text Chunking"), config=config
    )
    return TextChunkingStep(step_config)
