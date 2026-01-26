"""
Pipeline configuration module.

This module provides dataclasses for passing configuration through the ingestion
pipeline stages without relying on file-based or global configuration.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AWSConfig:
    """AWS S3 bucket configuration."""

    input_bucket: str = ""
    intermediate_bucket: str = ""
    region: Optional[str] = None


@dataclass
class ParserConfig:
    """Parser stage configuration."""

    mode: str = "s3"  # "s3" or "local"
    parsing_mode: str = "auto_parser"  # "auto_parser" or "custom"
    default_parser: str = "pdf"
    default_tool: Optional[str] = None
    custom_parser_selection: dict = field(default_factory=dict)
    parsers: dict = field(default_factory=dict)
    # Local mode paths
    input_directory: Optional[str] = None
    output_directory: Optional[str] = None


@dataclass
class ChunkerConfig:
    """Chunker stage configuration."""

    chunk_strategy: str = "semantic_chunking"
    settings: dict = field(
        default_factory=lambda: {
            "breakpoint_threshold_type": "percentile",
            "breakpoint_threshold_amount": 80,
        }
    )


@dataclass
class EmbedderConfig:
    """Embedder stage configuration."""

    provider: str = "openai"
    model: str = "text-embedding-ada-002"
    api_key: Optional[str] = None  # If not provided, uses env var


@dataclass
class VectorDBConfig:
    """Vector database stage configuration."""

    vector_db: str = "pinecone"  # "pinecone", "chroma", "qdrant"
    index_name: Optional[str] = None
    collection_name: Optional[str] = None
    # Provider-specific settings
    settings: dict = field(default_factory=dict)


@dataclass
class PipelineConfig:
    """
    Unified configuration for the entire ingestion pipeline.

    This config object is passed through all pipeline stages, replacing
    the legacy file-based configuration approach.
    """

    aws: AWSConfig = field(default_factory=AWSConfig)
    parser: ParserConfig = field(default_factory=ParserConfig)
    chunker: ChunkerConfig = field(default_factory=ChunkerConfig)
    embedder: EmbedderConfig = field(default_factory=EmbedderConfig)
    vector_db: VectorDBConfig = field(default_factory=VectorDBConfig)

    @classmethod
    def from_dict(cls, data: dict) -> "PipelineConfig":
        """
        Create a PipelineConfig from a dictionary (e.g., from API request).

        Args:
            data: Dictionary with configuration values

        Returns:
            PipelineConfig instance
        """
        aws_data = data.get("aws", {})
        parser_data = data.get("parser", {})
        chunker_data = data.get("chunker", {})
        embedder_data = data.get("embedder", {})
        vector_db_data = data.get("vector_db", {})

        return cls(
            aws=AWSConfig(
                input_bucket=aws_data.get("input_bucket", ""),
                intermediate_bucket=aws_data.get("intermediate_bucket", ""),
                region=aws_data.get("region"),
            ),
            parser=ParserConfig(
                mode=data.get("mode", parser_data.get("mode", "s3")),
                parsing_mode=parser_data.get("parsing_mode", "auto_parser"),
                default_parser=parser_data.get("default_parser", "pdf"),
                default_tool=parser_data.get("default_tool"),
                custom_parser_selection=parser_data.get("custom_parser_selection", {}),
                parsers=parser_data.get("parsers", {}),
                input_directory=parser_data.get("input_directory"),
                output_directory=parser_data.get("output_directory"),
            ),
            chunker=ChunkerConfig(
                chunk_strategy=chunker_data.get("chunk_strategy", "semantic_chunking"),
                settings=chunker_data.get("settings", {}),
            ),
            embedder=EmbedderConfig(
                provider=embedder_data.get("provider", "openai"),
                model=embedder_data.get("model", "text-embedding-ada-002"),
                api_key=embedder_data.get("api_key"),
            ),
            vector_db=VectorDBConfig(
                vector_db=vector_db_data.get("vector_db", "pinecone"),
                index_name=vector_db_data.get("index_name"),
                collection_name=vector_db_data.get("collection_name"),
                settings=vector_db_data.get("settings", {}),
            ),
        )

    def to_dict(self) -> dict:
        """Convert config to dictionary."""
        return {
            "aws": {
                "input_bucket": self.aws.input_bucket,
                "intermediate_bucket": self.aws.intermediate_bucket,
                "region": self.aws.region,
            },
            "parser": {
                "mode": self.parser.mode,
                "parsing_mode": self.parser.parsing_mode,
                "default_parser": self.parser.default_parser,
                "default_tool": self.parser.default_tool,
                "custom_parser_selection": self.parser.custom_parser_selection,
                "parsers": self.parser.parsers,
                "input_directory": self.parser.input_directory,
                "output_directory": self.parser.output_directory,
            },
            "chunker": {
                "chunk_strategy": self.chunker.chunk_strategy,
                "settings": self.chunker.settings,
            },
            "embedder": {
                "provider": self.embedder.provider,
                "model": self.embedder.model,
            },
            "vector_db": {
                "vector_db": self.vector_db.vector_db,
                "index_name": self.vector_db.index_name,
                "collection_name": self.vector_db.collection_name,
                "settings": self.vector_db.settings,
            },
        }
