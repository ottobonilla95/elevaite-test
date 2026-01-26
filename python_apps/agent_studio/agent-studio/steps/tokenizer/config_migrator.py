"""
Configuration Migration System for Tokenizer Steps

This module provides utilities to convert between different configuration formats:
- Simple tokenizer config ↔ Enhanced tokenizer config
- Elevaite_ingestion config ↔ Enhanced tokenizer config
- Auto-detection of configuration format
"""

from typing import Dict, Any
import logging
from .enhanced_config import (
    EnhancedTokenizerConfig,
    AdvancedParsingConfig,
    AdvancedChunkingConfig,
    AdvancedEmbeddingConfig,
    AdvancedStorageConfig,
    ExecutionMode,
    ConfigDefaults
)

logger = logging.getLogger(__name__)


class ConfigDetector:
    """Detects configuration format and execution mode"""
    
    @staticmethod
    def detect_mode(config: Dict[str, Any]) -> ExecutionMode:
        """Detect configuration mode from config structure"""
        
        # Check for explicit mode setting
        if "execution_mode" in config:
            return ExecutionMode(config["execution_mode"])
        
        if config.get("advanced_mode", False):
            return ExecutionMode.ADVANCED
        
        # Check for elevaite_ingestion style config keys
        elevaite_keys = ["loading", "parsing", "chunking", "embedding", "vector_db"]
        if any(key in config for key in elevaite_keys):
            return ExecutionMode.ELEVAITE_DIRECT
        
        # Check for advanced tokenizer config keys
        advanced_keys = ["advanced_parsing", "advanced_chunking", "advanced_embedding", "advanced_storage"]
        if any(key in config for key in advanced_keys):
            return ExecutionMode.ADVANCED
        
        # Check for tokenizer_step hint (indicates simple tokenizer mode)
        if "tokenizer_step" in config:
            return ExecutionMode.SIMPLE
        
        # Default to simple mode
        return ExecutionMode.SIMPLE
    
    @staticmethod
    def is_elevaite_config(config: Dict[str, Any]) -> bool:
        """Check if config is in elevaite_ingestion format"""
        elevaite_keys = ["loading", "parsing", "chunking", "embedding", "vector_db"]
        return any(key in config for key in elevaite_keys)
    
    @staticmethod
    def is_simple_tokenizer_config(config: Dict[str, Any]) -> bool:
        """Check if config is simple tokenizer format"""
        return "tokenizer_step" in config or ConfigDetector.detect_mode(config) == ExecutionMode.SIMPLE


