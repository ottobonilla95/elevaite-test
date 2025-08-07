"""
Sentence Chunker for Advanced Text Processing

This module implements sentence-based chunking with intelligent sentence
boundary detection and size optimization.
"""

import logging
from typing import Dict, Any, List, Optional
import re
import time

logger = logging.getLogger(__name__)


class SentenceChunker:
    """Sentence-based chunking with intelligent boundary detection"""
    
    def __init__(self):
        self.available = True  # No external dependencies
        self.spacy_available = False
        self._initialize_spacy()
    
    def _initialize_spacy(self):
        """Try to initialize spaCy for better sentence detection"""
        try:
            import spacy
            # Try to load a small English model
            self.nlp = spacy.load("en_core_web_sm")
            self.spacy_available = True
            logger.info("Sentence chunker initialized with spaCy")
        except (ImportError, OSError):
            self.spacy_available = False
            logger.info("Sentence chunker initialized with regex (spaCy not available)")
    
    async def chunk_sentence(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform sentence-based chunking"""
        start_time = time.time()
        
        try:
            # Configuration
            max_sentences_per_chunk = config.get("max_sentences_per_chunk", 10)
            min_sentences_per_chunk = config.get("min_sentences_per_chunk", 1)
            max_chunk_size = config.get("max_chunk_size", 2000)
            min_chunk_size = config.get("min_chunk_size", 100)
            overlap_sentences = config.get("overlap_sentences", 0)
            
            # Split into sentences
            if self.spacy_available:
                sentences = self._split_sentences_spacy(content)
            else:
                sentences = self._split_sentences_regex(content)
            
            if not sentences:
                return self._create_single_chunk(content, 0)
            
            # Create chunks from sentences
            chunks = self._create_sentence_chunks(
                sentences,
                max_sentences_per_chunk=max_sentences_per_chunk,
                min_sentences_per_chunk=min_sentences_per_chunk,
                max_chunk_size=max_chunk_size,
                min_chunk_size=min_chunk_size,
                overlap_sentences=overlap_sentences
            )
            
            processing_time = time.time() - start_time
            
            # Add metadata to chunks
            for chunk in chunks:
                chunk.update({
                    "processing_time": processing_time / len(chunks),
                    "chunk_method": "sentence_boundary",
                    "sentence_detection": "spacy" if self.spacy_available else "regex"
                })
            
            logger.info(f"Sentence chunking completed: {len(chunks)} chunks in {processing_time:.2f}s")
            return chunks
            
        except Exception as e:
            logger.error(f"Sentence chunking failed: {e}")
            return self._fallback_chunking(content, config)
    
    def _split_sentences_spacy(self, content: str) -> List[Dict[str, Any]]:
        """Split content into sentences using spaCy"""
        doc = self.nlp(content)
        sentences = []
        
        for sent in doc.sents:
            sentence_text = sent.text.strip()
            if sentence_text:
                sentences.append({
                    "text": sentence_text,
                    "start_char": sent.start_char,
                    "end_char": sent.end_char,
                    "confidence": 1.0  # spaCy is generally reliable
                })
        
        return sentences
    
    def _split_sentences_regex(self, content: str) -> List[Dict[str, Any]]:
        """Split content into sentences using regex patterns"""
        # Enhanced sentence splitting patterns
        sentence_endings = r'[.!?]+(?:\s+|$)'
        
        # Find all sentence boundaries
        boundaries = []
        for match in re.finditer(sentence_endings, content):
            boundaries.append(match.end())
        
        if not boundaries:
            return [{"text": content.strip(), "start_char": 0, "end_char": len(content), "confidence": 0.5}]
        
        sentences = []
        start = 0
        
        for boundary in boundaries:
            sentence_text = content[start:boundary].strip()
            if sentence_text:
                # Calculate confidence based on sentence characteristics
                confidence = self._calculate_sentence_confidence(sentence_text)
                
                sentences.append({
                    "text": sentence_text,
                    "start_char": start,
                    "end_char": boundary,
                    "confidence": confidence
                })
            start = boundary
        
        # Add any remaining text
        if start < len(content):
            remaining_text = content[start:].strip()
            if remaining_text:
                sentences.append({
                    "text": remaining_text,
                    "start_char": start,
                    "end_char": len(content),
                    "confidence": 0.3  # Lower confidence for incomplete sentences
                })
        
        return sentences
    
    def _calculate_sentence_confidence(self, sentence: str) -> float:
        """Calculate confidence score for sentence boundary detection"""
        confidence = 0.5  # Base confidence
        
        # Increase confidence for proper sentence characteristics
        if len(sentence.split()) >= 3:  # Has multiple words
            confidence += 0.2
        
        if sentence[0].isupper():  # Starts with capital letter
            confidence += 0.2
        
        if re.search(r'[.!?]$', sentence.strip()):  # Ends with punctuation
            confidence += 0.3
        
        # Decrease confidence for potential false positives
        if re.search(r'\b(?:Mr|Mrs|Dr|Prof|Inc|Ltd|etc)\.$', sentence):  # Common abbreviations
            confidence -= 0.3
        
        if len(sentence) < 10:  # Very short sentences might be fragments
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def _create_sentence_chunks(self, sentences: List[Dict[str, Any]], 
                              max_sentences_per_chunk: int, min_sentences_per_chunk: int,
                              max_chunk_size: int, min_chunk_size: int, 
                              overlap_sentences: int) -> List[Dict[str, Any]]:
        """Create chunks from sentences"""
        chunks = []
        i = 0
        
        while i < len(sentences):
            chunk_sentences = []
            chunk_size = 0
            sentence_count = 0
            
            # Add sentences to chunk
            while (i < len(sentences) and 
                   sentence_count < max_sentences_per_chunk and 
                   chunk_size < max_chunk_size):
                
                sentence = sentences[i]
                sentence_text = sentence["text"]
                
                # Check if adding this sentence would exceed size limit
                potential_size = chunk_size + len(sentence_text) + (1 if chunk_sentences else 0)
                
                if potential_size > max_chunk_size and chunk_sentences:
                    break
                
                chunk_sentences.append(sentence)
                chunk_size = potential_size
                sentence_count += 1
                i += 1
            
            # Ensure minimum sentences per chunk (if possible)
            while (len(chunk_sentences) < min_sentences_per_chunk and 
                   i < len(sentences) and 
                   chunk_size < max_chunk_size):
                
                sentence = sentences[i]
                sentence_text = sentence["text"]
                potential_size = chunk_size + len(sentence_text) + 1
                
                if potential_size > max_chunk_size:
                    break
                
                chunk_sentences.append(sentence)
                chunk_size = potential_size
                i += 1
            
            # Create chunk if we have sentences
            if chunk_sentences:
                chunk = self._create_chunk_from_sentences(chunk_sentences, len(chunks))
                
                # Only add chunk if it meets minimum size requirement
                if len(chunk["content"]) >= min_chunk_size or not chunks:
                    chunks.append(chunk)
                elif chunks:
                    # Merge with previous chunk if too small
                    prev_chunk = chunks[-1]
                    merged_content = prev_chunk["content"] + " " + chunk["content"]
                    if len(merged_content) <= max_chunk_size:
                        prev_chunk["content"] = merged_content
                        prev_chunk["end_char"] = chunk["end_char"]
                        prev_chunk["size"] = len(merged_content)
                        prev_chunk["word_count"] = len(merged_content.split())
                        prev_chunk["sentence_count"] += chunk["sentence_count"]
                        prev_chunk["avg_sentence_confidence"] = (
                            prev_chunk["avg_sentence_confidence"] + chunk["avg_sentence_confidence"]
                        ) / 2
                    else:
                        chunks.append(chunk)
                else:
                    chunks.append(chunk)
            
            # Handle overlap
            if overlap_sentences > 0 and i < len(sentences):
                i -= min(overlap_sentences, len(chunk_sentences))
                i = max(i, len(chunks) * max_sentences_per_chunk - overlap_sentences)
        
        return chunks
    
    def _create_chunk_from_sentences(self, sentences: List[Dict[str, Any]], chunk_id: int) -> Dict[str, Any]:
        """Create a chunk from a list of sentences"""
        if not sentences:
            return self._create_empty_chunk(chunk_id)
        
        # Combine sentence texts
        content = " ".join([s["text"] for s in sentences])
        
        # Calculate positions
        start_char = sentences[0]["start_char"]
        end_char = sentences[-1]["end_char"]
        
        # Calculate average confidence
        avg_confidence = sum(s["confidence"] for s in sentences) / len(sentences)
        
        # Analyze sentence characteristics
        sentence_lengths = [len(s["text"]) for s in sentences]
        
        return {
            "id": f"sentence_chunk_{chunk_id}",
            "content": content,
            "start_char": start_char,
            "end_char": end_char,
            "size": len(content),
            "word_count": len(content.split()),
            "sentence_count": len(sentences),
            "avg_sentence_confidence": avg_confidence,
            "avg_sentence_length": sum(sentence_lengths) / len(sentence_lengths),
            "min_sentence_length": min(sentence_lengths),
            "max_sentence_length": max(sentence_lengths)
        }
    
    def _create_empty_chunk(self, chunk_id: int) -> Dict[str, Any]:
        """Create an empty chunk"""
        return {
            "id": f"sentence_chunk_{chunk_id}",
            "content": "",
            "start_char": 0,
            "end_char": 0,
            "size": 0,
            "word_count": 0,
            "sentence_count": 0,
            "avg_sentence_confidence": 0.0,
            "avg_sentence_length": 0.0,
            "min_sentence_length": 0,
            "max_sentence_length": 0
        }
    
    def _create_single_chunk(self, content: str, start_char: int) -> List[Dict[str, Any]]:
        """Create a single chunk when sentence splitting isn't possible"""
        return [{
            "id": "sentence_chunk_0",
            "content": content,
            "start_char": start_char,
            "end_char": start_char + len(content),
            "size": len(content),
            "word_count": len(content.split()),
            "sentence_count": 1,
            "avg_sentence_confidence": 0.5,
            "avg_sentence_length": len(content),
            "min_sentence_length": len(content),
            "max_sentence_length": len(content)
        }]
    
    def _fallback_chunking(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to simple text splitting"""
        max_chunk_size = config.get("max_chunk_size", 2000)
        
        chunks = []
        words = content.split()
        current_chunk = []
        current_size = 0
        char_offset = 0
        
        for word in words:
            word_size = len(word) + 1  # +1 for space
            
            if current_size + word_size > max_chunk_size and current_chunk:
                # Create chunk
                chunk_text = " ".join(current_chunk)
                chunk = {
                    "id": f"sentence_fallback_{len(chunks)}",
                    "content": chunk_text,
                    "start_char": char_offset,
                    "end_char": char_offset + len(chunk_text),
                    "size": len(chunk_text),
                    "word_count": len(current_chunk),
                    "sentence_count": 1,  # Estimate
                    "avg_sentence_confidence": 0.3,
                    "avg_sentence_length": len(chunk_text),
                    "min_sentence_length": len(chunk_text),
                    "max_sentence_length": len(chunk_text)
                }
                chunks.append(chunk)
                
                # Start new chunk
                char_offset += len(chunk_text) + 1
                current_chunk = [word]
                current_size = len(word)
            else:
                current_chunk.append(word)
                current_size += word_size
        
        # Add final chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunk = {
                "id": f"sentence_fallback_{len(chunks)}",
                "content": chunk_text,
                "start_char": char_offset,
                "end_char": char_offset + len(chunk_text),
                "size": len(chunk_text),
                "word_count": len(current_chunk),
                "sentence_count": 1,
                "avg_sentence_confidence": 0.3,
                "avg_sentence_length": len(chunk_text),
                "min_sentence_length": len(chunk_text),
                "max_sentence_length": len(chunk_text)
            }
            chunks.append(chunk)
        
        return chunks
    
    def is_available(self) -> bool:
        """Check if sentence chunking is available"""
        return self.available
