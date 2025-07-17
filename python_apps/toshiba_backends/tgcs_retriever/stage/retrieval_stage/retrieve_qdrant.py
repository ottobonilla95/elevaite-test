import os
import sys
import re
import time
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models
import nltk

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(path)

import os
from typing import List
from dotenv import load_dotenv
import openai

STOPWORDS = set(nltk.corpus.stopwords.words('english'))

# load_dotenv("stage/.env")
# TBD - REMOVE BELOW LINE AFTER TESTING THE FUNCTION
load_dotenv(".env")
# load_dotenv("../.env")
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



def extract_part_numbers(text: str) -> List[str]:
    patterns = [
        # r'\b\d[A-Z][A-Z]?\d{8}\b',
        # r'\b\d[A-Z]{2}\d{7}\b',
        # r'(?=.*?[0-9])(?=.*?[A-Za-z]).+',
        r'^(?=.*[0-9])(?=.*[a-zA-Z])[a-zA-Z0-9]{11}$',
        r'^(?=.*[0-9])(?=.*[a-zA-Z])[a-zA-Z0-9]{8}$',
        r'^[mM][sS]\d{3}$',
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
    print("Part numbers: ", all_matches)
    return all_matches

def extract_mtm_numbers(text: str) -> List[str]:
    pattern = r'\b\d{4}-[A-Za-z0-9]{3,4}\b'
    matches = [word.upper() for word in text.split() if re.match(pattern, word)]
    return matches

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

def retrieve_chunks_semantic(query: str, top_k: int = 30, machine_types: Optional[List[str]] = None, collection_id: Optional[str] = None) -> List[Dict]:
    qdrant_url = "http://3.101.65.253"
    qdrant_port = 5333
    collection_name = "toshiba_demo_4" if not collection_id else collection_id
    print("Collection id in semantic: ",collection_id)

    client = QdrantClient(url=qdrant_url, port=qdrant_port, timeout=300.0, check_compatibility=False)
    try:
        query_embedding = get_embedding(query)

        results = []
        seen_ids = set()

        # First, search with filter if machine_types is provided
        if machine_types:
            filters = models.Filter(
                should=[
                    models.FieldCondition(
                        key="filename",
                        match=models.MatchText(text=mt)
                    ) for mt in machine_types
                ] + [
                    models.FieldCondition(
                        key="table_filename",
                        match=models.MatchText(text=mt)
                    ) for mt in machine_types
                ]
            )
            filtered_response = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True,
                query_filter=filters
            )
            for m in filtered_response:
                match = process_match(m) | {"search_type": "semantic"}
                results.append(match)
                seen_ids.add(match["chunk_id"])

        # Then, search without filter to fill up to top_k
        unfiltered_response = client.search(
            collection_name=collection_name,
            query_vector=query_embedding,
            limit=top_k * 2,  # get more to avoid duplicates
            with_payload=True,
            query_filter=None
        )
        for m in unfiltered_response:
            match = process_match(m) | {"search_type": "semantic"}
            if match["chunk_id"] not in seen_ids:
                results.append(match)
                seen_ids.add(match["chunk_id"])
            if len(results) >= 2*top_k:
                break

        return results[:top_k]
    except Exception as e:
        # logger.error(f"Semantic search failed: {str(e)}")
        return []
# def retrieve_chunks_semantic(query: str, top_k: int = 30, machine_types: Optional[List[str]] = None) -> List[Dict]:
#     try:
#         query_embedding = get_embedding(query)
#
#         # Create a filter where filename contains any of the machine types
#         filters = None
#         if machine_types:
#             filters = models.Filter(
#                 should=[
#                     models.FieldCondition(
#                         key="filename",
#                         match=models.MatchText(text=mt)
#                     ) for mt in machine_types
#                 ]+[
#                     models.FieldCondition(
#                         key="table_filename",
#                         match=models.MatchText(text=mt)
#                     ) for mt in machine_types
#                 ]
#             )
#
#         response = client.search(
#             collection_name=collection_name,
#             query_vector=query_embedding,
#             limit=top_k,
#             with_payload=True,
#             query_filter=filters
#         )
#         return [process_match(m) | {"search_type": "semantic"} for m in response]
#     except Exception as e:
#         # logger.error(f"Semantic search failed: {str(e)}")
#         return []

