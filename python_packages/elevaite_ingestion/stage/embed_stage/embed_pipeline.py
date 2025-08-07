import os
import sys
import json
from dotenv import load_dotenv
from config.aws_config import AWS_CONFIG
from config.embedder_config import EMBEDDER_CONFIG, get_embedder
from utils.logger import get_logger
from utils.s3_utils import list_s3_files, fetch_json_from_s3, save_json_to_s3
from embedding_factory.openai_embedder import get_embedding
from concurrent.futures import ThreadPoolExecutor, as_completed

load_dotenv()
logger = get_logger(__name__)


def process_single_chunk(chunk_key, input_s3_bucket, output_s3_prefix):
    try:
        chunk_data = fetch_json_from_s3(input_s3_bucket, chunk_key)
        if not chunk_data or "chunk_text" not in chunk_data:
            raise ValueError(f"Missing 'chunk_text' in {chunk_key}")

        chunk_id = chunk_data.get("chunk_id", "UNKNOWN")
        contextual_header = chunk_data.get("contextual_header", "NA")
        chunk_content = chunk_data["chunk_text"]
        filename = chunk_data.get("filename", "unknown_file")
        page_no = chunk_data.get("page_range", "NA")
        start_paragraph = chunk_data.get("start_paragraph", "UNKNOWN")
        end_paragraph = chunk_data.get("end_paragraph", "UNKNOWN")

        embedding_vector = get_embedding(chunk_content + contextual_header)

        embedding_output = {
            "chunk_id": chunk_id,
            "contextual_header": contextual_header,
            "chunk_text": chunk_content,
            "filename": filename,
            "page_range": page_no,
            "start_paragraph": start_paragraph,
            "end_paragraph": end_paragraph,
            "chunk_embedding": embedding_vector
        }

        embedding_key = f"{output_s3_prefix}{filename}_chunk_{chunk_id}.json"
        save_json_to_s3(embedding_output, input_s3_bucket, embedding_key)

        return {
            "filename": filename,
            "page_range": page_no,
            "chunk_id": chunk_id,
            "chunk_length": len(chunk_content),
            "input": f"s3://{input_s3_bucket}/{chunk_key}",
            "output": f"s3://{input_s3_bucket}/{embedding_key}",
            "status": "Success"
        }

    except Exception as e:
        logger.error(f"❌ Failed to generate embedding for {chunk_key}. Error: {e}")
        return {
            "input": f"s3://{input_s3_bucket}/{chunk_key}",
            "status": f"Failed - {e}"
        }


def execute_embedding_stage():
    embedder = get_embedder()
    input_s3_bucket = AWS_CONFIG["intermediate_bucket"]
    output_s3_prefix = "embeddings_output/"

    logger.info("🔹 Listing chunked files from S3...")
    chunk_files = list_s3_files(input_s3_bucket, "chunked_output/")

    if not chunk_files:
        logger.error("❌ No chunked files found in S3. Aborting STAGE_4.")
        return {"error": "STAGE_3 output not found"}

    pipeline_status = {
        "STAGE_4: GET_EMBEDDING": {
            "INPUT": f"s3://{input_s3_bucket}/chunked_output/",
            "OUTPUT": f"s3://{input_s3_bucket}/{output_s3_prefix}",
            "EMBEDDING_MODEL_PROVIDER": EMBEDDER_CONFIG["provider"],
            "EMBEDDING_MODEL_NAME": EMBEDDER_CONFIG["model"],
            "TOTAL_FILES": len(chunk_files),
            "EVENT_DETAILS": [],
            "STATUS": "Failed"
        }
    }

    results = []
    max_workers = int(os.getenv("MAX_EMBED_WORKERS", 10))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(process_single_chunk, chunk_file, input_s3_bucket, output_s3_prefix)
            for chunk_file in chunk_files
        ]
        for future in as_completed(futures):
            results.append(future.result())

    processed_chunks = [r for r in results if r["status"] == "Success"]
    # failed_chunks = [r for r in results if r["status"] != "Success"]

    pipeline_status["STAGE_4: GET_EMBEDDING"].update({
        "TOTAL_FILES": len(results),
        "EVENT_DETAILS": results,
        "STATUS": "Completed" if processed_chunks else "Failed"
    })

    final_output_key = f"{output_s3_prefix}stage_4_output.json"
    save_json_to_s3(pipeline_status, input_s3_bucket, final_output_key)

    json_output = json.dumps(pipeline_status, indent=4)
    logger.info(f"📌 Pipeline Execution Summary (GET_EMBEDDING):\n{json_output}")

    return pipeline_status

############# dense + sparse ##############
# import os
# import sys
# import json
# from dotenv import load_dotenv
# from config.aws_config import AWS_CONFIG
# from config.embedder_config import EMBEDDER_CONFIG, get_embedder
# from utils.logger import get_logger
# from utils.s3_utils import list_s3_files, fetch_json_from_s3, save_json_to_s3
# from embedding_factory.openai_embedder import get_embedding
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from sklearn.feature_extraction.text import TfidfVectorizer
# import joblib

# load_dotenv()
# logger = get_logger(__name__)

# # Collect all chunk texts first for TF-IDF fitting
# def collect_chunk_texts(chunk_files, input_s3_bucket):
#     all_texts = []
#     for key in chunk_files:
#         chunk_data = fetch_json_from_s3(input_s3_bucket, key)
#         if chunk_data and "chunk_text" in chunk_data:
#             combined = chunk_data["chunk_text"] + " " + chunk_data.get("contextual_header", "")
#             all_texts.append(combined.strip())
#     return all_texts

