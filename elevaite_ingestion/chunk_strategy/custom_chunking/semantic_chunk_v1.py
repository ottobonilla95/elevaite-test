# import re
# import numpy as np
# from typing import List, Dict, Tuple, Optional, Literal, cast
# from langchain_core.embeddings import Embeddings
# from langchain_core.documents import Document
# from langchain_community.utils.math import cosine_similarity
# from contextual_header import generate_contextual_header
# from dotenv import load_dotenv
# load_dotenv()

# # ---------------------------
# # Step 1: Combine Paragraphs
# # ---------------------------
# def combine_paragraphs(paragraphs: List[Dict], buffer_size: int = 1) -> List[Dict]:
#     for i in range(len(paragraphs)):
#         combined = ""
#         for j in range(i - buffer_size, i + buffer_size + 1):
#             if 0 <= j < len(paragraphs):
#                 combined += paragraphs[j]["paragraph_text"] + " "
#         paragraphs[i]["combined_text"] = combined.strip()
#     return paragraphs

# # ---------------------------
# # Step 2: Compute Similarity
# # ---------------------------
# def calculate_cosine_distances(paragraphs: List[Dict]) -> Tuple[List[float], List[Dict]]:
#     distances = []
#     for i in range(len(paragraphs) - 1):
#         emb1 = paragraphs[i]["combined_embedding"]
#         emb2 = paragraphs[i + 1]["combined_embedding"]
#         sim = cosine_similarity([emb1], [emb2])[0][0]
#         distance = 1 - sim
#         distances.append(distance)
#         paragraphs[i]["distance_to_next"] = distance
#     return distances, paragraphs

# BreakpointThresholdType = Literal["percentile", "standard_deviation"]

# def chunk_text(parsed_data: Dict, chunking_params: Dict) -> List[Dict]:
#     paragraphs = parsed_data.get("paragraphs", [])
#     if not paragraphs:
#         return []

#     from langchain_openai import OpenAIEmbeddings
#     embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

#     buffer_size = chunking_params.get("buffer_size", 1)
#     threshold_type = chunking_params.get("breakpoint_threshold_type", "percentile")
#     threshold_value = chunking_params.get("breakpoint_threshold_amount", 80)
#     max_chunk_size = chunking_params.get("max_chunk_size", 1500)
#     min_chunk_size = chunking_params.get("min_chunk_size", 500)
#     filename = parsed_data.get("filename", "unknown.pdf")


#     paragraphs = combine_paragraphs(paragraphs, buffer_size)
#     combined_texts = [p["combined_text"] for p in paragraphs]
#     combined_embeddings = embeddings.embed_documents(combined_texts)

#     for idx, emb in enumerate(combined_embeddings):
#         paragraphs[idx]["combined_embedding"] = emb

#     distances, paragraphs = calculate_cosine_distances(paragraphs)

#     if threshold_type == "percentile":
#         threshold = np.percentile(distances, threshold_value)
#     elif threshold_type == "standard_deviation":
#         threshold = np.mean(distances) + threshold_value * np.std(distances)
#     else:
#         raise ValueError("Unsupported threshold type")

#     chunk_list = []
#     start = 0
#     indices_above_threshold = [i for i, d in enumerate(distances) if d > threshold]

#     for idx in indices_above_threshold:
#         group = paragraphs[start:idx + 1]
#         chunk_text = ""
#         current_group = []

#         for p in group:
#             if len(chunk_text) + len(p["paragraph_text"]) > max_chunk_size:
#                 if current_group:
#                     combined = " ".join([x["paragraph_text"] for x in current_group])
#                     chunk_list.append({
#                         "chunk_text": combined.strip(),
#                         "filename": filename,
#                         "page_range": list(set(x["page_no"] for x in current_group)),
#                         "start_paragraph": current_group[0]["paragraph_no"],
#                         "end_paragraph": current_group[-1]["paragraph_no"],
#                         # "page_range": list(set(x["page_no"] for x in current_group)),

