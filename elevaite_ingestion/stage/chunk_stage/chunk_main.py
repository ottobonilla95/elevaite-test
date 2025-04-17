# import os
# import sys
# # sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..","..")))
# path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
# sys.path.append(path)
# import json
# import boto3
# from configuration import CONFIG
# from utils.logger import get_logger
# from chunk_pipeline import execute_chunking_stage
# from dotenv import load_dotenv

# load_dotenv()
# logger = get_logger(__name__)

# s3_client = boto3.client("s3")

# def clean_s3_bucket_name(bucket_name):
#     """Remove 's3://' prefix from bucket name if present."""
#     return bucket_name.replace("s3://", "") if bucket_name.startswith("s3://") else bucket_name

# def list_s3_files(bucket_name, prefix=""):
#     """List all JSON files in the given S3 bucket."""
#     try:
#         bucket_name = clean_s3_bucket_name(bucket_name)
#         response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
#         if "Contents" not in response:
#             return []
#         return [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".json")]
#     except Exception as e:
#         logger.error(f"Error listing files from {bucket_name}: {e}")
#         return []


# def fetch_parsed_json_from_s3(bucket_name, file_key):
#     """Downloads and reads a parsed JSON file from S3."""
#     try:
#         bucket_name = clean_s3_bucket_name(bucket_name)
#         response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
#         json_content = response["Body"].read().decode("utf-8")
#         return json.loads(json_content)
#     except Exception as e:
#         logger.error(f"Failed to fetch {file_key} from S3: {e}")
#         return None

# # def merge_parsed_content(parsed_files, intermediate_bucket_clean):
# #     """Merges all parsed content from JSON files in S3 into a single text document."""
# #     merged_content = ""
# #     event_details = []

# #     for file_key in parsed_files:
# #         parsed_content = fetch_parsed_json_from_s3(intermediate_bucket_clean, file_key)
        
# #         if parsed_content and isinstance(parsed_content, dict) and "content" in parsed_content:
# #             merged_content += parsed_content["content"] + "\n\n"
# #             event_details.append({
# #                 "input": f"s3://{CONFIG['aws']['intermediate_bucket']}/{file_key}",
# #                 "status": "Merged"
# #             })
# #         else:
# #             event_details.append({
# #                 "input": f"s3://{CONFIG['aws']['intermediate_bucket']}/{file_key}",
# #                 "status": "Failed - Missing 'content' field"
# #             })

# #     if not merged_content.strip():
# #         logger.error("No valid parsed content to merge.")
# #         return None

# #     return {
# #         "content": merged_content.strip(),
# #         "total_files_merged": len(event_details),
# #         "event_details": event_details
# #     }

# def merge_parsed_content(parsed_files, intermediate_bucket_clean):
#     """Merges all parsed content from JSON files in S3 into a single text document."""
#     merged_sentences = []
#     event_details = []

#     for file_key in parsed_files:
#         parsed_content = fetch_parsed_json_from_s3(intermediate_bucket_clean, file_key)

#         if parsed_content and isinstance(parsed_content, dict) and "sentences" in parsed_content:
#             # Extend merged_sentences with the sentences from each file
#             merged_sentences.extend(parsed_content["sentences"])

#             event_details.append({
#                 "input": f"s3://{CONFIG['aws']['intermediate_bucket']}/{file_key}",
#                 "status": "Merged"
#             })
#         else:
#             event_details.append({
#                 "input": f"s3://{CONFIG['aws']['intermediate_bucket']}/{file_key}",
#                 "status": "Failed - Missing 'sentences' field"
#             })

#     if not merged_sentences:
#         logger.error("No valid parsed content to merge.")
#         return None

#     return {
#         "sentences": merged_sentences,
#         "file_path": "merged_content_source",
#         "total_files_merged": len(event_details),
#         "event_details": event_details
#     }


# def execute_chunking_pipeline():
#     """
#     Executes STAGE_3: CHUNKING by processing merged JSON files from S3.
#     """
#     mode = CONFIG["data_source"]
#     intermediate_bucket = CONFIG["aws"]["intermediate_bucket"]

#     if mode != "s3":
#         logger.error("This script is designed for S3 mode only.")
#         return {"error": "Invalid mode. This script supports S3 only."}

#     intermediate_bucket_clean = clean_s3_bucket_name(intermediate_bucket)

#     parsed_files = list_s3_files(intermediate_bucket_clean)
#     if not parsed_files:
#         logger.error("No parsed files found in S3. Aborting chunking stage.")
#         return {"error": "No parsed files found in S3"}


#     stage_2_status = {
#         "STAGE_2: PARSING": {
#             "MODE": mode,
#             "INPUT": f"s3://{CONFIG['aws']['input_bucket']}",                  
#             "OUTPUT": f"s3://{intermediate_bucket}",
#             "TOTAL_FILES": len(parsed_files),
#             "EVENT_DETAILS": [],
#             "STATUS": "Completed"
#         }
#     }

