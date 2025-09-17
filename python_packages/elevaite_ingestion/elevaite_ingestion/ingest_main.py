import os
import sys
import json
import subprocess

from elevaite_ingestion.utils.logger import get_logger

logger = get_logger(__name__)


def run_stage(stage_name, script_path):
    """Runs a stage script and captures its status."""
    logger.info(f"🚀 Running {stage_name} using {script_path}...")
    try:
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True, check=True)

        logger.info(f"✅ {stage_name} completed successfully.")

        output_lines = result.stdout.strip().split("\n")
        json_output = None
        for line in output_lines:
            try:
                json_output = json.loads(line)
                break
            except json.JSONDecodeError:
                continue

        if json_output:
            return json_output
        else:
            logger.warning(
                f"⚠️ No valid JSON output captured from {script_path}.\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            )
            return {stage_name: {"STATUS": "Unknown - No JSON output"}}
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Error in {stage_name}: {e}\nSTDOUT: {e.stdout}\nSTDERR: {e.stderr}")
        return {stage_name: {"STATUS": "Failed", "ERROR": str(e)}}


# stages = [
#     ("STAGE_1: LOADING", "stage/load_stage/load_main.py"),
#     ("STAGE_2: PARSING", "stage/parse_stage/parse_main.py"),
#     ("STAGE_3: CHUNKING", "stage/chunk_stage/chunk_main.py"),
#     ("STAGE_4: EMBEDDING", "stage/embed_stage/embed_main.py"),
#     ("STAGE_5: VECTOR_DB", "stage/vectorstore_stage/vectordb_main.py")
# ]

stages = [
    ("STAGE_2: PARSING", "stage/parse_stage/parse_main.py"),
    ("STAGE_3: CHUNKING", "stage/chunk_stage/chunk_main.py"),
    ("STAGE_4: EMBEDDING", "stage/embed_stage/embed_main.py"),
    ("STAGE_5: VECTOR_DB", "stage/vectorstore_stage/vectordb_main.py"),
]


def main():
    """Executes all pipeline stages sequentially."""
    pipeline_status = {}

    for stage_name, script_path in stages:
        response = run_stage(stage_name, script_path)

        if isinstance(response, dict):
            pipeline_status.update(response)
        else:
            logger.error(f"Unexpected response format from {stage_name}: {response}")
            pipeline_status[stage_name] = {"STATUS": "Failed", "ERROR": "Invalid response format"}
            break

    status_file = "pipeline_status.json"
    with open(status_file, "w") as json_file:
        json.dump(pipeline_status, json_file, indent=4)

    logger.info(f"Full pipeline execution summary saved in {status_file}.")


if __name__ == "__main__":
    main()