#                     })
#                 chunk_text = p["paragraph_text"]
#                 current_group = [p]
#             else:
#                 chunk_text += " " + p["paragraph_text"]
#                 current_group.append(p)

#         if current_group:
#             combined = " ".join([x["paragraph_text"] for x in current_group])
#             chunk_list.append({
#                 "chunk_text": combined.strip(),
#                 "filename": filename,
#                 "page_range": list(set(x["page_no"] for x in current_group)),
#                 "start_paragraph": current_group[0]["paragraph_no"],
#                 "end_paragraph": current_group[-1]["paragraph_no"],
#                 # "page_range": list(set(x["page_no"] for x in current_group)),
#             })

#         start = idx + 1

#     # Final leftover group
#     if start < len(paragraphs):
#         group = paragraphs[start:]
#         chunk_text = ""
#         current_group = []

#         for p in group:
#             if len(chunk_text) + len(p["paragraph_text"]) > max_chunk_size:
#                 if current_group:
#                     combined = " ".join([x["paragraph_text"] for x in current_group])
#                     chunk_list.append({
#                         "chunk_text": combined.strip(),
#                         "filename": filename,
#                         "page_range": list(set(x["page_no"] for x in current_group)),
#                         "start_paragraph": current_group[0]["paragraph_no"],
#                         "end_paragraph": current_group[-1]["paragraph_no"],
#                         # "page_range": list(set(x["page_no"] for x in current_group)),
#                     })
#                 chunk_text = p["paragraph_text"]
#                 current_group = [p]
#             else:
#                 chunk_text += " " + p["paragraph_text"]
#                 current_group.append(p)

#         if current_group:
#             combined = " ".join([x["paragraph_text"] for x in current_group])
#             contextual_header = generate_contextual_header(combined,)
#             chunk_list.append({
#                 "chunk_text": combined.strip(),
#                 "contextual_header": contextual_header,
#                 "filename": filename,
#                 "page_range": list(set(x["page_no"] for x in current_group)),
#                 "start_paragraph": current_group[0]["paragraph_no"],
#                 "end_paragraph": current_group[-1]["paragraph_no"]


#             })

#     return 

######################### working by wednesday
# import os 
# import sys
# import re
# import uuid
# import numpy as np
# from typing import List, Dict, Tuple, Optional, Literal
# from langchain_core.embeddings import Embeddings
# from langchain_core.documents import Document
# from langchain_community.utils.math import cosine_similarity
# from .anthropic_contextual_header import generate_contextual_header
# from dotenv import load_dotenv
# load_dotenv()

# # ---------------------------
# # Step 1: Combine Paragraphs
# # ---------------------------
# def combine_paragraphs(paragraphs: List[Dict], buffer_size: int = 1) -> List[Dict]:
#     for i in range(len(paragraphs)):
#         combined = ""
#         for j in range(i - buffer_size, i + buffer_size + 1):
#             if 0 <= j < len(paragraphs):
#                 combined += paragraphs[j]["paragraph_text"] + " "
#         paragraphs[i]["combined_text"] = combined.strip()
#     return paragraphs

# # ---------------------------
# # Step 2: Compute Similarity
# # ---------------------------
# def calculate_cosine_distances(paragraphs: List[Dict]) -> Tuple[List[float], List[Dict]]:
#     distances = []
#     for i in range(len(paragraphs) - 1):
#         emb1 = paragraphs[i]["combined_embedding"]
#         emb2 = paragraphs[i + 1]["combined_embedding"]
#         sim = cosine_similarity([emb1], [emb2])[0][0]
#         distance = 1 - sim
#         distances.append(distance)
#         paragraphs[i]["distance_to_next"] = distance
#     return distances, paragraphs

# BreakpointThresholdType = Literal["percentile", "standard_deviation"]

# def chunk_text(parsed_data: Dict, chunking_params: Dict) -> List[Dict]:
#     paragraphs = parsed_data.get("paragraphs", [])
#     if not paragraphs:
#         return []

