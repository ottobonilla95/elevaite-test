import os
import logging
import boto3
from dotenv import load_dotenv
from concurrent.futures import ThreadPoolExecutor
from ...config.load_config import LOADING_CONFIG

load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger()


def upload_file_to_s3(local_file_path, bucket, key):
    """Upload a single file to S3."""
    s3 = boto3.client("s3")
    try:
        with open(local_file_path, "rb") as f:
            s3.upload_fileobj(f, bucket, key)
        return True, f"✅ Uploaded {key} successfully."
    except Exception as e:
        return False, f"❌ Error uploading file '{key}': {str(e)}"


def load_files_to_destination():
    """Handles loading files based on LOADING_CONFIG."""
    try:
        source_type = LOADING_CONFIG["default_source"]
        logger.info(f"🚀 Loading data source: {source_type}")

        if source_type == "s3":
            s3_config = LOADING_CONFIG["sources"].get("s3", {})
            bucket_name = s3_config.get("bucket_name")
            input_directory = (
                LOADING_CONFIG["sources"].get("local", {}).get("input_directory")
            )

            if not bucket_name:
                logger.error("❌ No S3 bucket name found in config.")
                return

            if not input_directory or not os.path.exists(input_directory):
                logger.error(f"❌ Invalid input directory: {input_directory}")
                return

            files = [
                os.path.join(input_directory, f)
                for f in os.listdir(input_directory)
                if os.path.isfile(os.path.join(input_directory, f))
            ]
            if not files:
                logger.info("ℹ️ No files found to upload.")
                return

            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_file = {
                    executor.submit(
                        upload_file_to_s3, file, bucket_name, os.path.basename(file)
                    ): file
                    for file in files
                }

                for future in future_to_file:
                    success, message = future.result()
                    if success:
                        logger.info(message)
                    else:
                        logger.error(message)

        elif source_type == "local":
            local_config = LOADING_CONFIG["sources"].get("local", {})
            input_directory = local_config.get("input_directory")
            output_directory = local_config.get("output_directory")

            if not input_directory or not os.path.exists(input_directory):
                logger.error(f"❌ Invalid input directory: {input_directory}")
                return

            if not output_directory:
                logger.error("❌ No output directory specified in config.")
                return

            os.makedirs(output_directory, exist_ok=True)
            files = os.listdir(input_directory)

            if not files:
                logger.info("ℹ️ No files found to move.")
                return

            for file_name in files:
                src = os.path.join(input_directory, file_name)
                dst = os.path.join(output_directory, file_name)
                os.rename(src, dst)
                logger.info(f"✅ Moved {file_name} to {output_directory}")

        else:
            logger.error(f"❌ Invalid source type: {source_type}")

    except Exception as e:
        logger.error(f"❌ Error in loading pipeline: {e}")


if __name__ == "__main__":
    load_files_to_destination()
