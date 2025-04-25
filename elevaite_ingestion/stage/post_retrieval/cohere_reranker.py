# import os
# import sys
# import cohere
# import numpy as np
# from dotenv import load_dotenv
# from scipy.stats import beta
# from typing import List, Dict, Tuple

# load_dotenv()

# base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# sys.path.append(base_path)

# from retrieval_stage.retrieve_qdrant import multi_strategy_search as enhanced_hybrid_search

# cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))


# def transform(x: float) -> float:
#     """
#     Transform scores using beta distribution CDF
    
#     Args:
#         x: Raw score value
        
#     Returns:
#         Transformed score
#     """
#     a, b = 0.4, 0.4
#     return beta.cdf(x, a, b)


# def rerank_chunks(query: str, chunks: List[str]) -> Tuple[List[float], List[float]]:
#     """
#     Rerank chunks using Cohere's reranking API
    
#     Args:
#         query: User query
#         chunks: List of text chunks to rerank
        
#     Returns:
#         Tuple of (similarity_scores, chunk_values)
#     """
#     model = "rerank-english-v3.0"
#     decay_rate = 30
    
#     reranked_results = cohere_client.rerank(model=model, query=query, documents=chunks)
#     results = reranked_results.results
#     reranked_indices = [result.index for result in results]
#     reranked_similarity_scores = [result.relevance_score for result in results]
    
#     similarity_scores = [0] * len(chunks)
#     chunk_values = [0] * len(chunks)
#     for i, index in enumerate(reranked_indices):
#         abs_val = transform(reranked_similarity_scores[i])
#         similarity_scores[index] = abs_val
#         chunk_values[index] = np.exp(-i / decay_rate) * abs_val
    
#     return similarity_scores, chunk_values


# def cohere_rerank(query: str, chunks: List[Dict], top_k: int = 20) -> List[Dict]:
#     """
#     Simplified reranking function that returns reordered chunks
    
#     Args:
#         query: User query
#         chunks: List of chunk dictionaries with metadata
#         top_k: Number of results to return
        
#     Returns:
#         Reranked list of chunks
#     """
#     inputs = [chunk["chunk_text"] for chunk in chunks]
#     response = cohere_client.rerank(
#         query=query, 
#         documents=inputs,
#         top_n=top_k,
#         model="rerank-english-v3.0"
#     )
#     return [chunks[result.index] for result in response.results]


import os
import sys
import cohere
import numpy as np
from dotenv import load_dotenv
from scipy.stats import beta
from typing import List, Dict, Tuple

# load_dotenv("../../.env")

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_path)

from retrieval_stage.retrieve_qdrant import retrieve_chunks_semantic, retrieve_by_payload, extract_part_numbers

cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))


def transform(x: float) -> float:
    """Transform scores using beta distribution CDF"""
    a, b = 0.4, 0.4
    return beta.cdf(x, a, b)


def rerank_text_chunks(query: str, chunk_texts: List[str], decay_rate: int = 30) -> Tuple[List[float], List[float]]:
    """Use Cohere reranker and apply beta CDF + exponential decay"""
    reranked_results = cohere_client.rerank(
        model="rerank-english-v3.0", query=query, documents=chunk_texts
    )
    results = reranked_results.results
    scores = [0.0] * len(chunk_texts)
    values = [0.0] * len(chunk_texts)

    for i, result in enumerate(results):
        idx = result.index
        transformed_score = transform(result.relevance_score)
        scores[idx] = transformed_score
        values[idx] = np.exp(-i / decay_rate) * transformed_score

    return scores, values


def rerank_separately_then_merge(query: str, top_k: int = 30) -> Tuple[List[Dict], List[float]]:
    """
    1. Rerank semantic chunks
    2. Rerank payload (exact match) chunks
    3. Merge both, return (chunks, values)
    """
    seen_ids = set()
    final_chunks: List[Dict] = []
    final_scores: List[float] = []

    # --- Semantic Retrieval ---
    semantic_chunks = retrieve_chunks_semantic(query, top_k=top_k)
    semantic_texts = [c["chunk_text"] for c in semantic_chunks]
    _, semantic_values = rerank_text_chunks(query, semantic_texts)

    for chunk, val in zip(semantic_chunks, semantic_values):
        if chunk["chunk_id"] not in seen_ids:
            seen_ids.add(chunk["chunk_id"])
            chunk["search_type"] = "semantic"
            final_chunks.append(chunk)
            final_scores.append(val)

    # --- Payload Retrieval ---
    part_numbers = extract_part_numbers(query)
    if part_numbers:
        payload_chunks = []
        for pn in part_numbers:
            payload_chunks.extend(retrieve_by_payload(pn, top_k=top_k))

        payload_chunks = [c for c in payload_chunks if c["chunk_id"] not in seen_ids]
        payload_texts = [c["chunk_text"] for c in payload_chunks]

        if payload_texts:
            _, payload_values = rerank_text_chunks(query, payload_texts)

            for chunk, val in zip(payload_chunks, payload_values):
                seen_ids.add(chunk["chunk_id"])
                chunk["search_type"] = "exact_match"
                final_chunks.append(chunk)
                final_scores.append(val + 0.05)

    return final_chunks, final_scores