#     from langchain_openai import OpenAIEmbeddings
#     embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

#     buffer_size = chunking_params.get("buffer_size", 1)
#     threshold_type = chunking_params.get("breakpoint_threshold_type", "percentile")
#     threshold_value = chunking_params.get("breakpoint_threshold_amount", 80)
#     max_chunk_size = chunking_params.get("max_chunk_size", 1500)
#     min_chunk_size = chunking_params.get("min_chunk_size", 500)
#     filename = parsed_data.get("filename", "unknown.pdf")

#     paragraphs = combine_paragraphs(paragraphs, buffer_size)
#     combined_texts = [p["combined_text"] for p in paragraphs]
#     combined_embeddings = embeddings.embed_documents(combined_texts)

#     for idx, emb in enumerate(combined_embeddings):
#         paragraphs[idx]["combined_embedding"] = emb

#     distances, paragraphs = calculate_cosine_distances(paragraphs)

#     if threshold_type == "percentile":
#         threshold = np.percentile(distances, threshold_value)
#     elif threshold_type == "standard_deviation":
#         threshold = np.mean(distances) + threshold_value * np.std(distances)
#     else:
#         raise ValueError("Unsupported threshold type")

#     chunk_list = []
#     start = 0
#     indices_above_threshold = [i for i, d in enumerate(distances) if d > threshold]

#     for idx in indices_above_threshold:
#         group = paragraphs[start:idx + 1]
#         chunk_text = ""
#         current_group = []

#         for p in group:
#             if len(chunk_text) + len(p["paragraph_text"]) > max_chunk_size:
#                 if current_group:
#                     combined = " ".join([x["paragraph_text"] for x in current_group])
#                     chunk_obj = {
#                         "chunk_id": str(uuid.uuid4()),
#                         "chunk_text": combined.strip(),
#                         "filename": filename,
#                         "page_range": list(set(x["page_no"] for x in current_group)),
#                         "start_paragraph": current_group[0]["paragraph_no"],
#                         "end_paragraph": current_group[-1]["paragraph_no"]
#                     }
#                     chunk_obj["contextual_header"] = generate_contextual_header(chunk_obj, paragraphs)
#                     chunk_list.append(chunk_obj)
#                 chunk_text = p["paragraph_text"]
#                 current_group = [p]
#             else:
#                 chunk_text += " " + p["paragraph_text"]
#                 current_group.append(p)

#         if current_group:
#             combined = " ".join([x["paragraph_text"] for x in current_group])
#             chunk_obj = {
#                 "chunk_id": str(uuid.uuid4()),
#                 "chunk_text": combined.strip(),
#                 "filename": filename,
#                 "page_range": list(set(x["page_no"] for x in current_group)),
#                 "start_paragraph": current_group[0]["paragraph_no"],
#                 "end_paragraph": current_group[-1]["paragraph_no"]
#             }
#             chunk_obj["contextual_header"] = generate_contextual_header(chunk_obj, paragraphs)
#             chunk_list.append(chunk_obj)

#         start = idx + 1

#     # Final leftover group
#     if start < len(paragraphs):
#         group = paragraphs[start:]
#         chunk_text = ""
#         current_group = []

#         for p in group:
#             if len(chunk_text) + len(p["paragraph_text"]) > max_chunk_size:
#                 if current_group:
#                     combined = " ".join([x["paragraph_text"] for x in current_group])
#                     chunk_obj = {
#                         "chunk_id": str(uuid.uuid4()),
#                         "chunk_text": combined.strip(),
#                         "filename": filename,
#                         "page_range": list(set(x["page_no"] for x in current_group)),
#                         "start_paragraph": current_group[0]["paragraph_no"],
#                         "end_paragraph": current_group[-1]["paragraph_no"]
#                     }
#                     chunk_obj["contextual_header"] = generate_contextual_header(chunk_obj, paragraphs)
#                     chunk_list.append(chunk_obj)
#                 chunk_text = p["paragraph_text"]
#                 current_group = [p]
#             else:
#                 chunk_text += " " + p["paragraph_text"]
#                 current_group.append(p)

