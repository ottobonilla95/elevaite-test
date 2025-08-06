"""
File Reader Step for Tokenizer Workflows

Reads and extracts text content from various document formats including:
- PDF files (using PyPDF2 or pdfplumber)
- Word documents (.docx) using python-docx
- Plain text files (.txt)
- Markdown files (.md)
- HTML files (.html)

Highly configurable through API parameters.
"""

import os
import mimetypes
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

from steps.base_deterministic_step import (
    BaseDeterministicStep,
    StepConfig,
    StepResult,
    StepStatus,
    StepValidationResult,
    DataInputStep,
)
from services.workflow_execution_context import DeterministicStepType
from fastapi_logger import ElevaiteLogger


class FileReaderStepConfig(StepConfig):
    """Configuration for File Reader Step"""
    step_type: DeterministicStepType = DeterministicStepType.DATA_INPUT


class FileReaderStep(DataInputStep):
    """
    Reads and extracts text content from various document formats.
    
    Supported formats:
    - PDF (.pdf)
    - Word documents (.docx) 
    - Plain text (.txt)
    - Markdown (.md)
    - HTML (.html)
    
    Configuration options:
    - file_path: Path to the file to read
    - supported_formats: List of allowed file extensions 
    - max_file_size: Maximum file size in bytes
    - encoding: Text encoding (default: utf-8)
    - pdf_method: 'pypdf2' or 'pdfplumber' for PDF reading
    - extract_metadata: Whether to extract file metadata
    - preserve_formatting: Whether to preserve original formatting
    """
    
    def __init__(self, config: FileReaderStepConfig):
        super().__init__(config)
        self.logger = ElevaiteLogger()
    
    def validate_config(self) -> StepValidationResult:
        """Validate file reader configuration"""
        result = StepValidationResult()
        
        config = self.config.config
        
        # Check required configuration
        if not config.get("file_path") and not config.get("input_source"):
            result.errors.append("Either 'file_path' or 'input_source' must be specified")
        
        # Validate supported formats
        supported_formats = config.get("supported_formats", [".pdf", ".docx", ".txt", ".md", ".html"])
        if not isinstance(supported_formats, list):
            result.errors.append("'supported_formats' must be a list")
        
        # Validate max file size
        max_file_size = config.get("max_file_size", 50 * 1024 * 1024)  # 50MB default
        if not isinstance(max_file_size, int) or max_file_size <= 0:
            result.errors.append("'max_file_size' must be a positive integer")
        
        # Validate PDF method
        pdf_method = config.get("pdf_method", "pypdf2")
        if pdf_method not in ["pypdf2", "pdfplumber"]:
            result.errors.append("'pdf_method' must be 'pypdf2' or 'pdfplumber'")
        
        # Validate encoding
        encoding = config.get("encoding", "utf-8")
        try:
            "test".encode(encoding)
        except LookupError:
            result.errors.append(f"Invalid encoding: {encoding}")
        
        result.is_valid = len(result.errors) == 0
        return result
    
    def get_required_inputs(self) -> List[str]:
        """Required inputs for file reader step"""
        config = self.config.config
        if config.get("file_path"):
            return []  # File path is in config
        else:
            return ["file_path"]  # File path must come from input
    
    def get_output_schema(self) -> Dict[str, Any]:
        """Output schema for file reader step"""
        return {
            "type": "object",
            "properties": {
                "content": {"type": "string", "description": "Extracted text content"},
                "metadata": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "file_size": {"type": "integer"},
                        "file_type": {"type": "string"},
                        "mime_type": {"type": "string"},
                        "page_count": {"type": "integer"},
                        "character_count": {"type": "integer"},
                        "word_count": {"type": "integer"},
                        "extraction_method": {"type": "string"},
                        "processed_at": {"type": "string"},
                    }
                },
                "success": {"type": "boolean"},
                "error": {"type": "string"},
            },
            "required": ["content", "metadata", "success"]
        }
    
    async def execute(self, input_data: Dict[str, Any]) -> StepResult:
        """Execute file reading step"""
        try:
            config = self.config.config
            
            # Get file path from config or input
            file_path = config.get("file_path") or input_data.get("file_path")
            if not file_path:
                return StepResult(
                    status=StepStatus.FAILED,
                    error="No file path provided in config or input data"
                )
            
            # Validate file exists and is accessible
            if not os.path.exists(file_path):
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"File not found: {file_path}"
                )
            
            if not os.path.isfile(file_path):
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"Path is not a file: {file_path}"
                )
            
            # Check file size
            file_size = os.path.getsize(file_path)
            max_file_size = config.get("max_file_size", 50 * 1024 * 1024)  # 50MB
            if file_size > max_file_size:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"File size ({file_size} bytes) exceeds maximum ({max_file_size} bytes)"
                )
            
            # Determine file type
            file_ext = Path(file_path).suffix.lower()
            supported_formats = config.get("supported_formats", [".pdf", ".docx", ".txt", ".md", ".html"])
            
            if file_ext not in supported_formats:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"Unsupported file format: {file_ext}. Supported formats: {supported_formats}"
                )
            
            # Extract content based on file type
            self._update_progress(
                current_operation=f"Reading {file_ext} file: {os.path.basename(file_path)}"
            )
            
            content = ""
            extraction_method = ""
            page_count = None
            
            if file_ext == ".pdf":
                content, page_count, extraction_method = await self._read_pdf(file_path, config)
            elif file_ext == ".docx":
                content, extraction_method = await self._read_docx(file_path, config)
            elif file_ext in [".txt", ".md"]:
                content, extraction_method = await self._read_text(file_path, config)
            elif file_ext == ".html":
                content, extraction_method = await self._read_html(file_path, config)
            else:
                return StepResult(
                    status=StepStatus.FAILED,
                    error=f"No handler for file type: {file_ext}"
                )
            
            # Calculate metadata
            mime_type, _ = mimetypes.guess_type(file_path)
            character_count = len(content)
            word_count = len(content.split()) if content else 0
            
            # Prepare result
            result_data = {
                "content": content,
                "metadata": {
                    "file_path": file_path,
                    "file_size": file_size,
                    "file_type": file_ext,
                    "mime_type": mime_type or "unknown",
                    "character_count": character_count,
                    "word_count": word_count,
                    "extraction_method": extraction_method,
                    "processed_at": datetime.now().isoformat(),
                },
                "success": True,
            }
            
            if page_count is not None:
                result_data["metadata"]["page_count"] = page_count
            
            self.logger.info(f"Successfully read file: {file_path} ({character_count} chars, {word_count} words)")
            
            return StepResult(
                status=StepStatus.COMPLETED,
                data=result_data
            )
            
        except Exception as e:
            self.logger.error(f"Error reading file: {str(e)}")
            return StepResult(
                status=StepStatus.FAILED,
                error=f"File reading error: {str(e)}"
            )
    
    async def _read_pdf(self, file_path: str, config: Dict[str, Any]) -> tuple[str, int, str]:
        """Read PDF file using specified method"""
        pdf_method = config.get("pdf_method", "pypdf2")
        
        if pdf_method == "pdfplumber":
            return await self._read_pdf_pdfplumber(file_path)
        else:
            return await self._read_pdf_pypdf2(file_path)
    
    async def _read_pdf_pypdf2(self, file_path: str) -> tuple[str, int, str]:
        """Read PDF using PyPDF2"""
        try:
            import PyPDF2
            
            content = ""
            page_count = 0
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                for page_num in range(page_count):
                    page = pdf_reader.pages[page_num]
                    content += page.extract_text() + "\n\n"
                    
                    # Update progress
                    progress = (page_num + 1) / page_count * 100
                    self._update_progress(
                        processed_items=page_num + 1,
                        total_items=page_count,
                        progress_percentage=progress
                    )
            
            return content.strip(), page_count, "PyPDF2"
            
        except ImportError:
            raise Exception("PyPDF2 not installed. Install with: pip install PyPDF2")
        except Exception as e:
            raise Exception(f"Error reading PDF with PyPDF2: {str(e)}")
    
    async def _read_pdf_pdfplumber(self, file_path: str) -> tuple[str, int, str]:
        """Read PDF using pdfplumber (better for complex layouts)"""
        try:
            import pdfplumber
            
            content = ""
            page_count = 0
            
            with pdfplumber.open(file_path) as pdf:
                page_count = len(pdf.pages)
                
                for page_num, page in enumerate(pdf.pages):
                    text = page.extract_text()
                    if text:
                        content += text + "\n\n"
                    
                    # Update progress
                    progress = (page_num + 1) / page_count * 100
                    self._update_progress(
                        processed_items=page_num + 1,
                        total_items=page_count,
                        progress_percentage=progress
                    )
            
            return content.strip(), page_count, "pdfplumber"
            
        except ImportError:
            raise Exception("pdfplumber not installed. Install with: pip install pdfplumber")
        except Exception as e:
            raise Exception(f"Error reading PDF with pdfplumber: {str(e)}")
    
    async def _read_docx(self, file_path: str, config: Dict[str, Any]) -> tuple[str, str]:
        """Read Word document"""
        try:
            import docx
            
            doc = docx.Document(file_path)
            content = ""
            
            preserve_formatting = config.get("preserve_formatting", False)
            
            for paragraph in doc.paragraphs:
                if preserve_formatting:
                    # Preserve some basic formatting
                    text = paragraph.text
                    if paragraph.style.name.startswith('Heading'):
                        text = f"# {text}"
                    content += text + "\n"
                else:
                    content += paragraph.text + "\n"
            
            return content.strip(), "python-docx"
            
        except ImportError:
            raise Exception("python-docx not installed. Install with: pip install python-docx")
        except Exception as e:
            raise Exception(f"Error reading DOCX: {str(e)}")
    
    async def _read_text(self, file_path: str, config: Dict[str, Any]) -> tuple[str, str]:
        """Read plain text file"""
        encoding = config.get("encoding", "utf-8")
        
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                content = file.read()
            
            return content, f"text reader (encoding: {encoding})"
            
        except UnicodeDecodeError:
            # Try alternative encodings
            for alt_encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                try:
                    with open(file_path, 'r', encoding=alt_encoding) as file:
                        content = file.read()
                    return content, f"text reader (encoding: {alt_encoding})"
                except UnicodeDecodeError:
                    continue
            
            raise Exception(f"Could not decode file with encoding {encoding} or common alternatives")
        except Exception as e:
            raise Exception(f"Error reading text file: {str(e)}")
    
    async def _read_html(self, file_path: str, config: Dict[str, Any]) -> tuple[str, str]:
        """Read HTML file and extract text"""
        try:
            from bs4 import BeautifulSoup
            
            encoding = config.get("encoding", "utf-8")
            
            with open(file_path, 'r', encoding=encoding) as file:
                html_content = file.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            content = ' '.join(chunk for chunk in chunks if chunk)
            
            return content, "BeautifulSoup HTML parser"
            
        except ImportError:
            raise Exception("BeautifulSoup not installed. Install with: pip install beautifulsoup4")
        except Exception as e:
            raise Exception(f"Error reading HTML: {str(e)}")


# Factory function for easy creation
def create_file_reader_step(config: Dict[str, Any]) -> FileReaderStep:
    """Create a FileReaderStep with given configuration"""
    step_config = FileReaderStepConfig(
        step_name=config.get("step_name", "File Reader"),
        config=config
    )
    return FileReaderStep(step_config)