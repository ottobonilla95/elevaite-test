import os
import sys
import re
from typing import List, Dict, Optional
from qdrant_client import AsyncQdrantClient
from qdrant_client.http import models
import nltk

path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.append(path)

import os
from dotenv import load_dotenv
import openai

STOPWORDS = set(nltk.corpus.stopwords.words('english'))

# load_dotenv("stage/.env")
# TBD - REMOVE BELOW LINE AFTER TESTING THE FUNCTION
load_dotenv(".env")
# load_dotenv("../.env")
# api_key = os.getenv("OPENAI_API_KEY")
api_key = "sk-0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000"

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


def extract_part_numbers(text: str) -> List[str]:
    patterns = [
        # r'\b\d[A-Z][A-Z]?\d{8}\b',
        # r'\b\d[A-Z]{2}\d{7}\b',
        # r'(?=.*?[0-9])(?=.*?[A-Za-z]).+',
        r'^(?=.*[0-9])(?=.*[a-zA-Z])[a-zA-Z0-9]{11}$',
        r'^(?=.*[0-9])(?=.*[a-zA-Z])[a-zA-Z0-9]{7}$',
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

async def retrieve_by_payload(part_number: str, top_k: int = 20, machine_types: Optional[List[str]] = None, collection_id: Optional[str] = None) -> List[Dict]:
    qdrant_url = "http://3.101.65.253"
    qdrant_port = 5333
    collection_name = "toshiba_demo_4" if not collection_id else collection_id

    client = AsyncQdrantClient(url=qdrant_url, port=qdrant_port, timeout=300.0, check_compatibility=False)
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
        response = await client.scroll(
            collection_name=collection_name,
            scroll_filter=filters,
            limit=top_k,
            with_payload=True,
            with_vectors=False
        )
        return [process_match(m) | {"search_type": "payload_filter"} for m in response[0]]
    except Exception:
        # logger.error(f"Payload (exact match) retrieval failed: {str(e)}")
        return []
    finally:
        await client.close()


# enhanced_hybrid_search("what is loader", top_k=30, machine_types=["6800"])
part_numbers = ["80Y1564","80Y1565","80Y1566","80Y1567","80Y1563"]*10

# async def main():
#     start = time.time()
#     tasks = [
#         retrieve_by_payload(part, machine_types=["6800"])
#         for part in part_numbers
#     ]
#     results_list = await asyncio.gather(*tasks)
#     for part, results in zip(part_numbers, results_list):
#         print(f"Results for {part}:", results)
#     print("Time taken:", time.time() - start)
#
# asyncio.run(main())