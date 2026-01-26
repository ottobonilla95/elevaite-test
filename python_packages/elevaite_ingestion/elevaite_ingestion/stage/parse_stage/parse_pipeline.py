import os
from typing import Optional

from elevaite_ingestion.config.pipeline_config import PipelineConfig

# Legacy import for backward compatibility
from elevaite_ingestion.config.parser_config import PARSER_CONFIG
from elevaite_ingestion.parsers.docx_parser import DocxParser
from elevaite_ingestion.parsers.xlsx_parser import XlsxParser
from elevaite_ingestion.parsers.pdf_parser import PdfParser
from elevaite_ingestion.utils.logger import get_logger

logger = get_logger(__name__)


def map_to_parser(file_type):
    """Map file types to appropriate parser classes."""
    parsers = {
        "docx": DocxParser,
        "xlsx": XlsxParser,
        "pdf": PdfParser,
    }
    return parsers.get(file_type)


def process_file(file_path, output_dir, original_filename, config: Optional[PipelineConfig] = None):
    """Processes a single file and preserves the original filename.

    Args:
        file_path: Path to the file to process
        output_dir: Directory to write output
        original_filename: Original name of the file
        config: Optional PipelineConfig object
    """
    file_type = file_path.split(".")[-1].lower()

    # Use provided config or fall back to global config
    if config:
        parsing_mode = config.parser.parsing_mode
        custom_parser_selection = config.parser.custom_parser_selection
        parsers_config = config.parser.parsers
    else:
        parsing_mode = PARSER_CONFIG["parsing_mode"]
        custom_parser_selection = PARSER_CONFIG.get("custom_parser_selection", {})
        parsers_config = PARSER_CONFIG.get("parsers", {})

    if parsing_mode == "custom_parser":
        selected_parser = custom_parser_selection.get("parser")
        selected_tool = custom_parser_selection.get("tool")

        if selected_parser and file_type != selected_parser:
            logger.error(
                f"❌ You chose '{selected_parser}' parser, but uploaded '{file_type}'. Only '{selected_parser}' files are allowed."
            )
            return None, None

        tool = selected_tool

    else:
        tool = parsers_config.get(file_type, {}).get("default_tool")

    parser_class = map_to_parser(file_type)
    if not parser_class:
        logger.error(f"❌ Unsupported file type: {file_type}")
        return None, None

    try:
        parser = parser_class() if file_type == "pdf" else parser_class(tool=tool)
        structured_data = parser.parse(file_path, original_filename)

        base_name = os.path.basename(file_path).split(".")[0]
        md_path = os.path.join(output_dir, f"{base_name}_{tool or 'default'}.md")

        return md_path, structured_data
    except Exception as e:
        logger.error(f"❌ Failed to process file {file_path}. Error: {e}")
        return None, None


def main_parse(config: Optional[PipelineConfig] = None):
    """Main function to handle parsing based on mode (local/S3).

    Args:
        config: Optional PipelineConfig object. Falls back to global config if not provided.
    """
    # Use provided config or fall back to global config
    if config:
        mode = config.parser.mode
        input_dir = config.parser.input_directory
        output_dir = config.parser.output_directory
        input_bucket = config.aws.input_bucket
        intermediate_bucket = config.aws.intermediate_bucket
    else:
        mode = PARSER_CONFIG.get("mode", "s3")
        input_dir = PARSER_CONFIG.get("local", {}).get("input_directory")
        output_dir = PARSER_CONFIG.get("local", {}).get("output_parsed_directory")
        input_bucket = PARSER_CONFIG.get("aws", {}).get("input_bucket")
        intermediate_bucket = PARSER_CONFIG.get("aws", {}).get("intermediate_bucket")

    logger.info(f"🔹 Running main_parse() with mode: {mode}")

    if mode == "local":
        if not input_dir or not output_dir:
            logger.error("Local mode requires input_directory and output_directory")
            return [], {}

        os.makedirs(output_dir, exist_ok=True)

        markdown_files = []
        structured_data = {}

        for file_name in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file_name)
            md_path, file_data = process_file(file_path, output_dir, file_name, config=config)
            if md_path:
                markdown_files.append(md_path)
                structured_data[md_path] = file_data

        return markdown_files, structured_data

    else:
        from elevaite_ingestion.stage.parse_stage.s3_processing import process_s3_files

        s3_results = process_s3_files(input_bucket, intermediate_bucket, config=config)
        return s3_results, {}
