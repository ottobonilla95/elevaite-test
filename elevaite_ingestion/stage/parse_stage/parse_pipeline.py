import os
import sys
import json

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(path)

from config.parser_config import PARSER_CONFIG
from parsers.docx_parser import DocxParser
from parsers.xlsx_parser import XlsxParser
from parsers.pdf_parser import PdfParser
from structured_data.markdown_writer import MarkdownWriter
from utils.logger import get_logger

logger = get_logger(__name__)

def map_to_parser(file_type):
    """Map file types to appropriate parser classes."""
    parsers = {
        "docx": DocxParser,
        "xlsx": XlsxParser,
        "pdf": PdfParser,        
    }
    return parsers.get(file_type)


def process_file(file_path, output_dir, original_filename):
    """Processes a single file and preserves the original filename."""
    file_type = file_path.split(".")[-1].lower()

    parsing_mode = PARSER_CONFIG["parsing_mode"]

    if parsing_mode == "custom_parser":
        selected_parser = PARSER_CONFIG["custom_parser_selection"].get("parser")
        selected_tool = PARSER_CONFIG["custom_parser_selection"].get("tool")

        if selected_parser and file_type != selected_parser:
            logger.error(f"❌ You chose '{selected_parser}' parser, but uploaded '{file_type}'. Only '{selected_parser}' files are allowed.")
            return None, None  

        tool = selected_tool  

    else:  
        tool = PARSER_CONFIG["parsers"].get(file_type, {}).get("default_tool")

    parser_class = map_to_parser(file_type)
    if not parser_class:
        logger.error(f"❌ Unsupported file type: {file_type}")
        return None, None

    try:
        parser = parser_class() if file_type == "pdf" else parser_class(tool=tool)
        structured_data = parser.parse(file_path, original_filename)

        base_name = os.path.basename(file_path).split('.')[0]
        md_path = os.path.join(output_dir, f"{base_name}_{tool or 'default'}.md")

        return md_path, structured_data
    except Exception as e:
        logger.error(f"❌ Failed to process file {file_path}. Error: {e}")
        return None, None


def main_parse():
    """Main function to handle parsing based on mode (local/S3)."""
    mode = PARSER_CONFIG.get("mode", "s3")
    logger.info(f"🔹 Running main_parse() with mode: {mode}")

    if mode == "local":
        input_dir = PARSER_CONFIG["local"]["input_directory"]
        output_dir = PARSER_CONFIG["local"]["output_parsed_directory"]
        os.makedirs(output_dir, exist_ok=True)

        markdown_files = []
        structured_data = {}

        for file_name in os.listdir(input_dir):
            file_path = os.path.join(input_dir, file_name)
            md_path, file_data = process_file(file_path, output_dir)
            if md_path:
                markdown_files.append(md_path)
                structured_data[md_path] = file_data

        return markdown_files, structured_data
    
    else: 
        from s3_processing import process_s3_files
        s3_results = process_s3_files(PARSER_CONFIG["aws"]["input_bucket"], PARSER_CONFIG["aws"]["intermediate_bucket"])
        return s3_results, {}





















































#############################
##########################################
# import os
# import sys
# import json

# # Set up path to access parent directory
# path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# sys.path.append(path)

# from config.parser_config import load_config
# from configuration import CONFIG
# from structured_data.markdown_writer import MarkdownWriter
# from s3_processing import process_s3_files
# from file_processor import process_file  # ✅ Import from file_processor
# from utils.logger import get_logger

# logger = get_logger(__name__)
# config = load_config()

# def main_parse():
#     """Handles both Local & S3 processing modes."""
#     mode = config["parsing"]["default_mode"]
#     print(f"DEBUG: Running main_parse() with mode: {mode}")

#     data_source = CONFIG["data_source"]

#     if data_source == "local":
#         input_dir = CONFIG["local"]["input_directory"]
#         output_dir = CONFIG["local"]["output_parsed_directory"]
#         os.makedirs(output_dir, exist_ok=True)

#         markdown_files = []
#         structured_data = {}

#         for file_name in os.listdir(input_dir):
#             file_path = os.path.join(input_dir, file_name)
#             parser_type = None
#             tool = None

#             if mode == "manual":
#                 parser_type = config["parsing"]["default_parser"]
#                 tool = config["parsing"]["parsers"].get(parser_type, {}).get("default_tool")

#             md_path, file_data = process_file(file_path, output_dir, parser_type, tool)

#             if md_path:
#                 markdown_files.append(md_path)
#                 structured_data[md_path] = file_data

#         return markdown_files, structured_data

#     else:
#         input_bucket = CONFIG["aws"]["input_bucket"]
#         intermediate_bucket = CONFIG["aws"]["intermediate_bucket"]

#         s3_results = process_s3_files(input_bucket, intermediate_bucket)
#         return s3_results, {}
