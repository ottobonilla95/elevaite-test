"""
Chunker Factory for Intelligent Chunking Strategy Selection

This module provides a factory for selecting the optimal chunking strategy
based on content type, configuration preferences, and chunker availability.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple

from .semantic_chunker import SemanticChunker
from .mdstructure_chunker import MDStructureChunker
from .sentence_chunker import SentenceChunker

logger = logging.getLogger(__name__)


class ChunkerFactory:
    """Factory for selecting optimal chunking strategy"""
    
    def __init__(self):
        self.chunkers = {}
        self._initialize_chunkers()
    
    def _initialize_chunkers(self):
        """Initialize all available chunkers"""
        # Advanced chunkers
        self.chunkers["semantic"] = SemanticChunker()
        self.chunkers["mdstructure"] = MDStructureChunker()
        self.chunkers["sentence"] = SentenceChunker()
        
        # Legacy chunkers (placeholders for existing implementations)
        self.chunkers["fixed_size"] = LegacyFixedSizeChunker()
        self.chunkers["sliding_window"] = LegacySlidingWindowChunker()
        self.chunkers["paragraph"] = LegacyParagraphChunker()
        
        logger.info(f"Initialized chunkers: {list(self.chunkers.keys())}")
    
    async def get_best_chunker(self, content: str, config: Dict[str, Any]) -> Tuple[Any, str]:
        """Select best chunker based on content and config"""
        
        # Get chunking strategy from config
        strategy = config.get("default_strategy", "sliding_window")
        
        # Auto-select if requested
        if strategy == "auto" or config.get("auto_select_strategy", False):
            return await self._auto_select_chunker(content, config)
        
        # Use specified strategy
        if strategy in self.chunkers:
            chunker = self.chunkers[strategy]
            if chunker.is_available():
                return chunker, strategy
            else:
                logger.warning(f"Requested chunker {strategy} not available, falling back to auto-selection")
                return await self._auto_select_chunker(content, config)
        
        # Fallback to auto-selection
        logger.warning(f"Unknown chunking strategy {strategy}, falling back to auto-selection")
        return await self._auto_select_chunker(content, config)
    
    async def _auto_select_chunker(self, content: str, config: Dict[str, Any]) -> Tuple[Any, str]:
        """Automatically select best chunker based on content characteristics"""
        
        content_length = len(content)
        content_lower = content.lower()
        
        # Analyze content characteristics
        has_markdown = self._detect_markdown(content)
        has_structure = self._detect_structure(content)
        is_technical = self._detect_technical_content(content)
        sentence_count = self._estimate_sentence_count(content)
        
        # Selection logic based on content characteristics
        
        # 1. For markdown content, prefer mdstructure
        if has_markdown and self.chunkers["mdstructure"].is_available():
            logger.info("Auto-selected mdstructure chunker (markdown detected)")
            return self.chunkers["mdstructure"], "mdstructure"
        
        # 2. For highly structured content with good sentence boundaries, use semantic
        if (has_structure and sentence_count >= 10 and 
            self.chunkers["semantic"].is_available() and 
            content_length > 1000):
            logger.info("Auto-selected semantic chunker (structured content with good sentence boundaries)")
            return self.chunkers["semantic"], "semantic"
        
        # 3. For content with clear sentence boundaries, use sentence chunker
        if (sentence_count >= 5 and sentence_count <= 50 and 
            self.chunkers["sentence"].is_available()):
            logger.info("Auto-selected sentence chunker (clear sentence boundaries)")
            return self.chunkers["sentence"], "sentence"
        
        # 4. For very long content, prefer semantic if available
        if (content_length > 5000 and 
            self.chunkers["semantic"].is_available()):
            logger.info("Auto-selected semantic chunker (long content)")
            return self.chunkers["semantic"], "semantic"
        
        # 5. Default to sliding window
        if self.chunkers["sliding_window"].is_available():
            logger.info("Auto-selected sliding_window chunker (default)")
            return self.chunkers["sliding_window"], "sliding_window"
        
        # 6. Final fallback to fixed size
        logger.info("Auto-selected fixed_size chunker (fallback)")
        return self.chunkers["fixed_size"], "fixed_size"
    
    def _detect_markdown(self, content: str) -> bool:
        """Detect if content contains markdown formatting"""
        import re
        
        markdown_patterns = [
            r'^#{1,6}\s+',  # Headers
            r'\*\*[^*]+\*\*',  # Bold
            r'\*[^*]+\*',  # Italic
            r'```[^`]*```',  # Code blocks
            r'`[^`]+`',  # Inline code
            r'\[([^\]]+)\]\([^)]+\)',  # Links
            r'^\s*[-*+]\s+',  # Lists
            r'^\s*\d+\.\s+',  # Numbered lists
            r'\|.*\|',  # Tables
        ]
        
        markdown_score = 0
        for pattern in markdown_patterns:
            if re.search(pattern, content, re.MULTILINE):
                markdown_score += 1
        
        return markdown_score >= 3  # Require multiple markdown elements
    
    def _detect_structure(self, content: str) -> bool:
        """Detect if content has clear structural elements"""
        import re
        
        # Look for structural indicators
        has_headers = bool(re.search(r'^(#{1,6}\s+|\w+:|\d+\.)', content, re.MULTILINE))
        has_paragraphs = len(content.split('\n\n')) > 3
        has_sections = bool(re.search(r'\n\s*\n', content))
        
        return has_headers or (has_paragraphs and has_sections)
    
    def _detect_technical_content(self, content: str) -> bool:
        """Detect if content is technical/academic"""
        technical_indicators = [
            'algorithm', 'function', 'method', 'implementation', 'analysis',
            'research', 'study', 'experiment', 'data', 'results', 'conclusion',
            'abstract', 'introduction', 'methodology', 'discussion'
        ]
        
        content_lower = content.lower()
        technical_score = sum(1 for indicator in technical_indicators if indicator in content_lower)
        
        return technical_score >= 3
    
    def _estimate_sentence_count(self, content: str) -> int:
        """Estimate number of sentences in content"""
        import re
        
        # Simple sentence counting
        sentence_endings = re.findall(r'[.!?]+', content)
        return len(sentence_endings)
    
    def get_available_chunkers(self) -> Dict[str, bool]:
        """Get list of available chunkers"""
        return {name: chunker.is_available() for name, chunker in self.chunkers.items()}
    
    def get_chunker_info(self, chunker_name: str) -> Dict[str, Any]:
        """Get information about a specific chunker"""
        if chunker_name not in self.chunkers:
            return {"available": False, "error": "Chunker not found"}
        
        chunker = self.chunkers[chunker_name]
        
        return {
            "available": chunker.is_available(),
            "name": chunker_name,
            "description": getattr(chunker, "description", f"{chunker_name} chunker"),
            "best_for": self._get_chunker_best_use_cases(chunker_name)
        }
    
    def _get_chunker_best_use_cases(self, chunker_name: str) -> List[str]:
        """Get best use cases for each chunker"""
        use_cases = {
            "semantic": [
                "Long documents with varied topics",
                "Academic papers and research",
                "Technical documentation",
                "Content requiring topic coherence"
            ],
            "mdstructure": [
                "Markdown documents",
                "Documentation with headers",
                "Structured content with sections",
                "README files and wikis"
            ],
            "sentence": [
                "Content with clear sentence boundaries",
                "Narrative text and stories",
                "News articles",
                "Conversational content"
            ],
            "sliding_window": [
                "General purpose chunking",
                "Consistent chunk sizes needed",
                "Simple content without structure",
                "Default choice for most content"
            ],
            "fixed_size": [
                "Character-based size requirements",
                "Simple text processing",
                "Performance-critical applications",
                "Uniform chunk sizes required"
            ],
            "paragraph": [
                "Content with clear paragraph structure",
                "Preserving natural breaks",
                "Informal text and blogs",
                "Content with topic changes per paragraph"
            ]
        }
        
        return use_cases.get(chunker_name, ["General text processing"])


# Legacy chunker placeholders (these would delegate to existing implementations)

class LegacyFixedSizeChunker:
    """Wrapper for existing fixed size chunker"""
    
    def is_available(self) -> bool:
        return True
    
    async def chunk_fixed_size(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fixed size chunking (placeholder - would call existing implementation)"""
        chunk_size = config.get("chunk_size", 1000)
        chunks = []
        
        for i in range(0, len(content), chunk_size):
            chunk_text = content[i:i + chunk_size]
            chunk = {
                "id": f"fixed_chunk_{len(chunks)}",
                "content": chunk_text,
                "start_char": i,
                "end_char": i + len(chunk_text),
                "size": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "chunk_method": "fixed_size"
            }
            chunks.append(chunk)
        
        return chunks