#         if current_group:
#             combined = " ".join([x["paragraph_text"] for x in current_group])
#             chunk_obj = {
#                 "chunk_id": str(uuid.uuid4()),
#                 "chunk_text": combined.strip(),
#                 "filename": filename,
#                 "page_range": list(set(x["page_no"] for x in current_group)),
#                 "start_paragraph": current_group[0]["paragraph_no"],
#                 "end_paragraph": current_group[-1]["paragraph_no"]
#             }
#             chunk_obj["contextual_header"] = generate_contextual_header(chunk_obj, paragraphs)
#             chunk_list.append(chunk_obj)

#     return chunk_list

import os 
import sys
import re
import uuid
import numpy as np
from typing import List, Dict, Tuple, Optional, Literal
from langchain_core.embeddings import Embeddings
from langchain_core.documents import Document
from langchain_community.utils.math import cosine_similarity
from .anthropic_contextual_header import generate_contextual_header
from .anthropic_contextual_header import generate_contextual_header_async
import asyncio
from asyncio import Semaphore
from dotenv import load_dotenv
load_dotenv()


# ---------------------------
# Async Header Assignment
# ---------------------------
# async def assign_headers_to_chunks(chunks: List[Dict], full_paragraphs: List[Dict]) -> List[Dict]:
#     print(f" Generating {len(chunks)} contextual headers asynchronously...")
#     tasks = [
#         generate_contextual_header_async(chunk, full_paragraphs)
#         for chunk in chunks
#     ]
#     results = await asyncio.gather(*tasks)
#     for i, header in enumerate(results):
#         chunks[i]["contextual_header"] = header
#     return chunks

MAX_CONCURRENT_LLM_CALLS = 60

import asyncio

import asyncio
import inspect

def asyncio_run_safe(awaitable):
    if not inspect.isawaitable(awaitable):
        raise TypeError("Passed object is not awaitable")

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        future = asyncio.run_coroutine_threadsafe(awaitable, loop)
        return future.result()  # blocks until result
    else:
        return asyncio.run(awaitable)




async def assign_headers_to_chunks(chunks, full_paragraphs):
    print(f"Generating {len(chunks)} contextual headers asynchronously...")

    sem = Semaphore(MAX_CONCURRENT_LLM_CALLS)

    async def safe_generate(chunk):
        async with sem:
            try:
                print(f"🔁 Starting header for chunk: {chunk['chunk_id'][:8]}...")
                result = await generate_contextual_header_async(chunk, full_paragraphs)
                print(f"✅ Finished header for chunk: {chunk['chunk_id'][:8]}")
                return result
            except Exception as e:
                print(f"❌ Error in chunk {chunk['chunk_id'][:8]}: {e}")
                return f"[Header Generation Failed]: {e}"

    tasks = [safe_generate(chunk) for chunk in chunks]
    results = await asyncio.gather(*tasks)

    for i, header in enumerate(results):
        chunks[i]["contextual_header"] = header

    return chunks


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

def assign_figures_to_chunks(chunk_list: List[Dict], figures: List[Dict]) -> List[Dict]:
    for chunk in chunk_list:
        matched_figures = [
            fig for fig in figures if fig["page_no"] in chunk["page_range"]
        ]
        if matched_figures:
            chunk["related_images"] = matched_figures
    return chunk_list

