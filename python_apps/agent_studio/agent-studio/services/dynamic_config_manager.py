import os
import json
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class LoadingConfig:
    """Configuration for data loading stage"""

    default_source: str = "local"
    s3_bucket_name: str = "kb-check-pdf"
    s3_region: str = "us-east-2"
    local_input_directory: str = "/tmp/input"
    local_output_directory: str = "/tmp/output"


@dataclass
class ParsingConfig:
    """Configuration for document parsing stage"""

    default_mode: str = "auto_parser"
    default_parser: str = "pdf"
    default_tool: Optional[str] = None
    custom_parser_selection: Optional[Dict[str, Any]] = None

    def __post_init__(self):
        if self.custom_parser_selection is None:
            self.custom_parser_selection = {}


@dataclass
class ChunkingConfig:
    """Configuration for text chunking stage"""

    default_strategy: str = "recursive_chunking"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    semantic_breakpoint_threshold_type: str = "percentile"
    semantic_breakpoint_threshold_amount: int = 85
    mdstructure_chunk_size: int = 1500
    sentence_max_chunk_size: int = 2000


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation stage"""

    default_provider: str = "openai"
    default_model: str = "text-embedding-3-small"
    openai_api_key: Optional[str] = None
    batch_size: int = 100

    def __post_init__(self):
        if self.openai_api_key is None:
            self.openai_api_key = os.getenv("OPENAI_API_KEY")


@dataclass
class VectorDBConfig:
    """Configuration for vector database storage stage"""

    default_db: str = "qdrant"
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_collection_name: str = "documents"
    pinecone_api_key: Optional[str] = None
    pinecone_index_name: str = "kb-final10"
    pinecone_dimension: int = 1536
    chroma_db_path: str = "data/chroma_db"
    chroma_collection_name: str = "kb-chroma"


@dataclass
class PipelineConfig:
    """Complete pipeline configuration"""

    loading: LoadingConfig
    parsing: ParsingConfig
    chunking: ChunkingConfig
    embedding: EmbeddingConfig
    vector_db: VectorDBConfig

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format"""
        return asdict(self)

    def to_elevaite_ingestion_format(self) -> Dict[str, Any]:
        """Convert to elevaite_ingestion compatible format"""
        return {
            "loading": {
                "default_source": self.loading.default_source,
                "sources": {
                    "s3": {
                        "bucket_name": self.loading.s3_bucket_name,
                        "region": self.loading.s3_region,
                    },
                    "local": {
                        "input_directory": self.loading.local_input_directory,
                        "output_directory": self.loading.local_output_directory,
                    },
                },
            },
            "parsing": {
                "default_mode": self.parsing.default_mode,
                "custom_parser_selection": self.parsing.custom_parser_selection,
                "parsers": {
                    "docx": {
                        "default_tool": "markitdown",
                        "available_tools": ["markitdown", "docling"],
                    },
                    "xlsx": {
                        "default_tool": "markitdown",
                        "available_tools": ["markitdown", "docling"],
                    },
                    "url": {
                        "default_tool": "markitdown",
                        "available_tools": ["markitdown", "crawl4ai"],
                    },
                    "pdf": {
                        "default_tool": self.parsing.default_tool,
                        "available_tools": [],
                    },
                },
            },
            "chunking": {
                "default_strategy": self.chunking.default_strategy,
                "strategies": {
                    "semantic_chunking": {
                        "breakpoint_threshold_type": self.chunking.semantic_breakpoint_threshold_type,
                        "breakpoint_threshold_amount": self.chunking.semantic_breakpoint_threshold_amount,
                    },
                    "mdstructure": {"chunk_size": self.chunking.mdstructure_chunk_size},
                    "recursive_chunking": {
                        "chunk_size": self.chunking.chunk_size,
                        "chunk_overlap": self.chunking.chunk_overlap,
                    },
                    "sentence_chunking": {
                        "max_chunk_size": self.chunking.sentence_max_chunk_size
                    },
                },
            },
            "embedding": {
                "default_provider": self.embedding.default_provider,
                "default_model": self.embedding.default_model,
                "providers": {
                    "openai": {
                        "api_key": self.embedding.openai_api_key,
                        "models": {
                            "text-embedding-ada-002": {
                                "description": "OpenAI's ada embedding model"
                            },
                            "text-embedding-3-small": {
                                "description": "OpenAI's small embedding model"
                            },
                            "text-embedding-3-large": {
                                "description": "OpenAI's large embedding model"
                            },
                        },
                    }
                },
            },
            "vector_db": {
                "default_db": self.vector_db.default_db,
                "databases": {
                    "qdrant": {
                        "host": self.vector_db.qdrant_host,
                        "port": self.vector_db.qdrant_port,
                        "collection_name": self.vector_db.qdrant_collection_name,
                    },
                    "pinecone": {
                        "api_key": self.vector_db.pinecone_api_key,
                        "index_name": self.vector_db.pinecone_index_name,
                        "dimension": self.vector_db.pinecone_dimension,
                    },
                    "chroma": {
                        "db_path": self.vector_db.chroma_db_path,
                        "collection_name": self.vector_db.chroma_collection_name,
                    },
                },
            },
        }


