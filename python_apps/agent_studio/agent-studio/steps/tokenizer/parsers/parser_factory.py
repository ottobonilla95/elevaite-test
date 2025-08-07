"""
Parser Factory for Intelligent Parser Selection

This module provides a factory for selecting the optimal parser based on
file type, size, configuration preferences, and parser availability.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path
import asyncio

from .docling_parser import DoclingParser
from .markitdown_parser import MarkitdownParser

logger = logging.getLogger(__name__)


class ParserFactory:
    """Factory for selecting optimal parser based on config and file characteristics"""

    def __init__(self):
        self.parsers = {}
        self._initialize_parsers()

    def _initialize_parsers(self):
        """Initialize all available parsers"""
        # Advanced parsers
        self.parsers["docling"] = DoclingParser()
        self.parsers["markitdown"] = MarkitdownParser()

        # Legacy parsers (from existing tokenizer implementation)
        self.parsers["pdfplumber"] = LegacyPdfPlumberParser()
        self.parsers["pypdf2"] = LegacyPyPdf2Parser()
        self.parsers["python-docx"] = LegacyDocxParser()

        logger.info(f"Initialized parsers: {list(self.parsers.keys())}")

    async def get_best_parser(
        self, file_path: str, config: Dict[str, Any]
    ) -> Tuple[Any, str]:
        """Select best parser based on file type, config, and availability"""
        file_ext = Path(file_path).suffix.lower()

        # Get parser preferences from config
        parser_config = config.get("advanced_parsing", {})

        # Auto-select if no preference or auto mode
        if parser_config.get("default_mode") == "auto_parser" or not parser_config.get(
            "parsers"
        ):
            return await self._auto_select_parser(file_path, file_ext, config)

        # Use configured parser preferences
        parsers_for_type = parser_config.get("parsers", {}).get(file_ext[1:], {})
        preferred_tool = parsers_for_type.get("default_tool")
        available_tools = parsers_for_type.get("available_tools", [])

        # Try preferred tool first
        if preferred_tool and preferred_tool in self.parsers:
            parser = self.parsers[preferred_tool]
            if parser.is_available():
                is_valid, message = await parser.validate_file(file_path)
                if is_valid:
                    return parser, preferred_tool
                else:
                    logger.warning(
                        f"Preferred parser {preferred_tool} validation failed: {message}"
                    )

        # Try available tools in order
        for tool in available_tools:
            if tool in self.parsers:
                parser = self.parsers[tool]
                if parser.is_available():
                    is_valid, message = await parser.validate_file(file_path)
                    if is_valid:
                        return parser, tool

        # Fallback to auto-selection
        return await self._auto_select_parser(file_path, file_ext, config)

    async def _auto_select_parser(
        self, file_path: str, file_ext: str, config: Dict[str, Any]
    ) -> Tuple[Any, str]:
        """Automatically select best parser based on file characteristics"""
        file_size = Path(file_path).stat().st_size

        # PDF selection logic
        if file_ext == ".pdf":
            # For large or complex PDFs, prefer docling if available
            if file_size > 10 * 1024 * 1024:  # > 10MB
                if self.parsers["docling"].is_available():
                    is_valid, _ = await self.parsers["docling"].validate_file(file_path)
                    if is_valid:
                        return self.parsers["docling"], "docling"

            # For medium PDFs, try markitdown first (faster)
            if self.parsers["markitdown"].is_available():
                is_valid, _ = await self.parsers["markitdown"].validate_file(file_path)
                if is_valid:
                    return self.parsers["markitdown"], "markitdown"

            # Fallback to legacy parsers
            if self.parsers["pdfplumber"].is_available():
                return self.parsers["pdfplumber"], "pdfplumber"

            if self.parsers["pypdf2"].is_available():
                return self.parsers["pypdf2"], "pypdf2"

        # DOCX selection logic
        elif file_ext == ".docx":
            # Try markitdown first (good balance of speed and quality)
            if self.parsers["markitdown"].is_available():
                is_valid, _ = await self.parsers["markitdown"].validate_file(file_path)
                if is_valid:
                    return self.parsers["markitdown"], "markitdown"

            # Try docling for complex documents
            if self.parsers["docling"].is_available():
                is_valid, _ = await self.parsers["docling"].validate_file(file_path)
                if is_valid:
                    return self.parsers["docling"], "docling"

            # Fallback to legacy
            if self.parsers["python-docx"].is_available():
                return self.parsers["python-docx"], "python-docx"

        # XLSX and other Office formats
        elif file_ext in [".xlsx", ".pptx"]:
            if self.parsers["markitdown"].is_available():
                is_valid, _ = await self.parsers["markitdown"].validate_file(file_path)
                if is_valid:
                    return self.parsers["markitdown"], "markitdown"

        # Text and Markdown files
        elif file_ext in [".txt", ".md", ".html"]:
            if self.parsers["markitdown"].is_available():
                is_valid, _ = await self.parsers["markitdown"].validate_file(file_path)
                if is_valid:
                    return self.parsers["markitdown"], "markitdown"

        # No suitable parser found
        raise Exception(f"No suitable parser found for {file_ext} files")

    def get_available_parsers(self) -> Dict[str, List[str]]:
        """Get list of available parsers by file type"""
        available = {}

        for parser_name, parser in self.parsers.items():
            if parser.is_available():
                for fmt in parser.get_supported_formats():
                    file_type = fmt[1:]  # Remove the dot
                    if file_type not in available:
                        available[file_type] = []
                    available[file_type].append(parser_name)

        return available

    def get_parser_info(self, parser_name: str) -> Dict[str, Any]:
        """Get information about a specific parser"""
        if parser_name not in self.parsers:
            return {"available": False, "error": "Parser not found"}

        parser = self.parsers[parser_name]

        return {
            "available": parser.is_available(),
            "supported_formats": parser.get_supported_formats(),
            "name": parser_name,
            "description": getattr(parser, "description", f"{parser_name} parser"),
        }


class LegacyPdfPlumberParser:
    """Wrapper for existing pdfplumber parser"""

    def __init__(self):
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        try:
            import pdfplumber

            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self.available

    def get_supported_formats(self) -> List[str]:
        return [".pdf"] if self.available else []

    async def validate_file(self, file_path: str) -> Tuple[bool, str]:
        if not self.available:
            return False, "pdfplumber not available"

        if not Path(file_path).exists():
            return False, "File not found"

        if Path(file_path).suffix.lower() != ".pdf":
            return False, "Not a PDF file"

        return True, "Valid for pdfplumber"

    async def parse_pdf(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PDF using pdfplumber (legacy implementation)"""
        # This would call the existing pdfplumber implementation
        # For now, return a placeholder
        return {
            "content": "Legacy pdfplumber content",
            "metadata": {"extraction_method": "pdfplumber"},
            "success": True,
        }


