from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Dict, Optional, Union
import time
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware

from retrieval_stage.retrieve_qdrant import multi_strategy_search as enhanced_hybrid_search
from post_retrieval.cohere_reranker import rerank_separately_then_merge
from post_retrieval.rse import get_best_segments

load_dotenv(".env")

origins = [
    "http://127.0.0.1:3002",
    "*"
    ]

class QueryRequest(BaseModel):
    query: str
    top_k: int = 60
    segment_max_length: int = 4
    overall_max_length: int = 16
    minimum_value: float = 0.35
    irrelevant_chunk_penalty: float = 0.1
    segment_method: str = "greedy"
    machine_types: Optional[List[str]] = None
    collection_id: Optional[str] = None
    customer_name: Optional[str] = None

app = FastAPI()

@app.post("/query")
async def query_kb(request: QueryRequest):
    try:
        total_start_time = time.time()

        retrieval_start_time = time.time()
        retrieved_chunks, chunk_values = rerank_separately_then_merge(
            query=request.query, 
            top_k=request.top_k,
            machine_types=request.machine_types,
            collection_id=request.collection_id
        )
        retrieval_time = (time.time() - retrieval_start_time) * 1000

        if not retrieved_chunks:
            raise HTTPException(status_code=404, detail="No relevant information found for the given query.")

        relevance_values = [v - request.irrelevant_chunk_penalty for v in chunk_values]

        segment_start_time = time.time()
        best_segments, scores = get_best_segments(
            relevance_values=relevance_values,
            max_length=request.segment_max_length,
            overall_max_length=request.overall_max_length,
            minimum_value=request.minimum_value,
            method=request.segment_method
        )
        segment_time = (time.time() - segment_start_time) * 1000

        selected_segments = []
        for i, (start, end) in enumerate(best_segments):
            segment_chunks = []
            for j in range(start, end):
                chunk = retrieved_chunks[j]
                segment_chunks.append({
                    "chunk_id": chunk["chunk_id"],
                    "chunk_text": chunk["chunk_text"],
                    "is_table": chunk.get("is_table", False),
                    "filename": chunk.get("filename"),
                    "page_info": chunk.get("page_info"),
                    "contextual_header": chunk.get("contextual_header"),
                    "matched_image_path": chunk.get("matched_image_path"),
                    "search_type": chunk.get("search_type", "semantic"),
                    "relevance_score": chunk_values[j],
                    "customer_name": chunk.get("customer_name"),
                    "email_sent_datetime": chunk.get("email_sent_datetime", "N/A")
                })

            segment_metadata = {
                "segment_id": i + 1,
                "score": scores[i],
                "chunks": segment_chunks
            }
            selected_segments.append(segment_metadata)

        total_time = (time.time() - total_start_time) * 1000

        return {
            "query": request.query,
            "selected_segments": selected_segments,
            "metrics": {
                "total_retrieved_chunks": len(retrieved_chunks),
                "selected_segment_count": len(best_segments),
                "retrieval_time_ms": retrieval_time,
                "segment_selection_time_ms": segment_time,
                "total_processing_time_ms": total_time
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post("/query-chunks")
async def query_chunks_api(query: str, top_k: int = Query(20), machine_types: Optional[List[str]] = Query(None), collection_id: Optional[str] = Query(None), customer_name: Optional[str] = Query(None)):
    print("Customer query: ",query)
    print("Collection id: ",collection_id)
    print("Customer name: ",customer_name)
    request = QueryRequest(query=query, top_k=top_k, machine_types=machine_types, collection_id=collection_id, customer_name=customer_name)
    return await query_kb(request)

if __name__ == "__main__":
    import uvicorn

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization'],
    )
    uvicorn.run(app, host="0.0.0.0", port=8002)