def retrieve_by_payload(part_number: str, top_k: int = 20, machine_types: Optional[List[str]] = None, collection_id: Optional[str] = None) -> List[Dict]:
    qdrant_url = "http://3.101.65.253"
    qdrant_port = 5333
    collection_name = "toshiba_demo_4" if not collection_id else collection_id
    print("Collection id in payload: ", collection_id)

    client = QdrantClient(url=qdrant_url, port=qdrant_port, timeout=300.0, check_compatibility=False)
    if machine_types:
        filters = models.Filter(should=[
            models.Filter(must=[
                models.FieldCondition(key="is_table", match=models.MatchValue(value=True)),
                models.FieldCondition(key="table_factual_sentences", match=models.MatchText(text=part_number)),
                # models.FieldCondition(key="filename", match=models.MatchAny(any=machine_types))
            ]),
            models.Filter(must=[
                models.FieldCondition(key="is_table", match=models.MatchValue(value=False)),
                models.FieldCondition(key="chunk_text", match=models.MatchText(text=part_number)),
                # models.FieldCondition(key="filename", match=models.MatchAny(any=machine_types))
            ]),
            # Filter by filename
        models.Filter(should=[
            models.FieldCondition(key="filename", match=models.MatchAny(any=machine_types))
        ])
        ])
    else:
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