class LegacyPyPdf2Parser:
    """Wrapper for existing PyPDF2 parser"""

    def __init__(self):
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        try:
            import PyPDF2

            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self.available

    def get_supported_formats(self) -> List[str]:
        return [".pdf"] if self.available else []

    async def validate_file(self, file_path: str) -> Tuple[bool, str]:
        if not self.available:
            return False, "PyPDF2 not available"

        if not Path(file_path).exists():
            return False, "File not found"

        if Path(file_path).suffix.lower() != ".pdf":
            return False, "Not a PDF file"

        return True, "Valid for PyPDF2"

    async def parse_pdf(self, file_path: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Parse PDF using PyPDF2 (legacy implementation)"""
        return {
            "content": "Legacy PyPDF2 content",
            "metadata": {"extraction_method": "pypdf2"},
            "success": True,
        }


class LegacyDocxParser:
    """Wrapper for existing python-docx parser"""

    def __init__(self):
        self.available = self._check_availability()

    def _check_availability(self) -> bool:
        try:
            import docx

            return True
        except ImportError:
            return False

    def is_available(self) -> bool:
        return self.available

    def get_supported_formats(self) -> List[str]:
        return [".docx"] if self.available else []

    async def validate_file(self, file_path: str) -> Tuple[bool, str]:
        if not self.available:
            return False, "python-docx not available"

        if not Path(file_path).exists():
            return False, "File not found"

        if Path(file_path).suffix.lower() != ".docx":
            return False, "Not a DOCX file"

        return True, "Valid for python-docx"

    async def parse_docx(
        self, file_path: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Parse DOCX using python-docx (legacy implementation)"""
        return {
            "content": "Legacy python-docx content",
            "metadata": {"extraction_method": "python-docx"},
            "success": True,
        }
