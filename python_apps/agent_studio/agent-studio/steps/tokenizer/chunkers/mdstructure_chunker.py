"""
Markdown Structure Chunker for Advanced Text Processing

This module implements structure-aware chunking for markdown documents,
respecting headers, sections, and other markdown elements.
"""

import logging
from typing import Dict, Any, List
import re
import time

logger = logging.getLogger(__name__)


class MDStructureChunker:
    """Markdown structure-aware chunking"""
    
    def __init__(self):
        self.available = True  # No external dependencies
    
    async def chunk_mdstructure(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Chunk based on markdown structure"""
        start_time = time.time()
        
        try:
            # Configuration
            chunk_size = config.get("chunk_size", 1500)
            min_chunk_size = config.get("min_chunk_size", 100)
            max_chunk_size = config.get("max_chunk_size", 3000)
            respect_headers = config.get("respect_headers", True)
            include_headers = config.get("include_headers", True)
            
            # Parse markdown structure
            sections = self._parse_markdown_sections(content)
            
            if not sections:
                # No markdown structure found, fallback to simple chunking
                return self._fallback_chunking(content, config)
            
            # Create chunks respecting structure
            chunks = self._create_structured_chunks(
                sections,
                chunk_size=chunk_size,
                min_chunk_size=min_chunk_size,
                max_chunk_size=max_chunk_size,
                respect_headers=respect_headers,
                include_headers=include_headers
            )
            
            processing_time = time.time() - start_time
            
            # Add metadata to chunks
            for chunk in chunks:
                chunk.update({
                    "processing_time": processing_time / len(chunks),
                    "chunk_method": "mdstructure"
                })
            
            logger.info(f"MDStructure chunking completed: {len(chunks)} chunks in {processing_time:.2f}s")
            return chunks
            
        except Exception as e:
            logger.error(f"MDStructure chunking failed: {e}")
            return self._fallback_chunking(content, config)
    
    def _parse_markdown_sections(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown into hierarchical sections"""
        sections = []
        lines = content.split('\n')
        
        current_section = {
            "header": "",
            "content": "",
            "level": 0,
            "start_line": 0,
            "header_type": "none"
        }
        
        line_num = 0
        
        for i, line in enumerate(lines):
            # Check for ATX headers (# ## ### etc.)
            atx_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())
            if atx_match:
                # Save previous section if it has content
                if current_section["content"].strip() or current_section["header"]:
                    current_section["end_line"] = i - 1
                    sections.append(current_section.copy())
                
                # Start new section
                level = len(atx_match.group(1))
                header_text = atx_match.group(2)
                current_section = {
                    "header": line.strip(),
                    "header_text": header_text,
                    "content": "",
                    "level": level,
                    "start_line": i,
                    "header_type": "atx"
                }
                continue
            
            # Check for Setext headers (underlined with = or -)
            if i < len(lines) - 1:
                next_line = lines[i + 1].strip()
                if re.match(r'^=+$', next_line) and line.strip():
                    # H1 Setext header
                    if current_section["content"].strip() or current_section["header"]:
                        current_section["end_line"] = i - 1
                        sections.append(current_section.copy())
                    
                    current_section = {
                        "header": line.strip(),
                        "header_text": line.strip(),
                        "content": "",
                        "level": 1,
                        "start_line": i,
                        "header_type": "setext_h1"
                    }
                    continue
                elif re.match(r'^-+$', next_line) and line.strip():
                    # H2 Setext header
                    if current_section["content"].strip() or current_section["header"]:
                        current_section["end_line"] = i - 1
                        sections.append(current_section.copy())
                    
                    current_section = {
                        "header": line.strip(),
                        "header_text": line.strip(),
                        "content": "",
                        "level": 2,
                        "start_line": i,
                        "header_type": "setext_h2"
                    }
                    continue
            
            # Regular content line
            current_section["content"] += line + "\n"
        
        # Add final section
        if current_section["content"].strip() or current_section["header"]:
            current_section["end_line"] = len(lines) - 1
            sections.append(current_section)
        
        return sections
    
    def _create_structured_chunks(self, sections: List[Dict[str, Any]], 
                                chunk_size: int, min_chunk_size: int, max_chunk_size: int,
                                respect_headers: bool, include_headers: bool) -> List[Dict[str, Any]]:
        """Create chunks respecting markdown structure"""
        chunks = []
        current_chunk_content = ""
        current_chunk_start = 0
        current_headers = []  # Stack of headers for context
        
        for section in sections:
            section_header = section["header"]
            section_content = section["content"].strip()
            section_level = section["level"]
            
            # Update header stack based on level
            if section_level > 0:
                # Remove headers at same or deeper level
                current_headers = [h for h in current_headers if h["level"] < section_level]
                # Add current header
                current_headers.append({
                    "text": section_header,
                    "level": section_level,
                    "header_text": section.get("header_text", "")
                })
            
            # Prepare section text
            section_text = ""
            if include_headers and section_header:
                section_text = section_header + "\n\n"
            if section_content:
                section_text += section_content
            
            # Check if adding this section would exceed chunk size
            potential_chunk = current_chunk_content
            if potential_chunk and section_text:
                potential_chunk += "\n\n" + section_text
            elif section_text:
                potential_chunk = section_text
            
            if len(potential_chunk) > chunk_size and current_chunk_content:
                # Current chunk is large enough, finalize it
                if len(current_chunk_content) >= min_chunk_size:
                    chunk = self._create_chunk(
                        current_chunk_content.strip(),
                        len(chunks),
                        current_chunk_start,
                        current_headers.copy()
                    )
                    chunks.append(chunk)
                
                # Start new chunk with current section
                current_chunk_content = section_text
                current_chunk_start = self._calculate_char_position(chunks)
            else:
                # Add section to current chunk
                if current_chunk_content and section_text:
                    current_chunk_content += "\n\n" + section_text
                elif section_text:
                    current_chunk_content = section_text
            
            # Handle very large sections
            if len(current_chunk_content) > max_chunk_size:
                # Split large section
                split_chunks = self._split_large_section(
                    current_chunk_content,
                    max_chunk_size,
                    current_chunk_start,
                    current_headers.copy(),
                    len(chunks)
                )
                chunks.extend(split_chunks)
                current_chunk_content = ""
                current_chunk_start = self._calculate_char_position(chunks)
        
        # Add final chunk
        if current_chunk_content.strip():
            if len(current_chunk_content) >= min_chunk_size or not chunks:
                chunk = self._create_chunk(
                    current_chunk_content.strip(),
                    len(chunks),
                    current_chunk_start,
                    current_headers.copy()
                )
                chunks.append(chunk)
            elif chunks:
                # Merge with last chunk if too small
                last_chunk = chunks[-1]
                merged_content = last_chunk["content"] + "\n\n" + current_chunk_content.strip()
                if len(merged_content) <= max_chunk_size:
                    last_chunk["content"] = merged_content
                    last_chunk["end_char"] = last_chunk["start_char"] + len(merged_content)
                    last_chunk["size"] = len(merged_content)
                    last_chunk["word_count"] = len(merged_content.split())
        
        return chunks
    
    def _split_large_section(self, content: str, max_size: int, start_char: int, 
                           headers: List[Dict[str, Any]], chunk_id_start: int) -> List[Dict[str, Any]]:
        """Split a large section into smaller chunks"""
        chunks = []
        
        # Try to split by paragraphs first
        paragraphs = content.split('\n\n')
        current_chunk = ""
        current_start = start_char
        
        for paragraph in paragraphs:
            potential_chunk = current_chunk
            if potential_chunk:
                potential_chunk += "\n\n" + paragraph
            else:
                potential_chunk = paragraph
            
            if len(potential_chunk) > max_size and current_chunk:
                # Create chunk from current content
                chunk = self._create_chunk(
                    current_chunk.strip(),
                    chunk_id_start + len(chunks),
                    current_start,
                    headers
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_start += len(current_chunk) + 2  # +2 for \n\n
                current_chunk = paragraph
            else:
                current_chunk = potential_chunk
        
        # Add final chunk
        if current_chunk.strip():
            chunk = self._create_chunk(
                current_chunk.strip(),
                chunk_id_start + len(chunks),
                current_start,
                headers
            )
            chunks.append(chunk)
        
        return chunks
    
    def _create_chunk(self, content: str, chunk_id: int, start_char: int, 
                     headers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create a chunk dictionary with markdown metadata"""
        # Extract markdown elements
        md_elements = self._analyze_markdown_elements(content)
        
        return {
            "id": f"mdstructure_chunk_{chunk_id}",
            "content": content,
            "start_char": start_char,
            "end_char": start_char + len(content),
            "size": len(content),
            "word_count": len(content.split()),
            "headers": headers,
            "header_context": " > ".join([h["header_text"] for h in headers]),
            "markdown_elements": md_elements,
            "structure_level": headers[-1]["level"] if headers else 0
        }
    
    def _analyze_markdown_elements(self, content: str) -> Dict[str, int]:
        """Analyze markdown elements in content"""
        elements = {
            "headers": len(re.findall(r'^#{1,6}\s+', content, re.MULTILINE)),
            "bold": len(re.findall(r'\*\*[^*]+\*\*', content)),
            "italic": len(re.findall(r'\*[^*]+\*', content)),
            "code_blocks": len(re.findall(r'```[^`]*```', content, re.DOTALL)),
            "inline_code": len(re.findall(r'`[^`]+`', content)),
            "links": len(re.findall(r'\[([^\]]+)\]\([^)]+\)', content)),
            "images": len(re.findall(r'!\[([^\]]*)\]\([^)]+\)', content)),
            "lists": len(re.findall(r'^[-*+]\s+', content, re.MULTILINE)),
            "tables": len(re.findall(r'\|.*\|', content))
        }
        return elements
    
    def _calculate_char_position(self, chunks: List[Dict[str, Any]]) -> int:
        """Calculate character position for next chunk"""
        if not chunks:
            return 0
        last_chunk = chunks[-1]
        return last_chunk["end_char"] + 2  # +2 for section separator
    
    def _fallback_chunking(self, content: str, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fallback to simple paragraph-based chunking"""
        chunk_size = config.get("chunk_size", 1500)
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
            
            if len(potential_chunk) > chunk_size and current_chunk:
                # Create chunk
                chunk = {
                    "id": f"mdstructure_fallback_{len(chunks)}",
                    "content": current_chunk.strip(),
                    "start_char": char_offset,
                    "end_char": char_offset + len(current_chunk),
                    "size": len(current_chunk),
                    "word_count": len(current_chunk.split()),
                    "headers": [],
                    "header_context": "",
                    "markdown_elements": self._analyze_markdown_elements(current_chunk),
                    "structure_level": 0
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
                "id": f"mdstructure_fallback_{len(chunks)}",
                "content": current_chunk.strip(),
                "start_char": char_offset,
                "end_char": char_offset + len(current_chunk),
                "size": len(current_chunk),
                "word_count": len(current_chunk.split()),
                "headers": [],
                "header_context": "",
                "markdown_elements": self._analyze_markdown_elements(current_chunk),
                "structure_level": 0
            }
            chunks.append(chunk)
        
        return chunks
    
    def is_available(self) -> bool:
        """Check if MDStructure chunking is available"""
        return self.available
