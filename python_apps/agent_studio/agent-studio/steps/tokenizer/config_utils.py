"""
Configuration Utilities for Enhanced Tokenizer Steps

This module provides utility functions for working with enhanced tokenizer configurations,
including merging configs, extracting step-specific settings, and handling defaults.
"""

from typing import Dict, Any, Optional, Union
import os
import json
import logging
from pathlib import Path

from .enhanced_config import (
    EnhancedTokenizerConfig,
    ExecutionMode,
    ConfigDefaults
)
from .config_migrator import ConfigMigrator

logger = logging.getLogger(__name__)


class ConfigUtils:
    """Utility functions for configuration management"""
    
    @staticmethod
    def merge_configs(base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two configuration dictionaries, with override taking precedence"""
        merged = base_config.copy()
        
        for key, value in override_config.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = ConfigUtils.merge_configs(merged[key], value)
            else:
                merged[key] = value
        
        return merged
    
    @staticmethod
    def extract_step_config(enhanced_config: EnhancedTokenizerConfig, step_type: str) -> Dict[str, Any]:
        """Extract configuration specific to a step type"""
        step_config = {}
        
        # Add global settings
        if enhanced_config.timeout_seconds:
            step_config["timeout_seconds"] = enhanced_config.timeout_seconds
        if enhanced_config.max_retries:
            step_config["max_retries"] = enhanced_config.max_retries
        if enhanced_config.batch_size:
            step_config["batch_size"] = enhanced_config.batch_size
        
        # Add execution mode
        step_config["execution_mode"] = enhanced_config.execution_mode
        
        # Add step-specific config based on type
        if step_type == "file_reader" and enhanced_config.advanced_parsing:
            step_config["advanced_parsing"] = enhanced_config.advanced_parsing.dict()
        
        elif step_type == "text_chunking" and enhanced_config.advanced_chunking:
            step_config["advanced_chunking"] = enhanced_config.advanced_chunking.dict()
        
        elif step_type == "embedding_generation" and enhanced_config.advanced_embedding:
            step_config["advanced_embedding"] = enhanced_config.advanced_embedding.dict()
        
        elif step_type == "vector_storage" and enhanced_config.advanced_storage:
            step_config["advanced_storage"] = enhanced_config.advanced_storage.dict()
        
        # Add simple config if in simple mode
        if enhanced_config.execution_mode == ExecutionMode.SIMPLE and enhanced_config.simple_config:
            step_config.update(enhanced_config.simple_config)
        
        return step_config
    
    @staticmethod
    def load_config_from_file(file_path: Union[str, Path]) -> EnhancedTokenizerConfig:
        """Load configuration from JSON file"""
        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)
            
            return ConfigMigrator.auto_migrate(config_data)
        
        except FileNotFoundError:
            logger.warning(f"Config file not found: {file_path}, using defaults")
            return EnhancedTokenizerConfig(**ConfigDefaults.get_simple_defaults())
        
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {file_path}: {e}")
            return EnhancedTokenizerConfig(**ConfigDefaults.get_simple_defaults())
        
        except Exception as e:
            logger.error(f"Error loading config from {file_path}: {e}")
            return EnhancedTokenizerConfig(**ConfigDefaults.get_simple_defaults())
    
    @staticmethod
    def save_config_to_file(config: EnhancedTokenizerConfig, file_path: Union[str, Path]) -> bool:
        """Save configuration to JSON file"""
        try:
            config_dict = config.dict(exclude_none=True)
            
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2, default=str)
            
            return True
        
        except Exception as e:
            logger.error(f"Error saving config to {file_path}: {e}")
            return False
    
    @staticmethod
    def get_environment_overrides() -> Dict[str, Any]:
        """Get configuration overrides from environment variables"""
        overrides = {}
        
        # Check for common environment variables
        if os.getenv("OPENAI_API_KEY"):
            overrides.setdefault("advanced_embedding", {}).setdefault("providers", {}).setdefault("openai", {})["api_key"] = os.getenv("OPENAI_API_KEY")
        
        if os.getenv("QDRANT_HOST"):
            overrides.setdefault("advanced_storage", {}).setdefault("databases", {}).setdefault("qdrant", {})["host"] = os.getenv("QDRANT_HOST")
        
        if os.getenv("QDRANT_PORT"):
            overrides.setdefault("advanced_storage", {}).setdefault("databases", {}).setdefault("qdrant", {})["port"] = int(os.getenv("QDRANT_PORT"))
        
        if os.getenv("PINECONE_API_KEY"):
            overrides.setdefault("advanced_storage", {}).setdefault("databases", {}).setdefault("pinecone", {})["api_key"] = os.getenv("PINECONE_API_KEY")
        
        # AWS Bedrock settings
        if os.getenv("AWS_REGION"):
            overrides.setdefault("advanced_embedding", {}).setdefault("providers", {}).setdefault("amazon_bedrock", {})["aws_region"] = os.getenv("AWS_REGION")
        
        return overrides
    
    @staticmethod
    def apply_environment_overrides(config: EnhancedTokenizerConfig) -> EnhancedTokenizerConfig:
        """Apply environment variable overrides to configuration"""
        env_overrides = ConfigUtils.get_environment_overrides()
        
        if not env_overrides:
            return config
        
        # Convert config to dict, apply overrides, convert back
        config_dict = config.dict()
        merged_dict = ConfigUtils.merge_configs(config_dict, env_overrides)
        
        try:
            return EnhancedTokenizerConfig(**merged_dict)
        except Exception as e:
            logger.warning(f"Failed to apply environment overrides: {e}")
            return config


class StepConfigBuilder:
    """Builder for creating step-specific configurations"""
    
    def __init__(self, base_config: Optional[EnhancedTokenizerConfig] = None):
        self.base_config = base_config or EnhancedTokenizerConfig(**ConfigDefaults.get_simple_defaults())
    
    def for_file_reader(self, **overrides) -> Dict[str, Any]:
        """Build configuration for FileReaderStep"""
        config = ConfigUtils.extract_step_config(self.base_config, "file_reader")
        config.update(overrides)
        return config
    
    def for_text_chunking(self, **overrides) -> Dict[str, Any]:
        """Build configuration for TextChunkingStep"""
        config = ConfigUtils.extract_step_config(self.base_config, "text_chunking")
        config.update(overrides)
        return config
    
    def for_embedding_generation(self, **overrides) -> Dict[str, Any]:
        """Build configuration for EmbeddingGenerationStep"""
        config = ConfigUtils.extract_step_config(self.base_config, "embedding_generation")
        config.update(overrides)
        return config
    
    def for_vector_storage(self, **overrides) -> Dict[str, Any]:
        """Build configuration for VectorStorageStep"""
        config = ConfigUtils.extract_step_config(self.base_config, "vector_storage")
        config.update(overrides)
        return config


class ConfigTemplates:
    """Pre-defined configuration templates for common use cases"""
    
    @staticmethod
    def basic_pdf_processing() -> Dict[str, Any]:
        """Template for basic PDF processing with OpenAI embeddings"""
        return {
            "execution_mode": "advanced",
            "advanced_parsing": {
                "default_mode": "auto_parser",
                "parsers": {
                    "pdf": {
                        "default_tool": "pdfplumber",
                        "available_tools": ["pdfplumber", "pypdf2"]
                    }
                }
            },
            "advanced_chunking": {
                "default_strategy": "recursive_chunking",
                "strategies": {
                    "recursive_chunking": {
                        "chunk_size": 1000,
                        "chunk_overlap": 200
                    }
                }
            },
            "advanced_embedding": {
                "default_provider": "openai",
                "default_model": "text-embedding-3-small"
            },
            "advanced_storage": {
                "default_db": "qdrant",
                "databases": {
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "pdf_documents"
                    }
                }
            }
        }
    
    @staticmethod
    def advanced_pdf_processing() -> Dict[str, Any]:
        """Template for advanced PDF processing with docling and semantic chunking"""
        return {
            "execution_mode": "advanced",
            "advanced_parsing": {
                "default_mode": "auto_parser",
                "parsers": {
                    "pdf": {
                        "default_tool": "docling",
                        "available_tools": ["docling", "pdfplumber"]
                    }
                },
                "use_docling": True
            },
            "advanced_chunking": {
                "default_strategy": "semantic_chunking",
                "strategies": {
                    "semantic_chunking": {
                        "breakpoint_threshold_type": "percentile",
                        "breakpoint_threshold_amount": 85
                    }
                }
            },
            "advanced_embedding": {
                "default_provider": "openai",
                "default_model": "text-embedding-3-small"
            },
            "advanced_storage": {
                "default_db": "qdrant",
                "databases": {
                    "qdrant": {
                        "host": "localhost",
                        "port": 6333,
                        "collection_name": "advanced_documents"
                    }
                }
            }
        }
    
    @staticmethod
    def local_processing() -> Dict[str, Any]:
        """Template for local processing with sentence transformers"""
        return {
            "execution_mode": "advanced",
            "advanced_parsing": {
                "default_mode": "auto_parser"
            },
            "advanced_chunking": {
                "default_strategy": "recursive_chunking",
                "strategies": {
                    "recursive_chunking": {
                        "chunk_size": 512,
                        "chunk_overlap": 50
                    }
                }
            },
            "advanced_embedding": {
                "default_provider": "sentence_transformers",
                "default_model": "all-MiniLM-L6-v2"
            },
            "advanced_storage": {
                "default_db": "chroma",
                "databases": {
                    "chroma": {
                        "db_path": "./chroma_db",
                        "collection_name": "local_documents"
                    }
                }
            }
        }