#     for file_key in parsed_files:
#         stage_2_status["STAGE_2: PARSING"]["EVENT_DETAILS"].append({
#             "input": f"s3://{intermediate_bucket}/{file_key}",
#             "output": f"s3://{intermediate_bucket}/{file_key}",
#             "status": "Success"
#         })

#     logger.info("Merging parsed content from S3 before chunking...")
#     merged_data = merge_parsed_content(parsed_files, intermediate_bucket_clean)

#     if not merged_data:
#         logger.error("Merging failed. Aborting chunking stage.")
#         return {"error": "Merging failed"}

#     chunking_input = {
#         "sentences": merged_data["sentences"],
#         "file_path": merged_data.get("file_path", "merged_content_source")

#     }

#     logger.info("Starting STAGE_3: CHUNKING...")
#     stage_3_status = execute_chunking_stage(chunking_input, stage_2_status)

#     pipeline_status = {**stage_2_status, **stage_3_status}

#     json_output = json.dumps(pipeline_status, indent=4)
#     script_dir = os.path.dirname(__file__)
#     file_path = os.path.join(script_dir, "stage_3_status.json")
#     with open(file_path, "w") as json_file:
#         json_file.write(json_output)
#     logger.info(f"CHUNKING STAGE: Pipeline Execution Summary:\n{json_output}")

#     return pipeline_status

# if __name__ == "__main__":
#     execute_chunking_pipeline()

################## running code.......
import os
import sys
path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(path)
import json
import boto3
from dotenv import load_dotenv
from config.load_config import LOADING_CONFIG
from config.aws_config import AWS_CONFIG
from utils.logger import get_logger
from chunk_pipeline import execute_chunking_stage
import time

load_dotenv()
logger = get_logger(__name__)

s3_client = boto3.client("s3")


def clean_s3_bucket_name(bucket_name):
    """Remove 's3://' prefix from bucket name if present."""
    return bucket_name.replace("s3://", "") if bucket_name.startswith("s3://") else bucket_name


def list_s3_files(bucket_name, prefix=""):
    """List all JSON files in the given S3 bucket."""
    try:
        bucket_name = clean_s3_bucket_name(bucket_name)
        response = s3_client.list_objects_v2(Bucket=bucket_name, Prefix=prefix)
        if "Contents" not in response:
            return []
        return [obj["Key"] for obj in response["Contents"] if obj["Key"].endswith(".json")]
    except Exception as e:
        logger.error(f"Error listing files from {bucket_name}: {e}")
        return []


def fetch_parsed_json_from_s3(bucket_name, file_key):
    """Downloads and reads a parsed JSON file from S3."""
    try:
        bucket_name = clean_s3_bucket_name(bucket_name)
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        json_content = response["Body"].read().decode("utf-8")
        return json.loads(json_content)
    except Exception as e:
        logger.error(f"Failed to fetch {file_key} from S3: {e}")
        return None


# def merge_parsed_content(parsed_files, intermediate_bucket_clean):
#     """Merges all parsed content from JSON files in S3 into a single text document."""
#     merged_data = {"sentences": [], "content": ""}
#     event_details = []

#     for file_key in parsed_files:
#         parsed_content = fetch_parsed_json_from_s3(intermediate_bucket_clean, file_key)

#         if parsed_content and isinstance(parsed_content, dict):
#             if "sentences" in parsed_content:
#                 merged_data["sentences"].extend(parsed_content["sentences"])
#                 event_details.append({"input": f"s3://{intermediate_bucket_clean}/{file_key}", "status": "Merged (PDF)"})
#             elif "content" in parsed_content:
#                 merged_data["content"] += parsed_content["content"] + "\n\n"
#                 event_details.append({"input": f"s3://{intermediate_bucket_clean}/{file_key}", "status": "Merged (Non-PDF)"})
#             else:
#                 event_details.append({"input": f"s3://{intermediate_bucket_clean}/{file_key}", "status": "Failed - Missing 'sentences' or 'content'"})

#     if not merged_data["sentences"] and not merged_data["content"].strip():
#         logger.error("No valid parsed content to merge.")
#         return None

#     merged_data["file_path"] = "merged_content_source"
#     merged_data["total_files_merged"] = len(event_details)
#     merged_data["event_details"] = event_details

#     return merged_data

# def merge_parsed_content(parsed_files, intermediate_bucket_clean):
#     """Merges all parsed content from JSON files in S3 into a single text document."""
#     merged_data = {"sentences": [], "content": "", "sentence_lookup": {}}
#     event_details = []

#     for file_key in parsed_files:
#         parsed_content = fetch_parsed_json_from_s3(intermediate_bucket_clean, file_key)

#         if parsed_content and isinstance(parsed_content, dict):
#             if "sentences" in parsed_content:
#                 for sentence in parsed_content["sentences"]:
#                     text = sentence["sentence_text"]
#                     page_no = sentence["page_no"]