class ConfigMigrator:
    """Converts between different configuration formats"""
    
    @staticmethod
    def from_elevaite_config(elevaite_config: Dict[str, Any]) -> EnhancedTokenizerConfig:
        """Convert elevaite_ingestion config to enhanced tokenizer config"""
        try:
            # Extract parsing config
            parsing_config = elevaite_config.get("parsing", {})
            advanced_parsing = AdvancedParsingConfig(
                default_mode=parsing_config.get("default_mode", "auto_parser"),
                custom_parser_selection=parsing_config.get("custom_parser_selection"),
                parsers=parsing_config.get("parsers", {}),
                use_docling="docling" in str(parsing_config).lower(),
                use_markitdown="markitdown" in str(parsing_config).lower(),
                auto_detect_format=parsing_config.get("default_mode") == "auto_parser"
            )
            
            # Extract chunking config
            chunking_config = elevaite_config.get("chunking", {})
            advanced_chunking = AdvancedChunkingConfig(
                default_strategy=chunking_config.get("default_strategy", "recursive_chunking"),
                strategies=chunking_config.get("strategies", {}),
                semantic_chunking=chunking_config.get("strategies", {}).get("semantic_chunking"),
                mdstructure=chunking_config.get("strategies", {}).get("mdstructure"),
                sentence_chunking=chunking_config.get("strategies", {}).get("sentence_chunking")
            )
            
            # Extract embedding config
            embedding_config = elevaite_config.get("embedding", {})
            advanced_embedding = AdvancedEmbeddingConfig(
                default_provider=embedding_config.get("default_provider", "openai"),
                default_model=embedding_config.get("default_model", "text-embedding-ada-002"),
                providers=embedding_config.get("providers", {})
            )
            
            # Extract storage config
            storage_config = elevaite_config.get("vector_db", {})
            advanced_storage = AdvancedStorageConfig(
                default_db=storage_config.get("default_db", "qdrant"),
                databases=storage_config.get("databases", {})
            )
            
            return EnhancedTokenizerConfig(
                execution_mode=ExecutionMode.ELEVAITE_DIRECT,
                advanced_parsing=advanced_parsing,
                advanced_chunking=advanced_chunking,
                advanced_embedding=advanced_embedding,
                advanced_storage=advanced_storage
            )
            
        except Exception as e:
            logger.error(f"Failed to convert elevaite config: {e}")
            # Return default advanced config as fallback
            return EnhancedTokenizerConfig(**ConfigDefaults.get_advanced_defaults())
    
    @staticmethod
    def to_elevaite_config(enhanced_config: EnhancedTokenizerConfig) -> Dict[str, Any]:
        """Convert enhanced tokenizer config to elevaite_ingestion format"""
        config = {}
        
        # Convert parsing config
        if enhanced_config.advanced_parsing:
            config["parsing"] = {
                "default_mode": enhanced_config.advanced_parsing.default_mode,
                "parsers": enhanced_config.advanced_parsing.parsers
            }
            if enhanced_config.advanced_parsing.custom_parser_selection:
                config["parsing"]["custom_parser_selection"] = enhanced_config.advanced_parsing.custom_parser_selection
        
        # Convert chunking config
        if enhanced_config.advanced_chunking:
            config["chunking"] = {
                "default_strategy": enhanced_config.advanced_chunking.default_strategy,
                "strategies": enhanced_config.advanced_chunking.strategies
            }
        
        # Convert embedding config
        if enhanced_config.advanced_embedding:
            config["embedding"] = {
                "default_provider": enhanced_config.advanced_embedding.default_provider,
                "default_model": enhanced_config.advanced_embedding.default_model,
                "providers": enhanced_config.advanced_embedding.providers
            }
        
        # Convert storage config
        if enhanced_config.advanced_storage:
            config["vector_db"] = {
                "default_db": enhanced_config.advanced_storage.default_db,
                "databases": enhanced_config.advanced_storage.databases
            }
        
        return config
    
    @staticmethod
    def from_simple_config(simple_config: Dict[str, Any]) -> EnhancedTokenizerConfig:
        """Convert simple tokenizer config to enhanced config"""
        return EnhancedTokenizerConfig(
            execution_mode=ExecutionMode.SIMPLE,
            simple_config=simple_config,
            timeout_seconds=simple_config.get("timeout_seconds"),
            max_retries=simple_config.get("max_retries", 3),
            batch_size=simple_config.get("batch_size")
        )
    
    @staticmethod
    def to_simple_config(enhanced_config: EnhancedTokenizerConfig) -> Dict[str, Any]:
        """Convert enhanced config back to simple tokenizer format"""
        if enhanced_config.simple_config:
            return enhanced_config.simple_config
        
        # Generate simple config from advanced config
        simple_config = {}
        
        if enhanced_config.advanced_parsing:
            simple_config.update({
                "supported_formats": [".pdf", ".docx", ".txt", ".md", ".html"],
                "max_file_size": 52428800,
                "encoding": "utf-8"
            })
        
        if enhanced_config.advanced_chunking:
            strategy = enhanced_config.advanced_chunking.default_strategy
            if strategy == "semantic_chunking":
                simple_config["chunk_strategy"] = "semantic"
            elif strategy == "recursive_chunking":
                simple_config["chunk_strategy"] = "sliding_window"
            else:
                simple_config["chunk_strategy"] = "fixed_size"
            
            # Get chunk size from strategy config
            strategies = enhanced_config.advanced_chunking.strategies
            if strategy in strategies:
                strategy_config = strategies[strategy]
                simple_config["chunk_size"] = strategy_config.get("chunk_size", 1000)
                simple_config["overlap"] = strategy_config.get("chunk_overlap", 200) / simple_config["chunk_size"]
        
        if enhanced_config.advanced_embedding:
            simple_config.update({
                "provider": enhanced_config.advanced_embedding.default_provider,
                "model": enhanced_config.advanced_embedding.default_model
            })
        
        if enhanced_config.advanced_storage:
            simple_config["vector_db"] = enhanced_config.advanced_storage.default_db
        
        return simple_config
    
    @staticmethod
    def auto_migrate(config: Dict[str, Any]) -> EnhancedTokenizerConfig:
        """Automatically detect and migrate any config format to enhanced format"""
        mode = ConfigDetector.detect_mode(config)
        
        if mode == ExecutionMode.ELEVAITE_DIRECT:
            return ConfigMigrator.from_elevaite_config(config)
        elif mode == ExecutionMode.SIMPLE:
            return ConfigMigrator.from_simple_config(config)
        elif mode == ExecutionMode.ADVANCED:
            # Already in enhanced format, validate and return
            try:
                return EnhancedTokenizerConfig(**config)
            except Exception as e:
                logger.warning(f"Invalid enhanced config, using defaults: {e}")
                return EnhancedTokenizerConfig(**ConfigDefaults.get_advanced_defaults())
        else:
            # Fallback to simple mode
            return ConfigMigrator.from_simple_config(config)


class ConfigValidator:
    """Validates configuration completeness and correctness"""
    
    @staticmethod
    def validate_enhanced_config(config: EnhancedTokenizerConfig) -> Dict[str, Any]:
        """Validate enhanced configuration and return validation results"""
        results = {
            "valid": True,
            "warnings": [],
            "errors": [],
            "suggestions": []
        }
        
        # Check execution mode consistency
        if config.execution_mode == ExecutionMode.SIMPLE and not config.simple_config:
            results["warnings"].append("Simple mode specified but no simple_config provided")
        
        if config.execution_mode == ExecutionMode.ADVANCED:
            if not any([config.advanced_parsing, config.advanced_chunking, 
                       config.advanced_embedding, config.advanced_storage]):
                results["warnings"].append("Advanced mode specified but no advanced configs provided")
        
        # Validate parsing config
        if config.advanced_parsing:
            if config.advanced_parsing.use_docling:
                results["suggestions"].append("Docling enabled - ensure docling package is installed")
        
        # Validate chunking config
        if config.advanced_chunking:
            if config.advanced_chunking.default_strategy == "semantic_chunking":
                results["suggestions"].append("Semantic chunking requires sentence-transformers package")
        
        # Validate embedding config
        if config.advanced_embedding:
            provider = config.advanced_embedding.default_provider
            if provider == "amazon_bedrock":
                results["suggestions"].append("Bedrock provider requires AWS credentials")
            elif provider == "sentence_transformers":
                results["suggestions"].append("Sentence transformers provider requires local model download")
        
        return results
