"""
Docling Parser Integration for Advanced PDF Processing

This module integrates docling's advanced PDF parsing capabilities into the
tokenizer workflow, providing structured content extraction, table detection,
and image processing.
"""

import logging
from typing import Dict, Any, List, Tuple
from pathlib import Path
import asyncio
import time

logger = logging.getLogger(__name__)


class DoclingParser:
    """Docling parser integration for advanced PDF processing"""
    
    def __init__(self):
        self.converter = None
        self.available = False
        self._initialize_docling()
    
    def _initialize_docling(self):
        """Initialize docling components"""
        try:
            from docling.document_converter import DocumentConverter
            from docling.datamodel.base_models import InputFormat
            from docling.datamodel.pipeline_options import PdfPipelineOptions
            from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
            
            # Configure pipeline options for better performance
            pipeline_options = PdfPipelineOptions()
            pipeline_options.do_ocr = True  # Enable OCR for scanned PDFs
            pipeline_options.do_table_structure = True  # Extract table structure
            pipeline_options.table_structure_options.do_cell_matching = True
            
            # Initialize converter with optimized settings
            self.converter = DocumentConverter(
                format_options={
                    InputFormat.PDF: pipeline_options
                }
            )
            
            self.available = True
            logger.info("Docling parser initialized successfully")
            
        except ImportError as e:
            self.available = False
            logger.warning(f"Docling not available: {e}. Install with: pip install docling")
        except Exception as e:
            self.available = False
            logger.error(f"Failed to initialize docling: {e}")
    
    async def parse_pdf(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PDF using docling with advanced features"""
        if not self.available:
            raise Exception("Docling not available. Please install docling package.")
        
        start_time = time.time()
        
        try:
            # Run docling conversion in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._convert_document, file_path, config)
            
            processing_time = time.time() - start_time
            
            # Extract content and metadata
            content = result.document.export_to_markdown()
            
            # Extract structured elements
            structured_elements = self._extract_structured_elements(result)
            
            # Calculate metadata
            metadata = {
                "page_count": len(result.document.pages) if result.document.pages else 0,
                "tables_count": len([elem for elem in structured_elements if elem["type"] == "table"]),
                "images_count": len([elem for elem in structured_elements if elem["type"] == "figure"]),
                "lists_count": len([elem for elem in structured_elements if elem["type"] == "list"]),
                "extraction_method": "docling",
                "structured_content": True,
                "processing_time_seconds": processing_time,
                "ocr_used": config.get("use_ocr", True),
                "table_extraction": config.get("extract_tables", True)
            }
            
            return {
                "content": content,
                "metadata": metadata,
                "structured_elements": structured_elements,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Docling parsing failed for {file_path}: {e}")
            return {
                "content": "",
                "metadata": {
                    "extraction_method": "docling",
                    "error": str(e),
                    "processing_time_seconds": time.time() - start_time
                },
                "structured_elements": [],
                "success": False,
                "error": str(e)
            }
    
    def _convert_document(self, file_path: str, config: Dict[str, Any]):
        """Convert document using docling (runs in thread pool)"""
        return self.converter.convert(file_path)
    
    def _extract_structured_elements(self, result) -> List[Dict[str, Any]]:
        """Extract tables, images, and other structured elements"""
        elements = []
        
        try:
            # Extract from document structure
            if hasattr(result.document, 'texts') and result.document.texts:
                for item in result.document.texts:
                    if hasattr(item, 'label') and item.label in ["table", "figure", "list"]:
                        element = {
                            "type": item.label,
                            "content": item.text if hasattr(item, 'text') else "",
                            "page": None,
                            "bbox": None
                        }
                        
                        # Extract position information if available
                        if hasattr(item, 'prov') and item.prov:
                            prov = item.prov[0] if isinstance(item.prov, list) else item.prov
                            if hasattr(prov, 'page'):
                                element["page"] = prov.page
                            if hasattr(prov, 'bbox'):
                                element["bbox"] = prov.bbox
                        
                        elements.append(element)
            
            # Extract tables specifically
            if hasattr(result.document, 'tables') and result.document.tables:
                for i, table in enumerate(result.document.tables):
                    table_element = {
                        "type": "table",
                        "content": self._table_to_markdown(table),
                        "table_id": f"table_{i}",
                        "rows": len(table.data) if hasattr(table, 'data') else 0,
                        "columns": len(table.data[0]) if hasattr(table, 'data') and table.data else 0
                    }
                    elements.append(table_element)
            
        except Exception as e:
            logger.warning(f"Failed to extract structured elements: {e}")
        
        return elements
    
    def _table_to_markdown(self, table) -> str:
        """Convert table to markdown format"""
        try:
            if not hasattr(table, 'data') or not table.data:
                return ""
            
            markdown_lines = []
            
            # Add header row
            if table.data:
                header = " | ".join(str(cell) for cell in table.data[0])
                markdown_lines.append(f"| {header} |")
                
                # Add separator
                separator = " | ".join("---" for _ in table.data[0])
                markdown_lines.append(f"| {separator} |")
                
                # Add data rows
                for row in table.data[1:]:
                    row_str = " | ".join(str(cell) for cell in row)
                    markdown_lines.append(f"| {row_str} |")
            
            return "\n".join(markdown_lines)
            
        except Exception as e:
            logger.warning(f"Failed to convert table to markdown: {e}")
            return str(table)
    
    async def parse_docx(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse DOCX using docling"""
        if not self.available:
            raise Exception("Docling not available")
        
        start_time = time.time()
        
        try:
            # Run conversion in thread pool
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, self._convert_document, file_path, config)
            
            processing_time = time.time() - start_time
            
            # Extract content
            content = result.document.export_to_markdown()
            
            # Extract structured elements
            structured_elements = self._extract_structured_elements(result)
            
            metadata = {
                "extraction_method": "docling",
                "structured_content": True,
                "processing_time_seconds": processing_time,
                "tables_count": len([elem for elem in structured_elements if elem["type"] == "table"]),
                "images_count": len([elem for elem in structured_elements if elem["type"] == "figure"])
            }
            
            return {
                "content": content,
                "metadata": metadata,
                "structured_elements": structured_elements,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Docling DOCX parsing failed for {file_path}: {e}")
            return {
                "content": "",
                "metadata": {
                    "extraction_method": "docling",
                    "error": str(e),
                    "processing_time_seconds": time.time() - start_time
                },
                "structured_elements": [],
                "success": False,
                "error": str(e)
            }
    
    def is_available(self) -> bool:
        """Check if docling is available"""
        return self.available
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported file formats"""
        if self.available:
            return [".pdf", ".docx"]
        return []
    
    async def validate_file(self, file_path: str) -> Tuple[bool, str]:
        """Validate if file can be processed by docling"""
        if not self.available:
            return False, "Docling not available"
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext not in self.get_supported_formats():
            return False, f"Unsupported format: {file_ext}"
        
        if not Path(file_path).exists():
            return False, "File not found"
        
        # Check file size (docling can handle large files but may be slow)
        file_size = Path(file_path).stat().st_size
        max_size = 100 * 1024 * 1024  # 100MB limit
        if file_size > max_size:
            return False, f"File too large: {file_size / (1024*1024):.1f}MB > {max_size / (1024*1024)}MB"
        
        return True, "File valid for docling processing"
