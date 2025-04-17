from fastapi import FastAPI, HTTPException
from typing import List, Dict
import time

from retrieval_stage.retrieve_qdrant import retrieve_chunks
from post_retrieval.cohere_reranker import rerank_chunks
from post_retrieval.rse import get_best_segments_greedy

app = FastAPI()

@app.post("/query-chunks")
async def query_chunks_api(query: str, top_k: int = 20):
    """
    API endpoint to retrieve and process chunks based on the query.

    Args:
        query (str): The user query.
        top_k (int): Number of top chunks to retrieve from Qdrant.

    Returns:
        dict: Processed chunks and metadata.
    """
    try:
        chunks = retrieve_chunks(query, top_k=top_k)
        if not chunks:
            raise HTTPException(status_code=404, detail="No chunks found for the given query.")

        chunk_texts = [chunk["chunk_text"] for chunk in chunks]

        _, chunk_values = rerank_chunks(query, chunk_texts)

        irrelevant_chunk_penalty = 0.2
        max_length = 4
        overall_max_length = 12
        minimum_value = 0.6

        relevance_values = [v - irrelevant_chunk_penalty for v in chunk_values]
        
        start_time = time.time()
        best_segments, scores = get_best_segments_greedy(
            relevance_values, max_length, overall_max_length, minimum_value)
        end_time = time.time()
        
        retrieval_time_ms = (end_time - start_time) * 1000

        selected_segments = []
        for i, (start, end) in enumerate(best_segments):
            segment_metadata = {
                "segment_id": i + 1,
                "score": scores[i],
                "retrieval_latency_ms": retrieval_time_ms,
                "chunks": [
                    {
                        "chunk_id": chunks[j]["chunk_id"],
                        "chunk_text": chunk_texts[j],
                        "filename": chunks[j].get("filename"),
                        "page_range": chunks[j].get("page_range"),
                        "contextual_header": chunks[j].get("contextual_header"),
                        "matched_image_path": chunks[j].get("matched_image_path"),
                    }
                    for j in range(start, end)
                ],
            }
            selected_segments.append(segment_metadata)

        return {
            "query": query,
            "selected_segments": selected_segments,
            "retrieval_latency_ms": retrieval_time_ms,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {e}")
