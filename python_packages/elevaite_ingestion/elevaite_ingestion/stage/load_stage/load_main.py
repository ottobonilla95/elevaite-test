import os
import sys
import json
import logging
import time
from datetime import datetime
from elevaite_ingestion.config.load_config import LOADING_CONFIG
from elevaite_ingestion.stage.load_stage.load_pipeline import load_files_to_destination, upload_file_to_s3

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger()


def execute_pipeline():
    """Executes the loading pipeline and stores detailed status."""
    try:
        source_type = LOADING_CONFIG["default_source"]
        pipeline_status = {
            "STAGE_1: LOADING": {
                "DATA_SOURCE": source_type,
                "BUCKET_NAME": None,
                "EVENT_DETAILS": [],
                "TOTAL_LOADING_TIME(SEC)": 0,
                "AVERAGE_LOADING_TIME(SEC)": 0,
                "STATUS": "Failed",
            }
        }

        event_details = []
        total_start_time = time.time()

        if source_type == "s3":
            s3_config = LOADING_CONFIG["sources"].get("s3", {})
            bucket_name = s3_config.get("bucket_name")

            if not bucket_name:
                logger.error("❌ No S3 bucket name found in config.")
                return pipeline_status

            pipeline_status["STAGE_1: LOADING"]["BUCKET_NAME"] = bucket_name
            input_directory = LOADING_CONFIG["sources"].get("local", {}).get("input_directory")

            if not input_directory or not os.path.exists(input_directory):
                logger.error(f"❌ Invalid input directory: {input_directory}")
                return pipeline_status

            files = [
                os.path.join(input_directory, f)
                for f in os.listdir(input_directory)
                if os.path.isfile(os.path.join(input_directory, f))
            ]

            if not files:
                logger.info("ℹ️ No files found to upload.")
                return pipeline_status

            for file_path in files:
                file_name = os.path.basename(file_path)
                file_extension = os.path.splitext(file_name)[-1].lower().replace(".", "")
                file_size_kb = round(os.path.getsize(file_path) / 1024, 2)
                start_load_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # load_time = datetime.now().strftime("%H:%M:%S")

                start_time = time.time()
                success, message = upload_file_to_s3(file_path, bucket_name, file_name)
                end_time = time.time()
                loading_time_sec = round(end_time - start_time, 2)

                event_details.append(
                    {
                        "file_name": file_name,
                        "file_url": f"s3://{bucket_name}/{file_name}",
                        "file_extension": file_extension,
                        "file_size(KB)": file_size_kb,
                        "start_load_datetime": start_load_datetime,
                        "loading_time(SEC)": loading_time_sec,
                        "status": "Success" if success else "Failed",
                    }
                )

        elif source_type == "local":
            # Process local file movement
            local_config = LOADING_CONFIG["sources"].get("local", {})
            input_directory = local_config.get("input_directory")
            output_directory = local_config.get("output_directory")

            if not input_directory or not os.path.exists(input_directory):
                logger.error(f"❌ Invalid input directory: {input_directory}")
                return pipeline_status

            if not output_directory:
                logger.error(f"❌ No output directory specified in config.")
                return pipeline_status

            os.makedirs(output_directory, exist_ok=True)
            files = os.listdir(input_directory)

            if not files:
                logger.info("ℹ️ No files found to move.")
                return pipeline_status

            for file_name in files:
                src = os.path.join(input_directory, file_name)
                dst = os.path.join(output_directory, file_name)
                file_extension = os.path.splitext(file_name)[-1].lower().replace(".", "")
                file_size_kb = round(os.path.getsize(src) / 1024, 2)
                start_load_datetime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # load_time = datetime.now().strftime("%H:%M:%S")

                start_time = time.time()
                os.rename(src, dst)
                end_time = time.time()
                loading_time_sec = round(end_time - start_time, 2)

                event_details.append(
                    {
                        "file_name": file_name,
                        "file_path": dst,
                        "file_extension": file_extension,
                        "file_size(KB)": file_size_kb,
                        "start_load_datetime": start_load_datetime,
                        "loading_time(SEC)": loading_time_sec,
                        "status": "Success",
                    }
                )

        total_end_time = time.time()
        total_loading_time = round(total_end_time - total_start_time, 2)
        pipeline_status["STAGE_1: LOADING"]["EVENT_DETAILS"] = event_details
        pipeline_status["STAGE_1: LOADING"]["TOTAL_LOADING_TIME(SEC)"] = total_loading_time
        # average loadinfgitme
        num_events = len(event_details)
        if num_events > 0:
            pipeline_status["STAGE_1: LOADING"]["AVERAGE_LOADING_TIME(SEC)"] = round(total_loading_time / num_events, 2)
        else:
            pipeline_status["STAGE_1: LOADING"]["AVERAGE_LOADING_TIME(SEC)"] = 0

        pipeline_status["STAGE_1: LOADING"]["STATUS"] = "Completed" if event_details else "No Files Processed"
        logger.info("✅ Loading pipeline executed successfully.")

    except Exception as e:
        logger.error(f"❌ Error in loading pipeline: {e}")
        pipeline_status["STAGE_1: LOADING"]["STATUS"] = f"Failed - {e}"

    status_file_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "stage/load_stage/stage_1_status.json")
    )
    with open(status_file_path, "w") as json_file:
        json.dump(pipeline_status, json_file, indent=4)

    return pipeline_status


if __name__ == "__main__":
    result = execute_pipeline()
    print(json.dumps(result, indent=4))
