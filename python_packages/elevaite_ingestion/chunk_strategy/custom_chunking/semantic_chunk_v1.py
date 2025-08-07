import os 
import sys
import re
import uuid
import numpy as np
from typing import List, Dict, Tuple, Optional, Literal
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_community.utils.math import cosine_similarity
from .anthropic_contextual_header import generate_contextual_header_async
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from tiktoken import encoding_for_model
import asyncio
import logging

load_dotenv()
logger = logging.getLogger("chunk_pipeline")

# ---------------------------
# Step 1: Combine Paragraphs
# ---------------------------
def combine_paragraphs(paragraphs: List[Dict], buffer_size: int = 1) -> List[Dict]:
    for i in range(len(paragraphs)):
        combined = ""
        for j in range(i - buffer_size, i + buffer_size + 1):
            if 0 <= j < len(paragraphs):
                combined += paragraphs[j]["paragraph_text"] + " "
        paragraphs[i]["combined_text"] = combined.strip()
    return paragraphs

# ---------------------------
# Step 2: Compute Similarity
# ---------------------------
def calculate_cosine_distances(paragraphs: List[Dict]) -> Tuple[List[float], List[Dict]]:
    distances = []
    for i in range(len(paragraphs) - 1):
        emb1 = paragraphs[i]["combined_embedding"]
        emb2 = paragraphs[i + 1]["combined_embedding"]
        sim = cosine_similarity([emb1], [emb2])[0][0]
        distance = 1 - sim
        distances.append(distance)
        paragraphs[i]["distance_to_next"] = distance
    return distances, paragraphs

BreakpointThresholdType = Literal["percentile", "standard_deviation"]

async def chunk_text(parsed_data: Dict, chunking_params: Dict) -> List[Dict]:
    paragraphs = parsed_data.get("paragraphs", [])
    if not paragraphs:
        return []

    embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")
    enc = encoding_for_model("text-embedding-3-small")

    buffer_size = chunking_params.get("buffer_size", 1)
    threshold_type = chunking_params.get("breakpoint_threshold_type", "percentile")
    threshold_value = chunking_params.get("breakpoint_threshold_amount", 80)
    max_chunk_size = chunking_params.get("max_chunk_size", 1500)
    min_chunk_size = chunking_params.get("min_chunk_size", 500)
    filename = parsed_data.get("filename", "unknown.pdf")

    # --- NEW: Extract total_pages safely ---
    total_pages = 1
    if "metadata" in parsed_data and "total_pages" in parsed_data["metadata"]:
        total_pages = parsed_data["metadata"]["total_pages"]
    elif paragraphs:
        # Fallback: infer from max page_no in paragraphs
        total_pages = max(p.get("page_no", 1) for p in paragraphs)

    paragraphs = combine_paragraphs(paragraphs, buffer_size)
    combined_texts = [p["combined_text"] for p in paragraphs]

    # Batching for embeddings
    batch_size = 50
    combined_embeddings = []
    for i in range(0, len(combined_texts), batch_size):
        batch = combined_texts[i:i+batch_size]
        combined_embeddings.extend(embedding_model.embed_documents(batch))

    for idx, emb in enumerate(combined_embeddings):
        paragraphs[idx]["combined_embedding"] = emb

    distances, paragraphs = calculate_cosine_distances(paragraphs)
    

    if threshold_type == "percentile":
        threshold = np.percentile(distances, threshold_value)
    elif threshold_type == "standard_deviation":
        threshold = np.mean(distances) + threshold_value * np.std(distances)
    else:
        raise ValueError("Unsupported threshold type")

    chunk_list = []
    start = 0
    indices_above_threshold = [i for i, d in enumerate(distances) if d > threshold]

    def create_chunk_obj(group):
        # if not group:
        #     logger.warning("⚠️ Skipping empty group in chunking. Group contents: %s", group)
        #     return None
        combined = " ".join([x["paragraph_text"] for x in group])
        chunk_obj = {
            "chunk_id": str(uuid.uuid4()),
            "chunk_text": combined.strip(),
            "filename": filename,
            "page_range": list(set(x["page_no"] for x in group)),
            "start_paragraph": group[0]["paragraph_no"],
            "end_paragraph": group[-1]["paragraph_no"]
        }
        return chunk_obj

    for idx in indices_above_threshold:
        group = paragraphs[start:idx + 1]
        chunk_text_str = ""
        current_group = []

        for p in group:
            if len(chunk_text_str) + len(p["paragraph_text"]) > max_chunk_size:
                if current_group:
                    chunk_list.append(create_chunk_obj(current_group))
                chunk_text_str = p["paragraph_text"]
                current_group = [p]
            else:
                chunk_text_str += " " + p["paragraph_text"]
                current_group.append(p)

        if current_group:
            chunk_list.append(create_chunk_obj(current_group))

        start = idx + 1

    if start < len(paragraphs):
        group = paragraphs[start:]
        chunk_text_str = ""
        current_group = []

        for p in group:
            if len(chunk_text_str) + len(p["paragraph_text"]) > max_chunk_size:
                if current_group:
                    chunk_list.append(create_chunk_obj(current_group))
                chunk_text_str = p["paragraph_text"]
                current_group = [p]
            else:
                chunk_text_str += " " + p["paragraph_text"]
                current_group.append(p)

        if current_group:
            chunk_list.append(create_chunk_obj(current_group))

    # --- FIX: Pass total_pages to header generation ---
    headers = await asyncio.gather(
        *[
            generate_contextual_header_async(chunk, paragraphs, total_pages)
            for chunk in chunk_list
        ]
    )
    for i, header in enumerate(headers):
        chunk_list[i]["contextual_header"] = header

    return chunk_list
