"""
Enhanced Configuration System for Tokenizer Steps

This module provides a unified configuration system that supports both simple
(existing) and advanced (elevaite_ingestion-style) configuration modes.

The system maintains backward compatibility while enabling access to advanced
features like docling parsing, semantic chunking, and multi-provider support.
"""

from typing import Dict, Any, Optional, Union, List
from pydantic import BaseModel, Field
from enum import Enum


class ExecutionMode(str, Enum):
    """Execution mode for tokenizer steps"""
    SIMPLE = "simple"
    ADVANCED = "advanced"
    ELEVAITE_DIRECT = "elevaite_direct"


class AdvancedParsingConfig(BaseModel):
    """Advanced parsing configuration matching elevaite_ingestion"""
    default_mode: str = Field(default="auto_parser", description="Default parsing mode")
    custom_parser_selection: Optional[Dict[str, Any]] = Field(
        default=None, description="Custom parser selection configuration"
    )
    parsers: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Parser configurations by file type"
    )
    
    # Elevaite_ingestion specific options
    use_docling: bool = Field(default=False, description="Enable docling parser")
    use_markitdown: bool = Field(default=True, description="Enable markitdown parser")
    auto_detect_format: bool = Field(default=True, description="Auto-detect file format")


class AdvancedChunkingConfig(BaseModel):
    """Advanced chunking with elevaite_ingestion strategies"""
    default_strategy: str = Field(default="recursive_chunking", description="Default chunking strategy")
    strategies: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Strategy configurations"
    )
    
    # New strategies from elevaite_ingestion
    semantic_chunking: Optional[Dict[str, Any]] = Field(
        default=None, description="Semantic chunking configuration"
    )
    mdstructure: Optional[Dict[str, Any]] = Field(
        default=None, description="Markdown structure chunking configuration"
    )
    sentence_chunking: Optional[Dict[str, Any]] = Field(
        default=None, description="Sentence-based chunking configuration"
    )


class AdvancedEmbeddingConfig(BaseModel):
    """Advanced embedding configuration with multiple providers"""
    default_provider: str = Field(default="openai", description="Default embedding provider")
    default_model: str = Field(default="text-embedding-ada-002", description="Default model")
    providers: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Provider configurations"
    )


class AdvancedStorageConfig(BaseModel):
    """Advanced vector storage configuration"""
    default_db: str = Field(default="qdrant", description="Default vector database")
    databases: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, description="Database configurations"
    )


class EnhancedTokenizerConfig(BaseModel):
    """Enhanced configuration supporting both simple and advanced modes"""
    
    # Execution mode
    execution_mode: ExecutionMode = Field(default=ExecutionMode.SIMPLE, description="Execution mode")
    
    # Backward compatibility - simple mode config
    simple_config: Optional[Dict[str, Any]] = Field(
        default=None, description="Simple mode configuration (backward compatibility)"
    )
    
    # Advanced mode configurations
    advanced_parsing: Optional[AdvancedParsingConfig] = Field(
        default=None, description="Advanced parsing configuration"
    )
    advanced_chunking: Optional[AdvancedChunkingConfig] = Field(
        default=None, description="Advanced chunking configuration"
    )
    advanced_embedding: Optional[AdvancedEmbeddingConfig] = Field(
        default=None, description="Advanced embedding configuration"
    )
    advanced_storage: Optional[AdvancedStorageConfig] = Field(
        default=None, description="Advanced storage configuration"
    )
    
    # Global settings
    timeout_seconds: Optional[int] = Field(default=None, description="Global timeout")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    batch_size: Optional[int] = Field(default=None, description="Default batch size")


class ConfigDefaults:
    """Default configurations for various modes"""
    
    @staticmethod
    def get_simple_defaults() -> Dict[str, Any]:
        """Get default simple mode configuration"""
        return {
            "execution_mode": ExecutionMode.SIMPLE,
            "simple_config": {
                "supported_formats": [".pdf", ".docx", ".txt", ".md", ".html"],
                "max_file_size": 52428800,  # 50MB
                "encoding": "utf-8",
                "chunk_strategy": "sliding_window",
                "chunk_size": 1000,
                "overlap": 0.2,
                "provider": "openai",
                "model": "text-embedding-3-small",
                "vector_db": "qdrant"
            }
        }
    
    @staticmethod
    def get_advanced_defaults() -> Dict[str, Any]:
        """Get default advanced mode configuration"""
        return {
            "execution_mode": ExecutionMode.ADVANCED,
            "advanced_parsing": AdvancedParsingConfig(
                default_mode="auto_parser",
                parsers={
                    "pdf": {
                        "default_tool": "docling",
                        "available_tools": ["docling", "pdfplumber", "pypdf2"]
                    },
                    "docx": {
                        "default_tool": "markitdown",
                        "available_tools": ["markitdown", "docling"]
                    }
                }
            ),
            "advanced_chunking": AdvancedChunkingConfig(
                default_strategy="semantic_chunking",
                strategies={
                    "semantic_chunking": {
                        "breakpoint_threshold_type": "percentile",
                        "breakpoint_threshold_amount": 85
                    },
                    "recursive_chunking": {
                        "chunk_size": 1000,
                        "chunk_overlap": 200
                    }
                }
            ),
            "advanced_embedding": AdvancedEmbeddingConfig(
                default_provider="openai",
                default_model="text-embedding-3-small",
                providers={
                    "openai": {
                        "models": {
                            "text-embedding-3-small": {"description": "OpenAI small embedding model"},
                            "text-embedding-ada-002": {"description": "OpenAI ada embedding model"}
                        }
                    }
                }
            ),
            "advanced_storage": AdvancedStorageConfig(
                default_db="qdrant",
                databases={
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "enhanced_documents"
                    }
                }
            )
        }
    
    @staticmethod
    def get_elevaite_defaults() -> Dict[str, Any]:
        """Get default elevaite_ingestion compatible configuration"""
        return {
            "execution_mode": ExecutionMode.ELEVAITE_DIRECT,
            "loading": {
                "default_source": "local",
                "sources": {
                    "local": {
                        "input_directory": "./input",
                        "output_directory": "./output"
                    }
                }
            },
            "parsing": {
                "default_mode": "auto_parser",
                "parsers": {
                    "pdf": {"default_tool": "docling", "available_tools": ["docling"]},
                    "docx": {"default_tool": "markitdown", "available_tools": ["markitdown", "docling"]}
                }
            },
            "chunking": {
                "default_strategy": "semantic_chunking",
                "strategies": {
                    "semantic_chunking": {
                        "breakpoint_threshold_type": "percentile",
                        "breakpoint_threshold_amount": 85
                    }
                }
            },
            "embedding": {
                "default_provider": "openai",
                "default_model": "text-embedding-3-small",
                "providers": {
                    "openai": {
                        "models": {
                            "text-embedding-3-small": {"description": "OpenAI small embedding model"}
                        }
                    }
                }
            },
            "vector_db": {
                "default_db": "qdrant",
                "databases": {
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "elevaite_documents"
                    }
                }
            }
        }
