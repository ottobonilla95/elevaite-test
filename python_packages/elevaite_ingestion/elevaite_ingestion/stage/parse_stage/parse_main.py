import os
import json
import time
from typing import Optional

from elevaite_ingestion.config.pipeline_config import PipelineConfig

# Legacy imports for backward compatibility
from elevaite_ingestion.config.aws_config import AWS_CONFIG
from elevaite_ingestion.config.parser_config import PARSER_CONFIG
from elevaite_ingestion.stage.parse_stage.parse_pipeline import main_parse
from elevaite_ingestion.stage.parse_stage.s3_processing import process_s3_files
from elevaite_ingestion.utils.logger import get_logger

logger = get_logger(__name__)


def ensure_directory_exists(directory):
    """Create directory if it does not exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"Created directory: {directory}")


def execute_pipeline(mode: Optional[str] = None, config: Optional[PipelineConfig] = None) -> dict:
    """
    Executes the parsing pipeline & logs status.

    Args:
        mode: Processing mode ('s3' or 'local'). Defaults to config mode.
        config: PipelineConfig object. If provided, uses this instead of global config.

    Returns:
        Dictionary with pipeline execution status.
    """
    # Use provided config or fall back to legacy global config
    if config:
        mode = mode or config.parser.mode
        parsing_mode = config.parser.parsing_mode
        input_bucket = config.aws.input_bucket
        intermediate_bucket = config.aws.intermediate_bucket
        input_dir = config.parser.input_directory
        output_dir = config.parser.output_directory
    else:
        mode = mode or PARSER_CONFIG.get("mode", "s3")
        parsing_mode = PARSER_CONFIG.get("parsing_mode", "auto_parser")
        input_bucket = AWS_CONFIG.get("input_bucket", "")
        intermediate_bucket = AWS_CONFIG.get("intermediate_bucket", "")
        input_dir = PARSER_CONFIG.get("local", {}).get("input_directory")
        output_dir = PARSER_CONFIG.get("local", {}).get("output_parsed_directory")

    if mode not in ["s3", "local"]:
        mode = input("Select mode (s3/local): ").strip().lower()
        PARSER_CONFIG["mode"] = mode

    pipeline_status = {
        "STAGE_2: PARSING": {
            "MODE": mode,
            "PARSING_MODE": parsing_mode,
            "INPUT_BUCKET": None,
            "OUTPUT_BUCKET": None,
            "TOTAL_FILES": 0,
            "EVENT_DETAILS": [],
            "STATUS": "Failed",
        }
    }

    if mode == "local":
        if not input_dir or not output_dir:
            logger.error("Local mode requires input_directory and output_directory")
            return {"error": "Missing local directories configuration"}

        ensure_directory_exists(input_dir)
        ensure_directory_exists(output_dir)

        logger.info(f"📌 Running {parsing_mode} mode for local files...")

        markdown_files, structured_data = main_parse(config=config)

        event_details = []
        for file in markdown_files:
            output_path = os.path.join(output_dir, os.path.basename(file))
            with open(output_path, "w") as f:
                json.dump(structured_data[file], f, indent=4)

            event_details.append(
                {"input": os.path.join(input_dir, os.path.basename(file)), "output": output_path, "status": "Success"}
            )

        pipeline_status["STAGE_2: PARSING"].update(
            {
                "INPUT": input_dir,
                "OUTPUT": output_dir,
                "TOTAL_FILES": len(markdown_files),
                "EVENT_DETAILS": event_details,
                "STATUS": "Completed" if markdown_files else "Failed",
            }
        )

    elif mode == "s3":
        logger.info(f"📌 Running {parsing_mode} mode for S3 files...")

        try:
            event_status = process_s3_files(input_bucket, intermediate_bucket)

            successful_files = [e for e in event_status if e["status"] == "Success"]
            failed_files = [e for e in event_status if e["status"] != "Success"]

            pipeline_status["STAGE_2: PARSING"].update(
                {
                    "INPUT_BUCKET": f"s3://{input_bucket}",
                    "OUTPUT_BUCKET": f"s3://{intermediate_bucket}",
                    "TOTAL_FILES": len(event_status),
                    "EVENT_DETAILS": event_status,
                    "STATUS": "Completed" if successful_files else "Failed",
                }
            )
        except Exception as e:
            logger.error(f"❌ S3 Processing Failed: {e}")
            pipeline_status["STAGE_2: PARSING"]["STATUS"] = "Failed"

    else:
        logger.error(f"❌ Invalid mode '{mode}' specified. Please choose 's3' or 'local'.")
        return {"error": "Invalid processing mode"}

    json_output = json.dumps(pipeline_status, indent=4)
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "stage_2_status.json")

    with open(file_path, "w") as json_file:
        json_file.write(json_output)

    logger.info(f"📌 PARSING STAGE: Pipeline Execution Summary:\n{json_output}")

    return pipeline_status


if __name__ == "__main__":
    start_time = time.time()
    execute_pipeline()
    end_time = time.time()
    print(f"total parsing time: {end_time - start_time:.2f} seconds")