def chunk_text(parsed_data: Dict, chunking_params: Dict) -> List[Dict]:
    paragraphs = parsed_data.get("paragraphs", [])
    if not paragraphs:
        return []

    from langchain_openai import OpenAIEmbeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

    buffer_size = chunking_params.get("buffer_size", 1)
    threshold_type = chunking_params.get("breakpoint_threshold_type", "percentile")
    threshold_value = chunking_params.get("breakpoint_threshold_amount", 80)
    max_chunk_size = chunking_params.get("max_chunk_size", 1500)
    min_chunk_size = chunking_params.get("min_chunk_size", 500)
    filename = parsed_data.get("filename", "unknown.pdf")

    paragraphs = combine_paragraphs(paragraphs, buffer_size)
    combined_texts = [p["combined_text"] for p in paragraphs]
    combined_embeddings = embeddings.embed_documents(combined_texts)

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

    for idx in indices_above_threshold:
        group = paragraphs[start:idx + 1]
        chunk_text = ""
        current_group = []

        for p in group:
            if len(chunk_text) + len(p["paragraph_text"]) > max_chunk_size:
                if current_group:
                    combined = " ".join([x["paragraph_text"] for x in current_group])
                    chunk_obj = {
                        "chunk_id": str(uuid.uuid4()),
                        "chunk_text": combined.strip(),
                        "filename": filename,
                        "page_range": list(set(x["page_no"] for x in current_group)),
                        "start_paragraph": current_group[0]["paragraph_no"],
                        "end_paragraph": current_group[-1]["paragraph_no"]
                    }
                    # chunk_obj["contextual_header"] = generate_contextual_header(chunk_obj, paragraphs)
                    chunk_list.append(chunk_obj)
                chunk_text = p["paragraph_text"]
                current_group = [p]
            else:
                chunk_text += " " + p["paragraph_text"]
                current_group.append(p)

        if current_group:
            combined = " ".join([x["paragraph_text"] for x in current_group])
            chunk_obj = {
                "chunk_id": str(uuid.uuid4()),
                "chunk_text": combined.strip(),
                "filename": filename,
                "page_range": list(set(x["page_no"] for x in current_group)),
                "start_paragraph": current_group[0]["paragraph_no"],
                "end_paragraph": current_group[-1]["paragraph_no"]
            }
            # chunk_obj["contextual_header"] = generate_contextual_header(chunk_obj, paragraphs)
            chunk_list.append(chunk_obj)

        start = idx + 1

    if start < len(paragraphs):
        group = paragraphs[start:]
        chunk_text = ""
        current_group = []

        for p in group:
            if len(chunk_text) + len(p["paragraph_text"]) > max_chunk_size:
                if current_group:
                    combined = " ".join([x["paragraph_text"] for x in current_group])
                    chunk_obj = {
                        "chunk_id": str(uuid.uuid4()),
                        "chunk_text": combined.strip(),
                        "filename": filename,
                        "page_range": list(set(x["page_no"] for x in current_group)),
                        "start_paragraph": current_group[0]["paragraph_no"],
                        "end_paragraph": current_group[-1]["paragraph_no"]
                    }
                    # chunk_obj["contextual_header"] = generate_contextual_header(chunk_obj, paragraphs)
                    chunk_list.append(chunk_obj)
                chunk_text = p["paragraph_text"]
                current_group = [p]
            else:
                chunk_text += " " + p["paragraph_text"]
                current_group.append(p)

        if current_group:
            combined = " ".join([x["paragraph_text"] for x in current_group])
            chunk_obj = {
                "chunk_id": str(uuid.uuid4()),
                "chunk_text": combined.strip(),
                "filename": filename,
                "page_range": list(set(x["page_no"] for x in current_group)),
                "start_paragraph": current_group[0]["paragraph_no"],
                "end_paragraph": current_group[-1]["paragraph_no"]
            }
            # chunk_obj["contextual_header"] = generate_contextual_header(chunk_obj, paragraphs)
            chunk_list.append(chunk_obj)

    if "figures" in parsed_data:
        chunk_list = assign_figures_to_chunks(chunk_list, parsed_data["figures"])

    # chunk_list = asyncio.run(assign_headers_to_chunks(chunk_list, paragraphs))
    chunk_list = asyncio_run_safe(assign_headers_to_chunks(chunk_list, paragraphs))
    return chunk_list