class DynamicConfigManager:
    """
    Dynamic configuration manager that provides runtime configuration
    customization for pipeline execution.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._default_config = self._create_default_config()

    def _create_default_config(self) -> PipelineConfig:
        """Create default configuration with environment variable support"""
        return PipelineConfig(
            loading=LoadingConfig(
                default_source=os.getenv("DEFAULT_LOADING_SOURCE", "local"),
                s3_bucket_name=os.getenv("S3_BUCKET_NAME", "kb-check-pdf"),
                s3_region=os.getenv("S3_REGION", "us-east-2"),
                local_input_directory=os.getenv("LOCAL_INPUT_DIR", "/tmp/input"),
                local_output_directory=os.getenv("LOCAL_OUTPUT_DIR", "/tmp/output"),
            ),
            parsing=ParsingConfig(
                default_mode=os.getenv("PARSING_MODE", "auto_parser"),
                default_parser=os.getenv("DEFAULT_PARSER", "pdf"),
                default_tool=os.getenv("DEFAULT_TOOL"),
            ),
            chunking=ChunkingConfig(
                default_strategy=os.getenv("CHUNKING_STRATEGY", "recursive_chunking"),
                chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
                chunk_overlap=int(os.getenv("CHUNK_OVERLAP", "200")),
            ),
            embedding=EmbeddingConfig(
                default_provider=os.getenv("EMBEDDING_PROVIDER", "openai"),
                default_model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
                batch_size=int(os.getenv("EMBEDDING_BATCH_SIZE", "100")),
            ),
            vector_db=VectorDBConfig(
                default_db=os.getenv("VECTOR_DB", "qdrant"),
                qdrant_host=os.getenv("QDRANT_HOST", "localhost"),
                qdrant_port=int(os.getenv("QDRANT_PORT", "6333")),
                qdrant_collection_name=os.getenv("QDRANT_COLLECTION", "documents"),
            ),
        )

    def get_default_config(self) -> PipelineConfig:
        """Get the default pipeline configuration"""
        return self._default_config

    def create_custom_config(self, overrides: Dict[str, Any]) -> PipelineConfig:
        """
        Create a custom configuration by applying overrides to the default config.

        Args:
            overrides: Dictionary of configuration overrides

        Returns:
            PipelineConfig with applied overrides
        """
        # Start with default config
        config_dict = self._default_config.to_dict()

        # Apply overrides recursively
        self._apply_overrides(config_dict, overrides)

        # Reconstruct config objects
        return PipelineConfig(
            loading=LoadingConfig(**config_dict.get("loading", {})),
            parsing=ParsingConfig(**config_dict.get("parsing", {})),
            chunking=ChunkingConfig(**config_dict.get("chunking", {})),
            embedding=EmbeddingConfig(**config_dict.get("embedding", {})),
            vector_db=VectorDBConfig(**config_dict.get("vector_db", {})),
        )

    def _apply_overrides(
        self, base_dict: Dict[str, Any], overrides: Dict[str, Any]
    ) -> None:
        """Recursively apply configuration overrides"""
        for key, value in overrides.items():
            if (
                key in base_dict
                and isinstance(base_dict[key], dict)
                and isinstance(value, dict)
            ):
                self._apply_overrides(base_dict[key], value)
            else:
                base_dict[key] = value

    def create_config_from_steps(self, steps: List[Dict[str, Any]]) -> PipelineConfig:
        """
        Create configuration from pipeline steps configuration.

        Args:
            steps: List of step configurations from API request

        Returns:
            PipelineConfig built from step configurations
        """
        config = self._default_config.to_dict()

        for step in steps:
            step_type = step.get("step_type")
            step_config = step.get("config", {})

            if step_type == "load":
                self._apply_load_config(config, step_config)
            elif step_type == "parse":
                self._apply_parse_config(config, step_config)
            elif step_type == "chunk":
                self._apply_chunk_config(config, step_config)
            elif step_type == "embed":
                self._apply_embed_config(config, step_config)
            elif step_type == "store":
                self._apply_store_config(config, step_config)

        return PipelineConfig(
            loading=LoadingConfig(**config["loading"]),
            parsing=ParsingConfig(**config["parsing"]),
            chunking=ChunkingConfig(**config["chunking"]),
            embedding=EmbeddingConfig(**config["embedding"]),
            vector_db=VectorDBConfig(**config["vector_db"]),
        )

    def _apply_load_config(
        self, config: Dict[str, Any], step_config: Dict[str, Any]
    ) -> None:
        """Apply loading step configuration"""
        loading_config = config["loading"]

        if "provider" in step_config:
            loading_config["default_source"] = step_config["provider"]
        if "file_path" in step_config:
            loading_config["local_input_directory"] = str(
                Path(step_config["file_path"]).parent
            )
        if "s3_bucket" in step_config:
            loading_config["s3_bucket_name"] = step_config["s3_bucket"]
        if "s3_region" in step_config:
            loading_config["s3_region"] = step_config["s3_region"]

    def _apply_parse_config(
        self, config: Dict[str, Any], step_config: Dict[str, Any]
    ) -> None:
        """Apply parsing step configuration"""
        parsing_config = config["parsing"]

        if "provider" in step_config:
            parsing_config["default_tool"] = step_config["provider"]
        if "strategy" in step_config:
            parsing_config["default_mode"] = step_config["strategy"]

    def _apply_chunk_config(
        self, config: Dict[str, Any], step_config: Dict[str, Any]
    ) -> None:
        """Apply chunking step configuration"""
        chunking_config = config["chunking"]

        if "strategy" in step_config:
            chunking_config["default_strategy"] = step_config["strategy"]
        if "chunk_size" in step_config:
            chunking_config["chunk_size"] = step_config["chunk_size"]
        if "chunk_overlap" in step_config:
            chunking_config["chunk_overlap"] = step_config["chunk_overlap"]

    def _apply_embed_config(
        self, config: Dict[str, Any], step_config: Dict[str, Any]
    ) -> None:
        """Apply embedding step configuration"""
        embedding_config = config["embedding"]

        if "provider" in step_config:
            embedding_config["default_provider"] = step_config["provider"]
        if "model" in step_config:
            embedding_config["default_model"] = step_config["model"]
        if "batch_size" in step_config:
            embedding_config["batch_size"] = step_config["batch_size"]

    def _apply_store_config(
        self, config: Dict[str, Any], step_config: Dict[str, Any]
    ) -> None:
        """Apply vector storage step configuration"""
        vector_db_config = config["vector_db"]

        if "provider" in step_config:
            vector_db_config["default_db"] = step_config["provider"]
        if "collection_name" in step_config:
            vector_db_config["qdrant_collection_name"] = step_config["collection_name"]
        if "index_name" in step_config:
            vector_db_config["pinecone_index_name"] = step_config["index_name"]

    def save_config_to_file(self, config: PipelineConfig, file_path: str) -> None:
        """
        Save configuration to a file in elevaite_ingestion format.

        Args:
            config: Pipeline configuration to save
            file_path: Path where to save the configuration file
        """
        config_data = config.to_elevaite_ingestion_format()

        # Ensure directory exists
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "w") as f:
            json.dump(config_data, f, indent=2)

        self.logger.info(f"Configuration saved to {file_path}")

    def validate_config(self, config: PipelineConfig) -> List[str]:
        """
        Validate pipeline configuration and return list of errors.

        Args:
            config: Configuration to validate

        Returns:
            List of validation error messages
        """
        errors = []

        # Validate embedding configuration
        if (
            config.embedding.default_provider == "openai"
            and not config.embedding.openai_api_key
        ):
            errors.append(
                "OpenAI API key is required when using OpenAI embedding provider"
            )

        # Validate vector DB configuration
        if (
            config.vector_db.default_db == "pinecone"
            and not config.vector_db.pinecone_api_key
        ):
            errors.append(
                "Pinecone API key is required when using Pinecone vector database"
            )

        # Validate chunking configuration
        if config.chunking.chunk_size <= 0:
            errors.append("Chunk size must be greater than 0")

        if config.chunking.chunk_overlap >= config.chunking.chunk_size:
            errors.append("Chunk overlap must be less than chunk size")

        return errors


# Global instance
config_manager = DynamicConfigManager()
