import os
import sys
import cohere
import numpy as np
from dotenv import load_dotenv
from scipy.stats import beta
from typing import List, Dict, Tuple, Optional

load_dotenv()

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_path)

from retrieval_stage.retrieve_qdrant import retrieve_by_payload, extract_part_numbers, extract_keywords


cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))


def transform(x: float) -> float:
    """Apply beta CDF transformation to a raw score."""
    a, b = 0.4, 0.4
    return beta.cdf(x, a, b)

def rerank_text_chunks(query: str, chunk_texts: List[str], decay_rate: int = 30) -> Tuple[List[float], List[float]]:
    """Use Cohere reranker and apply beta CDF + exponential decay to similarity scores."""
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

def dynamic_keyword_boost(query: str, final_chunks: List[Dict], final_scores: List[float], boost_amount: float = 0.15) -> List[float]:
    query_keywords = extract_keywords(query)
    boosted_scores = []
    for chunk, score in zip(final_chunks, final_scores):
        text = chunk.get("chunk_text", "").lower()
        # if any(keyword.lower() in text for keyword in query_keywords):
        #     print("Boosting score for chunk: ", chunk["chunk_text"])
        #     print("Boost amount: ", boost_amount)
        #     print("Original score: ", score)
        #     print("Boosted score: ", score + boost_amount)
        #     boosted_scores.append(score + boost_amount)
        # else:
        #     boosted_scores.append(score)
        keyword_matches = sum(1 for keyword in query_keywords if keyword.lower() in text)
        if keyword_matches > 0:
            boost = boost_amount * (1 + np.exp(-keyword_matches))
            boosted_scores.append(score + boost)
        else:
            boosted_scores.append(score)
    return boosted_scores

async def rerank_separately_then_merge(query: str, top_k: int = 30, machine_types: Optional[List[str]] = None, collection_id: Optional[str] = None) -> Tuple[List[Dict], List[float]]:
    """
    1. Semantic retrieval + rerank
    2. Exact match retrieval + rerank
    3. sparse keyword retrieval + rerank
    4. merge and normalize scores
    """
    seen_ids = set()
    final_chunks: List[Dict] = []
    final_scores: List[float] = []
    
    #2 ---
    part_numbers = extract_part_numbers(query)
    if part_numbers:
        payload_chunks = []
        for pn in part_numbers:
            payload_chunks.extend(await retrieve_by_payload(pn, top_k=top_k, machine_types=machine_types, collection_id=collection_id))

        payload_chunks = [c for c in payload_chunks if c["chunk_id"] not in seen_ids]
        payload_texts = [c["chunk_text"] for c in payload_chunks]

        if payload_texts:
            for chunk in payload_chunks:
                seen_ids.add(chunk["chunk_id"])
                chunk["search_type"] = "exact_match"
                final_chunks.append(chunk)
                final_scores.append(0 + 1.05)

    final_scores = dynamic_keyword_boost(query, final_chunks, final_scores, boost_amount=0.15)

    return final_chunks, final_scores