class LegacySlidingWindowChunker:
    """Wrapper for existing sliding window chunker"""
    
    def is_available(self) -> bool:
        return True
    
    async def chunk_sliding_window(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Sliding window chunking (placeholder - would call existing implementation)"""
        chunk_size = config.get("chunk_size", 1000)
        overlap = config.get("overlap", 0.2)
        step_size = int(chunk_size * (1 - overlap))
        
        chunks = []
        
        for i in range(0, len(content), step_size):
            chunk_text = content[i:i + chunk_size]
            if not chunk_text.strip():
                break
                
            chunk = {
                "id": f"sliding_chunk_{len(chunks)}",
                "content": chunk_text,
                "start_char": i,
                "end_char": i + len(chunk_text),
                "size": len(chunk_text),
                "word_count": len(chunk_text.split()),
                "overlap_ratio": overlap,
                "chunk_method": "sliding_window"
            }
            chunks.append(chunk)
        
        return chunks


class LegacyParagraphChunker:
    """Wrapper for existing paragraph chunker"""
    
    def is_available(self) -> bool:
        return True
    
    async def chunk_paragraph(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Paragraph-based chunking (placeholder - would call existing implementation)"""
        max_chunk_size = config.get("max_chunk_size", 2000)
        
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = ""
        char_offset = 0
        
        for paragraph in paragraphs:
            potential_chunk = current_chunk
            if potential_chunk:
                potential_chunk += "\n\n" + paragraph
            else:
                potential_chunk = paragraph
            
            if len(potential_chunk) > max_chunk_size and current_chunk:
                # Create chunk
                chunk = {
                    "id": f"paragraph_chunk_{len(chunks)}",
                    "content": current_chunk.strip(),
                    "start_char": char_offset,
                    "end_char": char_offset + len(current_chunk),
                    "size": len(current_chunk),
                    "word_count": len(current_chunk.split()),
                    "chunk_method": "paragraph"
                }
                chunks.append(chunk)
                
                # Start new chunk
                char_offset += len(current_chunk) + 2
                current_chunk = paragraph
            else:
                current_chunk = potential_chunk
        
        # Add final chunk
        if current_chunk.strip():
            chunk = {
                "id": f"paragraph_chunk_{len(chunks)}",
                "content": current_chunk.strip(),
                "start_char": char_offset,
                "end_char": char_offset + len(current_chunk),
                "size": len(current_chunk),
                "word_count": len(current_chunk.split()),
                "chunk_method": "paragraph"
            }
            chunks.append(chunk)
        
        return chunks
