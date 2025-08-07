"""
Semantic Chunker for Advanced Text Processing

This module implements semantic chunking using sentence embeddings and similarity
analysis to create chunks based on semantic coherence rather than just size.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
import asyncio
import time
import re

logger = logging.getLogger(__name__)


class SemanticChunker:
    """Semantic chunking using sentence embeddings and breakpoint detection"""
    
    def __init__(self):
        self.model = None
        self.available = False
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize sentence transformer model"""
        try:
            from sentence_transformers import SentenceTransformer
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            # Use a lightweight model for fast processing
            self.model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
            self.np = np
            self.cosine_similarity = cosine_similarity
            self.available = True
            logger.info("Semantic chunker initialized successfully")
            
        except ImportError as e:
            self.available = False
            logger.warning(f"Semantic chunker not available: {e}. Install with: pip install sentence-transformers scikit-learn")
        except Exception as e:
            self.available = False
            logger.error(f"Failed to initialize semantic chunker: {e}")
    
    async def chunk_semantic(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform semantic chunking with breakpoint detection"""
        if not self.available:
            raise Exception("Semantic chunking not available. Please install sentence-transformers and scikit-learn.")
        
        start_time = time.time()
        
        try:
            # Configuration
            breakpoint_threshold_type = config.get("breakpoint_threshold_type", "percentile")
            breakpoint_threshold_amount = config.get("breakpoint_threshold_amount", 85)
            max_chunk_size = config.get("max_chunk_size", 1500)
            min_chunk_size = config.get("min_chunk_size", 100)
            
            # Split into sentences
            sentences = self._split_sentences(content)
            
            if len(sentences) <= 1:
                # Not enough sentences for semantic analysis
                return self._create_single_chunk(content, 0)
            
            # Generate embeddings in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(None, self._generate_embeddings, sentences)
            
            # Find semantic breakpoints
            breakpoints = self._find_breakpoints(
                embeddings, 
                threshold_type=breakpoint_threshold_type,
                threshold_amount=breakpoint_threshold_amount
            )
            
            # Create chunks based on breakpoints
            chunks = self._create_chunks_from_breakpoints(
                sentences, 
                breakpoints, 
                max_chunk_size=max_chunk_size,
                min_chunk_size=min_chunk_size
            )
            
            processing_time = time.time() - start_time
            
            # Add metadata to chunks
            for i, chunk in enumerate(chunks):
                chunk.update({
                    "semantic_score": chunk.get("semantic_score", 0.0),
                    "processing_time": processing_time / len(chunks),
                    "chunk_method": "semantic_breakpoint"
                })
            
            logger.info(f"Semantic chunking completed: {len(chunks)} chunks in {processing_time:.2f}s")
            return chunks
            
        except Exception as e:
            logger.error(f"Semantic chunking failed: {e}")
            # Fallback to simple sentence-based chunking
            return self._fallback_chunking(content, config)
    
    def _split_sentences(self, content: str) -> List[str]:
        """Split content into sentences using regex"""
        # Simple sentence splitting - could be enhanced with spaCy or NLTK
        sentence_pattern = r'(?<=[.!?])\s+'
        sentences = re.split(sentence_pattern, content.strip())
        
        # Clean up sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def _generate_embeddings(self, sentences: List[str]) -> List[List[float]]:
        """Generate embeddings for sentences (runs in thread pool)"""
        embeddings = self.model.encode(sentences)
        return embeddings.tolist()
    
    def _find_breakpoints(self, embeddings: List[List[float]], threshold_type: str, threshold_amount: float) -> List[int]:
        """Find semantic breakpoints using similarity analysis"""
        if len(embeddings) <= 1:
            return []
        
        # Calculate similarities between consecutive sentences
        similarities = []
        for i in range(len(embeddings) - 1):
            sim = self.cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
            similarities.append(sim)
        
        # Find breakpoints based on threshold
        if threshold_type == "percentile":
            threshold = self.np.percentile(similarities, 100 - threshold_amount)
        elif threshold_type == "standard_deviation":
            mean_sim = self.np.mean(similarities)
            std_sim = self.np.std(similarities)
            threshold = mean_sim - (threshold_amount / 100) * std_sim
        else:
            threshold = threshold_amount
        
        # Find indices where similarity drops below threshold
        breakpoints = [i + 1 for i, sim in enumerate(similarities) if sim < threshold]
        
        # Always include the end
        if breakpoints and breakpoints[-1] != len(embeddings):
            breakpoints.append(len(embeddings))
        elif not breakpoints:
            breakpoints = [len(embeddings)]
        
        return breakpoints
    
    def _create_chunks_from_breakpoints(self, sentences: List[str], breakpoints: List[int], 
                                      max_chunk_size: int, min_chunk_size: int) -> List[Dict[str, Any]]:
        """Create chunks based on semantic breakpoints"""
        chunks = []
        start_idx = 0
        char_offset = 0
        
        for breakpoint in breakpoints:
            # Get sentences for this chunk
            chunk_sentences = sentences[start_idx:breakpoint]
            chunk_text = " ".join(chunk_sentences)
            
            # Check size constraints
            if len(chunk_text) > max_chunk_size:
                # Split large chunks further
                sub_chunks = self._split_large_chunk(chunk_text, max_chunk_size, char_offset)
                chunks.extend(sub_chunks)
                char_offset += len(chunk_text)
            elif len(chunk_text) >= min_chunk_size:
                # Good size chunk
                chunk = {
                    "id": f"semantic_chunk_{len(chunks)}",
                    "content": chunk_text,
                    "start_char": char_offset,
                    "end_char": char_offset + len(chunk_text),
                    "size": len(chunk_text),
                    "word_count": len(chunk_text.split()),
                    "sentence_count": len(chunk_sentences),
                    "semantic_score": self._calculate_semantic_score(chunk_sentences)
                }
                chunks.append(chunk)
                char_offset += len(chunk_text) + 1  # +1 for space
            else:
                # Too small, merge with previous chunk if possible
                if chunks:
                    prev_chunk = chunks[-1]
                    merged_content = prev_chunk["content"] + " " + chunk_text
                    if len(merged_content) <= max_chunk_size:
                        prev_chunk["content"] = merged_content
                        prev_chunk["end_char"] = char_offset + len(chunk_text)
                        prev_chunk["size"] = len(merged_content)
                        prev_chunk["word_count"] = len(merged_content.split())
                        prev_chunk["sentence_count"] += len(chunk_sentences)
                        char_offset += len(chunk_text) + 1
                    else:
                        # Can't merge, create small chunk anyway
                        chunk = self._create_chunk(chunk_text, len(chunks), char_offset, len(chunk_sentences))
                        chunks.append(chunk)
                        char_offset += len(chunk_text) + 1
                else:
                    # First chunk, create even if small
                    chunk = self._create_chunk(chunk_text, 0, char_offset, len(chunk_sentences))
                    chunks.append(chunk)
                    char_offset += len(chunk_text) + 1
            
            start_idx = breakpoint
        
        return chunks
    
    def _split_large_chunk(self, text: str, max_size: int, start_offset: int) -> List[Dict[str, Any]]:
        """Split a large chunk into smaller pieces"""
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0
        chunk_start = start_offset
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > max_size and current_chunk:
                # Create chunk from current words
                chunk_text = " ".join(current_chunk)
                chunk = self._create_chunk(chunk_text, len(chunks), chunk_start)
                chunks.append(chunk)
                
                # Start new chunk
                chunk_start += len(chunk_text) + 1
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += word_size
        
        # Add remaining words as final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk = self._create_chunk(chunk_text, len(chunks), chunk_start)
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, text: str, chunk_id: int, start_char: int, sentence_count: int = None) -> Dict[str, Any]:
        """Create a chunk dictionary"""
        return {
            "id": f"semantic_chunk_{chunk_id}",
            "content": text,
            "start_char": start_char,
            "end_char": start_char + len(text),
            "size": len(text),
            "word_count": len(text.split()),
            "sentence_count": sentence_count or len(self._split_sentences(text)),
            "semantic_score": 0.0
        }
    
    def _create_single_chunk(self, content: str, start_char: int) -> List[Dict[str, Any]]:
        """Create a single chunk when semantic analysis isn't possible"""
        return [self._create_chunk(content, 0, start_char)]
    
    def _calculate_semantic_score(self, sentences: List[str]) -> float:
        """Calculate a semantic coherence score for a chunk"""
        if len(sentences) <= 1:
            return 1.0
        
        try:
            # Simple coherence score based on sentence similarity
            embeddings = self.model.encode(sentences)
            similarities = []
            
            for i in range(len(embeddings) - 1):
                sim = self.cosine_similarity([embeddings[i]], [embeddings[i + 1]])[0][0]
                similarities.append(sim)
            
            return float(self.np.mean(similarities))
        except:
            return 0.0
    
    def _fallback_chunking(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to simple sentence-based chunking"""
        sentences = self._split_sentences(content)
        max_chunk_size = config.get("max_chunk_size", 1500)
        
        chunks = []
        current_chunk = []
        current_size = 0
        char_offset = 0
        
        for sentence in sentences:
            sentence_size = len(sentence) + 1
            
            if current_size + sentence_size > max_chunk_size and current_chunk:
                # Create chunk
                chunk_text = " ".join(current_chunk)
                chunk = self._create_chunk(chunk_text, len(chunks), char_offset)
                chunks.append(chunk)
                
                # Start new chunk
                char_offset += len(chunk_text) + 1
                current_chunk = [sentence]
                current_size = len(sentence)
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk = self._create_chunk(chunk_text, len(chunks), char_offset)
            chunks.append(chunk)
        
        return chunks
    
    def is_available(self) -> bool:
        """Check if semantic chunking is available"""
        return self.available
