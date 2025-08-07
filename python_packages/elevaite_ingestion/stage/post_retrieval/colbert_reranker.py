# colbert_reranker.py

import os
import sys
import time
from typing import List, Dict

# ColBERT imports
from colbert import Searcher

# Add base path for relative imports
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_path)

from retrieval_stage.retrieve_qdrant import retrieve_chunks

# Path to ColBERT prebuilt index (must be built beforehand using ColBERT indexing pipeline)
COLBERT_INDEX_PATH = os.getenv("COLBERT_INDEX_PATH", "colbert/indexes/pisa_index")
searcher = Searcher(index=COLBERT_INDEX_PATH)

def colbert_rerank(query: str, chunks: List[Dict], top_k: int = 3) -> List[Dict]:
    # Extract raw texts from chunks
    texts = [chunk["chunk_text"] for chunk in chunks]

    # Simulate ranking using Searcher's score (note: real ColBERT usage requires indexing these chunks first)
    # This is a simulated reranking by querying the original corpus index and matching returned scores
    print("⚠️ NOTE: This is a simulated reranker. True reranking requires ColBERT pre-indexed corpus.")

    results = searcher.search(query, k=top_k)
    # Each result: {'docid': int, 'score': float, 'text': str}
    top_chunks = []
    seen_ids = set()
    for result in results:
        matched = next((chunk for chunk in chunks if result['text'].strip() in chunk['chunk_text'] and chunk['chunk_id'] not in seen_ids), None)
        if matched:
            top_chunks.append(matched)
            seen_ids.add(matched['chunk_id'])
        if len(top_chunks) == top_k:
            break
    return top_chunks

if __name__ == "__main__":
    user_query = "what is the angle of the Tower of Pisa?"
    start_time = time.time()

    retrieved_chunks = retrieve_chunks(user_query, top_k=10)
    print(f"\n📄 Retrieved {len(retrieved_chunks)} chunks in {(time.time() - start_time):.2f} seconds")

    if retrieved_chunks:
        print("\n--- ColBERT Rerank ---")
        reranked_chunks = colbert_rerank(user_query, retrieved_chunks, top_k=3)

        for i, res in enumerate(reranked_chunks, 1):
            print(f"\n🔹 Rank {i}")
            print(f"Chunk ID: {res['chunk_id']}")
            print(f"Header: {res.get('contextual_header')}")
            print(f"Text: {res['chunk_text']}")
