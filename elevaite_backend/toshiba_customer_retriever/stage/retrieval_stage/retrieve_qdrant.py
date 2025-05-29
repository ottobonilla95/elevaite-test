import os
import sys
import re
import time
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(path)

import os
from typing import List
from dotenv import load_dotenv
import openai
import nltk

STOPWORDS = set(nltk.corpus.stopwords.words('english'))

load_dotenv(".env")
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Please set it in the environment variables.")

openai_client = openai.OpenAI(api_key=api_key)

def get_embedding(text: str) -> List[float]:
    try:
        response = openai_client.embeddings.create(
            model="text-embedding-ada-002",
            input=[text]
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return [0] * 1536


# logger = get_logger(__name__)

# qdrant_config = VECTOR_DB_CONFIG.get("qdrant", {})
# qdrant_url = qdrant_config.get("host")
# qdrant_port = qdrant_config.get("port")
# collection_name = qdrant_config.get("collection_name")

# qdrant_url = "http://3.101.65.253"
# qdrant_port = 5333
# collection_name = "toshiba_demo_4"

qdrant_url = "http://3.101.65.253"
qdrant_port = 5333
collection_name = "toshiba_walgreen"

client = QdrantClient(url=qdrant_url, port=qdrant_port, timeout=300.0, check_compatibility=False)

def extract_part_numbers(text: str) -> List[str]:
    patterns = [
        # r'\b\d[A-Z][A-Z]?\d{8}\b',
        # r'\b\d[A-Z]{2}\d{7}\b',
        r'(?=.*?[0-9])(?=.*?[A-Za-z-]).+'
    ]
    all_matches = []
    words = text.split()
    for pattern in patterns:
        for word in words:
            if re.match(pattern, word):
                word = word.upper()
                all_matches.append(word)
    if all_matches:
        # logger.info(f"Found part numbers: {all_matches}")
        pass
    return all_matches

def extract_keywords(text: str, min_length: int = 4) -> List[str]:
    # stopwords = {'the', 'and', 'for', 'with', 'that', 'this', 'what', 'where', 'when', 'which',
    #              'who', 'whom', 'whose', 'why', 'how', 'are', 'was', 'were', 'have', 'has',
    #              'had', 'not', 'does', 'did', 'but', 'can', 'could', 'should', 'would', 'will'}
    stopwords = STOPWORDS
    return [w for w in text.split() if len(w) >= min_length and w.lower() not in stopwords]

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
        # logger.error(f"Semantic search failed: {str(e)}")
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
    try:
        response = client.scroll(
            collection_name=collection_name,
            scroll_filter=filters,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        return [process_match(m) | {"search_type": "payload_filter"} for m in response[0]]
    except Exception as e:
        # logger.error(f"Payload (exact match) retrieval failed: {str(e)}")
        return []

def retrieve_by_keywords(keywords: List[str], top_k: int = 20) -> List[Dict]:
    if not keywords:
        return []
    keyword_conditions = [
        models.FieldCondition(
            key="chunk_text",
            match=models.MatchText(text=kw)
        ) for kw in keywords
    ]
    filters = models.Filter(should=keyword_conditions)
    try:
        response = client.scroll(
            collection_name=collection_name,
            scroll_filter=filters,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        matches = response[0]
        return [process_match(m) | {"search_type": "sparse_keyword"} for m in matches]
    except Exception as e:
        # logger.error(f"Sparse keyword retrieval failed: {str(e)}")
        return []

# multi-search mechinaims 
def multi_strategy_search(query: str, top_k: int = 30) -> List[Dict]:
    seen_ids = set()
    results = []

    # Semantic retrieval
    semantic_results = retrieve_chunks_semantic(query, top_k=top_k)
    results.extend([r for r in semantic_results if r["chunk_id"] not in seen_ids and not seen_ids.add(r["chunk_id"])])

    #  Exact match retrieval (part numbers)
    part_numbers = extract_part_numbers(query)
    for pn in part_numbers:
        payload_matches = retrieve_by_payload(pn)
        results.extend([r for r in payload_matches if r["chunk_id"] not in seen_ids and not seen_ids.add(r["chunk_id"])])

    #  Sparse keyword retrieval
    keywords = extract_keywords(query)
    sparse_matches = retrieve_by_keywords(keywords, top_k=10)
    results.extend([r for r in sparse_matches if r["chunk_id"] not in seen_ids and not seen_ids.add(r["chunk_id"])])

    return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

def enhanced_hybrid_search(query: str, top_k: int = 30, is_table: Optional[bool] = None) -> List[Dict]:
    # logger.info("Using enhanced_hybrid_search")
    return multi_strategy_search(query, top_k=top_k)