# def retrieve_by_keywords(keywords: List[str], top_k: int = 20, machine_types: Optional[List[str]] = None) -> List[Dict]:
#     if not keywords:
#         return []
#
#     # keyword_conditions = [
#     #     [
#     #     models.FieldCondition(key="is_table", match=models.MatchValue(value=True)),
#     #     models.FieldCondition(
#     #         key="chunk_text",
#     #         match=models.MatchText(text=kw)
#     #
#     #     )] for kw in keywords
#     # ]
#     # filters = models.Filter(should=[
#     #     models.Filter(must=[
#     #         models.FieldCondition(key="is_table", match=models.MatchValue(value=True)),
#     #         models.FieldCondition(key="table_factual_sentences", match=models.MatchText(text=kw[0]))
#     #     ]),
#     #     models.Filter(must=[
#     #         models.FieldCondition(key="is_table", match=models.MatchValue(value=False)),
#     #         models.FieldCondition(key="chunk_text", match=models.MatchText(text=kw[1]))
#     #     ])
#     # ],
#     #     # Filter by filename
#     #     must=[
#     #     models.Filter(should=[
#     #         models.FieldCondition(key="filename", match=models.MatchAny(any=machine_types))
#     #     ])
#     # ])
#     print("Keywords: ", keywords)
#     print("Machine type: ", machine_types)
#
#     try:
#         matches = []
#         for kw in keywords:
#             for mt in machine_types:
#                 filters = models.Filter(should=[
#                     models.Filter(must=[
#                         models.FieldCondition(key="is_table", match=models.MatchValue(value=True)),
#                                 models.FieldCondition(key="table_factual_sentences", match=models.MatchText(text=kw)),
#                         models.FieldCondition(key="table_filename", match=models.MatchText(text=mt)),
#
#                     ]),
#                     models.Filter(must=[
#                                 models.FieldCondition(key="is_table", match=models.MatchValue(value=False)),
#                                 models.FieldCondition(key="chunk_text", match=models.MatchText(text=kw)),
#                         models.FieldCondition(key="filename", match=models.MatchText(text=mt)),
#
#                     ]),
#                     # models.FieldCondition(key="filename", match=models.MatchAny(any=machine_types))
#                 ],
#                     # Filter by filename
#                     # must=[
#                     # models.FieldCondition(key="filename", match=models.MatchText(text=mt))
#                 # ]
#                 )
#
#                 response = client.scroll(
#                     collection_name=collection_name,
#                     scroll_filter=filters,
#                     limit=top_k,
#                     with_payload=True,
#                     with_vectors=False
#                 )
#                 print("Response: ", response)
#                 matches.extend(response[0])
#                 print("Matches: ", len(matches))
#         print("Matches: ", len(matches))
#         return [process_match(m) | {"search_type": "sparse_keyword"} for m in matches]
#     except Exception as e:
#         # logger.error(f"Sparse keyword retrieval failed: {str(e)}")
#         return []
def retrieve_by_keywords(keywords: List[str], top_k: int = 20, machine_types: Optional[List[str]] = None, collection_id: Optional[str] = None) -> List[Dict]:
    if not keywords:
        return []

    qdrant_url = "http://3.101.65.253"
    qdrant_port = 5333
    collection_name = "toshiba_demo_4" if not collection_id else collection_id
    print("Collection id in keyword: ", collection_id)

    client = QdrantClient(url=qdrant_url, port=qdrant_port, timeout=300.0, check_compatibility=False)

    # print("Keywords: ", keywords)
    # print("Machine type: ", machine_types)

    try:
        if machine_types:
            filters = models.Filter(should=[
                models.Filter(must=[
                    models.FieldCondition(key="is_table", match=models.MatchValue(value=True)),
                    models.FieldCondition(key="table_factual_sentences", match=models.MatchText(text=kw)),
                    models.Filter(should=[
                    models.FieldCondition(key="table_filename", match=models.MatchText(text=mt)),
                        models.FieldCondition(key="filename", match=models.MatchText(text=mt)),
                        ]),
                ])
                for kw in keywords for mt in machine_types
            ] + [
                models.Filter(must=[
                    models.FieldCondition(key="is_table", match=models.MatchValue(value=True)),
                    models.FieldCondition(key="chunk_text", match=models.MatchText(text=kw)),
                    models.Filter(should=[
                        models.FieldCondition(key="table_filename", match=models.MatchText(text=mt)),
                        models.FieldCondition(key="filename", match=models.MatchText(text=mt)),
                    ]),
                ])
                for kw in keywords for mt in machine_types
            ]+[
                models.Filter(must=[
                    models.FieldCondition(key="is_table", match=models.MatchValue(value=False)),
                    models.FieldCondition(key="chunk_text", match=models.MatchText(text=kw)),
                    models.Filter(should=[
                        models.FieldCondition(key="table_filename", match=models.MatchText(text=mt)),
                        models.FieldCondition(key="filename", match=models.MatchText(text=mt)),
                    ]),
                ])
                for kw in keywords for mt in machine_types
            ]

                                    )
        else:
            # print("No machine type")
            filters = models.Filter(should=[
                models.Filter(must=[
                    models.FieldCondition(key="is_table", match=models.MatchValue(value=True)),
                    models.FieldCondition(key="table_factual_sentences", match=models.MatchText(text=kw)),
                ])
                for kw in keywords
            ] + [
                models.Filter(must=[
                    models.FieldCondition(key="is_table", match=models.MatchValue(value=True)),
                    models.FieldCondition(key="chunk_text", match=models.MatchText(text=kw)),
                ])
                for kw in keywords
            ]+ [
                models.Filter(must=[
                    models.FieldCondition(key="is_table", match=models.MatchValue(value=False)),
                    models.FieldCondition(key="chunk_text", match=models.MatchText(text=kw)),
                ])
                for kw in keywords
            ])

        response = client.scroll(
            collection_name=collection_name,
            scroll_filter=filters,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        matches = response[0]
        # print("Matches: ", len(matches))
        return [process_match(m) | {"search_type": "sparse_keyword"} for m in matches]
    except Exception as e:
        # logger.error(f"Sparse keyword retrieval failed: {str(e)}")
        return []

# multi-search mechanism
def multi_strategy_search(query: str, top_k: int = 30, machine_types: Optional[List[str]] = None) -> List[Dict]:
    seen_ids = set()
    results = []

    # Semantic retrieval
    semantic_results = retrieve_chunks_semantic(query, top_k=top_k, machine_types=machine_types)
    # print("Semantic results: ", semantic_results)
    results.extend([r for r in semantic_results if r["chunk_id"] not in seen_ids and not seen_ids.add(r["chunk_id"])])

    #  Exact match retrieval (part numbers)
    part_numbers = extract_part_numbers(query)
    # print("Part numbers: ", part_numbers)
    for pn in part_numbers:
        payload_matches = retrieve_by_payload(pn, machine_types=machine_types)
        results.extend([r for r in payload_matches if r["chunk_id"] not in seen_ids and not seen_ids.add(r["chunk_id"])])
        # print("Payload matches: ", payload_matches)

    #  Sparse keyword retrieval
    keywords = extract_keywords(query)
    # print("Keywords: ", keywords)
    sparse_matches = retrieve_by_keywords(keywords, top_k=10, machine_types=machine_types)
    # print("Sparse matches: ", sparse_matches)
    results.extend([r for r in sparse_matches if r["chunk_id"] not in seen_ids and not seen_ids.add(r["chunk_id"])])

    return sorted(results, key=lambda x: x["score"], reverse=True)[:top_k]

def enhanced_hybrid_search(query: str, top_k: int = 30, is_table: Optional[bool] = None,machine_types: Optional[List[str]] = None) -> List[Dict]:
    # logger.info("Using enhanced_hybrid_search")
    return multi_strategy_search(query, top_k=top_k, machine_types=machine_types)


# enhanced_hybrid_search("what is loader", top_k=30, machine_types=["6800"])