#                     # **Store each sentence in lookup dictionary for later page mapping**
#                     merged_data["sentence_lookup"][text] = page_no  
#                     merged_data["sentences"].append(sentence)

#                 event_details.append({"input": f"s3://{intermediate_bucket_clean}/{file_key}", "status": "Merged (PDF)"})

#             elif "content" in parsed_content:
#                 merged_data["content"] += parsed_content["content"] + "\n\n"
#                 event_details.append({"input": f"s3://{intermediate_bucket_clean}/{file_key}", "status": "Merged (Non-PDF)"})

#             else:
#                 event_details.append({"input": f"s3://{intermediate_bucket_clean}/{file_key}", "status": "Failed - Missing 'sentences' or 'content'"})

#     if not merged_data["sentences"] and not merged_data["content"].strip():
#         logger.error("No valid parsed content to merge.")
#         return None

#     merged_data["file_path"] = "merged_content_source"
#     merged_data["total_files_merged"] = len(event_details)
#     merged_data["event_details"] = event_details

#     return merged_data

# def merge_parsed_content(parsed_files, intermediate_bucket_clean):
#     """Merges all parsed content from JSON files in S3 into a single text document."""
#     merged_data = {"paragraphs": [], "content": "", "paragraph_lookup": {}}
#     event_details = []

#     for file_key in parsed_files:
#         parsed_content = fetch_parsed_json_from_s3(intermediate_bucket_clean, file_key)

#         if parsed_content and isinstance(parsed_content, dict):
#             if "paragraphs" in parsed_content:
#                 for paragraph in parsed_content["paragraphs"]:
#                     text = paragraph["paragraph_text"]
#                     page_no = paragraph["page_no"]

#                     merged_data["paragraph_lookup"][text] = page_no  
#                     merged_data["paragraphs"].append(paragraph)

#                 event_details.append({"input": f"s3://{intermediate_bucket_clean}/{file_key}", "status": "Merged (PDF)"})

#             elif "content" in parsed_content:
#                 merged_data["content"] += parsed_content["content"] + "\n\n"
#                 event_details.append({"input": f"s3://{intermediate_bucket_clean}/{file_key}", "status": "Merged (Non-PDF)"})

#             else:
#                 event_details.append({"input": f"s3://{intermediate_bucket_clean}/{file_key}", "status": "Failed - Missing 'paragraphs' or 'content'"})

#     if not merged_data["paragraphs"] and not merged_data["content"].strip():
#         logger.error("No valid parsed content to merge.")
#         return None

#     merged_data["file_path"] = "merged_content_source"
#     merged_data["total_files_merged"] = len(event_details)
#     merged_data["event_details"] = event_details

#     return merged_data




def execute_chunking_pipeline():
    """
    Executes STAGE_3: CHUNKING by processing parsed JSON files from S3 individually.
    """
    source_type = LOADING_CONFIG["default_source"]
    input_bucket = AWS_CONFIG["intermediate_bucket"]
    intermediate_bucket = AWS_CONFIG["intermediate_bucket"]

    if source_type != "s3":
        logger.error("This script is designed for S3 mode only.")
        return {"error": "Invalid mode. This script supports S3 only."}

    intermediate_bucket_clean = clean_s3_bucket_name(intermediate_bucket)

    parsed_files = list_s3_files(intermediate_bucket_clean)  # ✅ Get list of JSON files
    if not parsed_files:
        logger.error("No parsed files found in S3. Aborting chunking stage.")
        return {"error": "No parsed files found in S3"}

    stage_2_status = {
        "STAGE_2: PARSING": {
            "MODE": source_type,
            "INPUT": f"s3://{input_bucket}",
            "OUTPUT": f"s3://{intermediate_bucket}",
            "TOTAL_FILES": len(parsed_files),
            "EVENT_DETAILS": [],
            "STATUS": "Completed"
        }
    }

    for file_key in parsed_files:
        stage_2_status["STAGE_2: PARSING"]["EVENT_DETAILS"].append({
            "input": f"s3://{intermediate_bucket}/{file_key}",
            "output": f"s3://{intermediate_bucket}/{file_key}",
            "status": "Success"
        })

    logger.info("Starting STAGE_3: CHUNKING...")
    stage_3_status = execute_chunking_stage(parsed_files, stage_2_status)

    pipeline_status = {**stage_3_status}

    json_output = json.dumps(pipeline_status, indent=4)
    script_dir = os.path.dirname(__file__)
    file_path = os.path.join(script_dir, "stage_3_status.json")
    with open(file_path, "w") as json_file:
        json_file.write(json_output)
    logger.info(f"CHUNKING STAGE: Pipeline Execution Summary:\n{json_output}")

    return pipeline_status

if __name__ == "__main__":
    start_time = time.time()
    execute_chunking_pipeline()
    end_time = time.time()
    print(f"total chunking time: {end_time -start_time:.2f} seconds")
