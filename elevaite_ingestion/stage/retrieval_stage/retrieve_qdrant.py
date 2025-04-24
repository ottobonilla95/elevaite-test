import os
import sys
import re
import time
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(path)

from embedding_factory.openai_embedder import get_embedding
from config.vector_db_config import VECTOR_DB_CONFIG
from utils.logger import get_logger

logger = get_logger(__name__)

qdrant_config = VECTOR_DB_CONFIG.get("qdrant", {})
qdrant_url = qdrant_config.get("host")
qdrant_port = qdrant_config.get("port")
collection_name = qdrant_config.get("collection_name")

client = QdrantClient(url=qdrant_url, port=qdrant_port, timeout=300.0, check_compatibility=False)

def extract_part_numbers(text: str) -> List[str]:
    patterns = [
        r'\b\d[A-Z][A-Z]?\d{8}\b',
        r'\b\d[A-Z]{2}\d{7}\b',
    ]
    all_matches = []
    for pattern in patterns:
        all_matches.extend(re.findall(pattern, text))
    if all_matches:
        logger.info(f"Found part numbers: {all_matches}")
    return all_matches

def process_match(match) -> Dict:
    payload = match.payload
    chunk_id = match.id
    is_table_chunk = payload.get("is_table", False)
    if is_table_chunk:
        chunk_text = f"{payload.get('table_contextual_header', '')} {payload.get('table_factual_sentences', '')}".strip()
        filename = payload.get("table_filename")
        page_info = payload.get("table_page_no")
        context_header = payload.get("table_contextual_header")
        image_path = payload.get("matched_table_image")
    else:
        chunk_text = payload.get("chunk_text", "")
        filename = payload.get("filename")
        page_info = payload.get("page_range")
        context_header = payload.get("contextual_header")
        image_path = None
    return {
        "chunk_id": chunk_id,
        "score": getattr(match, "score", 0.0),
        "chunk_text": chunk_text,
        "is_table": is_table_chunk,
        "filename": filename,
        "page_info": page_info,
        "contextual_header": context_header,
        "matched_image_path": image_path
    }

def retrieve_chunks_semantic(query: str, top_k: int = 30) -> List[Dict]:
    try:
        query_embedding = get_embedding(query)
        response = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True
        )
        return [process_match(m) | {"search_type": "semantic"} for m in response]
    except Exception as e:
        logger.error(f"Semantic search failed: {str(e)}")
        return []

def retrieve_by_payload(part_number: str, top_k: int = 20) -> List[Dict]:
    filters = models.Filter(should=[
        models.Filter(must=[
            models.FieldCondition(key="is_table", match=models.MatchValue(value=True)),
            models.FieldCondition(key="table_factual_sentences", match=models.MatchText(text=part_number))
        ]),
        models.Filter(must=[
            models.FieldCondition(key="is_table", match=models.MatchValue(value=False)),
            models.FieldCondition(key="chunk_text", match=models.MatchText(text=part_number))
        ])
    ])
    response = client.scroll(
        collection_name=collection_name,
        scroll_filter=filters,
        limit=top_k,
        with_payload=True,
        with_vectors=False
    )
    return [process_match(m) | {"search_type": "payload_filter", "score": 1.0} for m in response[0]]

def extract_keywords(query: str, min_length: int = 4) -> List[str]:
    stopwords = {'the', 'and', 'for', 'with', 'that', 'this', 'what', 'where', 'when', 'which',
                 'who', 'whom', 'whose', 'why', 'how', 'are', 'was', 'were', 'have', 'has',
                 'had', 'not', 'does', 'did', 'but', 'can', 'could', 'should', 'would', 'will'}
    return [w for w in query.split() if len(w) >= min_length and w.lower() not in stopwords]

def keyword_boost(results: List[Dict], keywords: List[str]) -> List[Dict]:
    updated = []
    for kw in keywords:
        for r in results:
            if kw.lower() in r["chunk_text"].lower() and r["search_type"] == "semantic":
                r["score"] = max(r["score"], 0.9)
                r["search_type"] = "keyword_filtered"
                r["matching_term"] = kw
                updated.append(r)
    return updated

def multi_strategy_search(query: str, top_k: int = 30) -> List[Dict]:
    seen_ids = set()
    results = []

    semantic_results = retrieve_chunks_semantic(query, top_k=top_k)
    results.extend([r for r in semantic_results if r["chunk_id"] not in seen_ids and not seen_ids.add(r["chunk_id"])])

    part_numbers = extract_part_numbers(query)
    for pn in part_numbers:
        payload_matches = retrieve_by_payload(pn)
        results.extend([r for r in payload_matches if r["chunk_id"] not in seen_ids and not seen_ids.add(r["chunk_id"])])

    keywords = extract_keywords(query)
    boosted = keyword_boost(semantic_results, keywords[:3])
    results.extend([r for r in boosted if r["chunk_id"] not in seen_ids and not seen_ids.add(r["chunk_id"])])

    return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

def enhanced_hybrid_search(query: str, top_k: int = 30, is_table: Optional[bool] = None) -> List[Dict]:
    logger.info("Using enhanced_hybrid_search")
    return multi_strategy_search(query, top_k=top_k)



if __name__ == "__main__":
    # test_queries = [
    #     "what does this part number 3AC00630600 refers to?",
    #     "find information about 3AC00597000",
    #     "When using the Hub in the countertop stand, what are the following I/O power requirements",
    #     "What are the recommended maintenance procedures for the TCx 800 system?",
    #     "How to install part number 3AC00633900 on the countertop stand"
    # ]
    test_queries = ["description for part number 3AC01548000"]

    for query in test_queries:
        print(f"\n=== QUERY: {query} ===")
        start = time.time()
        results = enhanced_hybrid_search(query, top_k=10)
        for i, res in enumerate(results[:5]):
            print(f"\nResult {i+1}")
            print(f"Search Type: {res.get('search_type')}")
            print(f"Score: {res.get('score')}")
            print(f"Chunk: {res['chunk_text'][:300]}...")
            print(f"Filename: {res['filename']} | Page: {res['page_info']}")
        print(f"\nCompleted in {time.time() - start:.2f} seconds")

