"""
Markitdown Parser Integration

This module integrates markitdown's document parsing capabilities into the
tokenizer workflow, providing support for various document formats with
markdown output.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import asyncio
import time

logger = logging.getLogger(__name__)


class MarkitdownParser:
    """Markitdown parser integration for document processing"""
    
    def __init__(self):
        self.markitdown = None
        self.available = False
        self._initialize_markitdown()
    
    def _initialize_markitdown(self):
        """Initialize markitdown components"""
        try:
            from markitdown import MarkItDown
            
            self.markitdown = MarkItDown()
            self.available = True
            logger.info("Markitdown parser initialized successfully")
            
        except ImportError as e:
            self.available = False
            logger.warning(f"Markitdown not available: {e}. Install with: pip install markitdown")
        except Exception as e:
            self.available = False
            logger.error(f"Failed to initialize markitdown: {e}")
    
    async def parse_document(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse document using markitdown"""
        if not self.available:
            raise Exception("Markitdown not available. Please install markitdown package.")
        
        start_time = time.time()
        
        try:
            # Run markitdown conversion in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._convert_document, file_path, config)
            
            processing_time = time.time() - start_time
            
            # Extract content
            content = result.text_content if hasattr(result, 'text_content') else str(result)
            
            # Calculate basic metadata
            metadata = {
                "extraction_method": "markitdown",
                "structured_content": False,
                "processing_time_seconds": processing_time,
                "character_count": len(content),
                "word_count": len(content.split()) if content else 0,
                "markdown_format": True
            }
            
            # Add file-specific metadata if available
            if hasattr(result, 'metadata') and result.metadata:
                metadata.update(result.metadata)
            
            return {
                "content": content,
                "metadata": metadata,
                "structured_elements": [],  # Markitdown doesn't extract structured elements
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Markitdown parsing failed for {file_path}: {e}")
            return {
                "content": "",
                "metadata": {
                    "extraction_method": "markitdown",
                    "error": str(e),
                    "processing_time_seconds": time.time() - start_time
                },
                "structured_elements": [],
                "success": False,
                "error": str(e)
            }
    
    def _convert_document(self, file_path: str, config: Dict[str, Any]):
        """Convert document using markitdown (runs in thread pool)"""
        return self.markitdown.convert(file_path)
    
    async def parse_pdf(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PDF using markitdown"""
        return await self.parse_document(file_path, config)
    
    async def parse_docx(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DOCX using markitdown"""
        return await self.parse_document(file_path, config)
    
    async def parse_xlsx(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse XLSX using markitdown"""
        return await self.parse_document(file_path, config)
    
    async def parse_url(self, url: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse URL using markitdown"""
        if not self.available:
            raise Exception("Markitdown not available")
        
        start_time = time.time()
        
        try:
            # Run markitdown URL conversion in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._convert_url, url, config)
            
            processing_time = time.time() - start_time
            
            # Extract content
            content = result.text_content if hasattr(result, 'text_content') else str(result)
            
            metadata = {
                "extraction_method": "markitdown",
                "source_url": url,
                "structured_content": False,
                "processing_time_seconds": processing_time,
                "character_count": len(content),
                "word_count": len(content.split()) if content else 0,
                "markdown_format": True
            }
            
            return {
                "content": content,
                "metadata": metadata,
                "structured_elements": [],
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Markitdown URL parsing failed for {url}: {e}")
            return {
                "content": "",
                "metadata": {
                    "extraction_method": "markitdown",
                    "source_url": url,
                    "error": str(e),
                    "processing_time_seconds": time.time() - start_time
                },
                "structured_elements": [],
                "success": False,
                "error": str(e)
            }
    
    def _convert_url(self, url: str, config: Dict[str, Any]):
        """Convert URL using markitdown (runs in thread pool)"""
        return self.markitdown.convert(url)
    
    def is_available(self) -> bool:
        """Check if markitdown is available"""
        return self.available
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        if self.available:
            return [".pdf", ".docx", ".xlsx", ".pptx", ".txt", ".html", ".md"]
        return []
    
    def get_supported_sources(self) -> List[str]:
        """Get list of supported source types"""
        if self.available:
            return ["file", "url"]
        return []
    
    async def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate if file can be processed by markitdown"""
        if not self.available:
            return False, "Markitdown not available"
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.get_supported_formats():
            return False, f"Unsupported format: {file_ext}"
        
        if not Path(file_path).exists():
            return False, "File not found"
        
        # Check file size (markitdown is generally fast but large files may take time)
        file_size = Path(file_path).stat().st_size
        max_size = 50 * 1024 * 1024  # 50MB limit
        if file_size > max_size:
            return False, f"File too large: {file_size / (1024*1024):.1f}MB > {max_size / (1024*1024)}MB"
        
        return True, "File valid for markitdown processing"
    
    async def validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate if URL can be processed by markitdown"""
        if not self.available:
            return False, "Markitdown not available"
        
        # Basic URL validation
        if not url.startswith(('http://', 'https://')):
            return False, "URL must start with http:// or https://"
        
        return True, "URL valid for markitdown processing"