# def process_single_chunk(chunk_key, input_s3_bucket, output_s3_prefix, vectorizer):
#     try:
#         chunk_data = fetch_json_from_s3(input_s3_bucket, chunk_key)
#         if not chunk_data or "chunk_text" not in chunk_data:
#             raise ValueError(f"Missing 'chunk_text' in {chunk_key}")

#         chunk_id = chunk_data.get("chunk_id", "UNKNOWN")
#         contextual_header = chunk_data.get("contextual_header", "NA")
#         chunk_content = chunk_data["chunk_text"]
#         filename = chunk_data.get("filename", "unknown_file")
#         page_no = chunk_data.get("page_range", "NA")
#         start_paragraph = chunk_data.get("start_paragraph", "UNKNOWN")
#         end_paragraph = chunk_data.get("end_paragraph", "UNKNOWN")

#         combined_text = chunk_content + " " + contextual_header

#         # Dense embedding
#         embedding_vector = get_embedding(combined_text)

#         # Sparse vector
#         sparse_vector_array = vectorizer.transform([combined_text])
#         sparse_vector_dict = {
#             vectorizer.get_feature_names_out()[i]: float(val)
#             for i, val in zip(sparse_vector_array.indices, sparse_vector_array.data)
#         }

#         embedding_output = {
#             "chunk_id": chunk_id,
#             "contextual_header": contextual_header,
#             "chunk_text": chunk_content,
#             "filename": filename,
#             "page_range": page_no,
#             "start_paragraph": start_paragraph,
#             "end_paragraph": end_paragraph,
#             "chunk_embedding": embedding_vector,
#             "sparse_vector": sparse_vector_dict
#         }

#         embedding_key = f"{output_s3_prefix}{filename}_chunk_{chunk_id}.json"
#         save_json_to_s3(embedding_output, input_s3_bucket, embedding_key)

#         return {
#             "filename": filename,
#             "page_range": page_no,
#             "chunk_id": chunk_id,
#             "chunk_length": len(chunk_content),
#             "input": f"s3://{input_s3_bucket}/{chunk_key}",
#             "output": f"s3://{input_s3_bucket}/{embedding_key}",
#             "status": "Success"
#         }

#     except Exception as e:
#         logger.error(f"❌ Failed to generate embedding for {chunk_key}. Error: {e}")
#         return {
#             "input": f"s3://{input_s3_bucket}/{chunk_key}",
#             "status": f"Failed - {e}"
#         }

# def execute_embedding_stage():
#     embedder = get_embedder()
#     input_s3_bucket = AWS_CONFIG["intermediate_bucket"]
#     output_s3_prefix = "embeddings_output/"

#     logger.info("🔹 Listing chunked files from S3...")
#     chunk_files = list_s3_files(input_s3_bucket, "chunked_output/")

#     if not chunk_files:
#         logger.error("❌ No chunked files found in S3. Aborting STAGE_4.")
#         return {"error": "STAGE_3 output not found"}

#     logger.info("🔹 Collecting texts for TF-IDF vectorizer...")
#     all_texts = collect_chunk_texts(chunk_files, input_s3_bucket)

#     logger.info("🔹 Fitting TF-IDF vectorizer...")
#     vectorizer = TfidfVectorizer()
#     vectorizer.fit(all_texts)

#     # Save vectorizer locally
#     vectorizer_path = os.path.join(os.path.dirname(__file__), "tfidf_vectorizer.joblib")
#     joblib.dump(vectorizer, vectorizer_path)
#     logger.info(f"✅ TF-IDF vectorizer saved to {vectorizer_path}")

#     pipeline_status = {
#         "STAGE_4: GET_EMBEDDING": {
#             "INPUT": f"s3://{input_s3_bucket}/chunked_output/",
#             "OUTPUT": f"s3://{input_s3_bucket}/{output_s3_prefix}",
#             "EMBEDDING_MODEL_PROVIDER": EMBEDDER_CONFIG["provider"],
#             "EMBEDDING_MODEL_NAME": EMBEDDER_CONFIG["model"],
#             "TOTAL_FILES": len(chunk_files),
#             "EVENT_DETAILS": [],
#             "STATUS": "Failed"
#         }
#     }

#     results = []
#     max_workers = int(os.getenv("MAX_EMBED_WORKERS", 10))

#     with ThreadPoolExecutor(max_workers=max_workers) as executor:
#         futures = [
#             executor.submit(process_single_chunk, chunk_file, input_s3_bucket, output_s3_prefix, vectorizer)
#             for chunk_file in chunk_files
#         ]
#         for future in as_completed(futures):
#             results.append(future.result())

#     processed_chunks = [r for r in results if r["status"] == "Success"]

#     pipeline_status["STAGE_4: GET_EMBEDDING"].update({
#         "TOTAL_FILES": len(results),
#         "EVENT_DETAILS": results,
#         "STATUS": "Completed" if processed_chunks else "Failed"
#     })

#     final_output_key = f"{output_s3_prefix}stage_4_output.json"
#     save_json_to_s3(pipeline_status, input_s3_bucket, final_output_key)

#     json_output = json.dumps(pipeline_status, indent=4)
#     logger.info(f"📌 Pipeline Execution Summary (GET_EMBEDDING):\n{json_output}")

#     return pipeline_status


