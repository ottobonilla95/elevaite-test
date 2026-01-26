import hashlib
import json
import os
import time
import re
from openai import OpenAI
from typing import List, Dict
from ..retrieval_stage.retrieve_qdrant import retrieve_chunks_semantic

# In-memory rerank cache
rerank_cache = {}

# OpenAI Client setup
openai_api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)


def generate_cache_key(query: str, chunks: List[Dict]) -> str:
    """
    Generate a hash key from the query and chunk IDs.
    """
    base = {"query": query, "chunks": [chunk["chunk_id"] for chunk in chunks]}
    return hashlib.md5(json.dumps(base, sort_keys=True).encode()).hexdigest()


def format_chunk_with_context(chunk: Dict) -> str:
    """
    Combine contextual_header and chunk_text for reranking input.
    """
    contextual_header = chunk.get("contextual_header", "")
    chunk_text = chunk.get("chunk_text", "")
    return f"Context: {contextual_header}\n\nContent: {chunk_text}"


def instruction_rerank_openai(query: str, chunks: List[Dict], top_k: int = 3, model: str = "gpt-4") -> List[Dict]:
    """
    Rerank retrieved chunks using OpenAI's GPT-3.5/4 with instruction-following prompt.
    """
    cache_key = generate_cache_key(query, chunks)
    if cache_key in rerank_cache:
        print("⚡ Returning reranked results from cache")
        return rerank_cache[cache_key]

    # Combine each chunk into a string with context
    formatted_chunks = [format_chunk_with_context(chunk) for chunk in chunks]
    passage_block = "\n\n".join([f"[{i + 1}] {text}" for i, text in enumerate(formatted_chunks)])

    # Instructional prompt for reranking
    prompt = (
        f"You are an expert assistant. Given a user question and multiple text chunks, your goal is to rank only those chunks that **directly contain or imply the factual answer** to the user’s question.\n\n"
        f"Ignore chunks that discuss general concepts, background, or theory **unless they directly help answer the question**.\n\n"
        f"User Question: '{query}'\n\n"
        f"Return only the most relevant chunks by their index. Prefer concise and factual information.\n\n"
        f"{passage_block}"
    )

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant that reranks search results."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
        )
        reply = response.choices[0].message.content
        print("\n🔁 Reranker Reply:", reply)
    except Exception as e:
        print(f"❌ Reranker failed: {e}")
        return chunks[:top_k]

    # Extract top-k indices from LLM response
    if reply is None:
        return chunks[:top_k]
    indices = [int(num) - 1 for num in re.findall(pattern=r"\b\d+\b", query=reply) if 0 < int(num) <= len(chunks)]

    # Remove duplicates while preserving order
    seen = set()
    reranked = []
    for i in indices:
        if i not in seen:
            reranked.append(chunks[i])
            seen.add(i)
        if len(reranked) >= top_k:
            break

    if len(indices) != len(set(indices)):
        print("⚠️ Duplicate indices detected in reranker reply. De-duplicated for safety.")

    # Fallback if not enough reranked chunks
    if len(reranked) < top_k:
        remaining = [chunk for i, chunk in enumerate(chunks) if i not in seen]
        reranked += remaining[: top_k - len(reranked)]

    rerank_cache[cache_key] = reranked
    return reranked


# Run as script
if __name__ == "__main__":
    user_query = "what is the angle of the Tower of Pisa?"
    start_time = time.time()

    retrieved_chunks = retrieve_chunks_semantic(user_query, top_k=5)
    print(f"\n📄 Retrieved {len(retrieved_chunks)} chunks in {(time.time() - start_time):.2f} seconds")

    if retrieved_chunks:
        reranked_chunks = instruction_rerank_openai(user_query, retrieved_chunks, top_k=5, model="gpt-3.5-turbo")

        print("\n🏆 Top Reranked Chunks:")
        for i, res in enumerate(reranked_chunks, 1):
            print(f"\n🔹 Rank {i}")
            print(f"Chunk ID: {res['chunk_id']}")
            print(f"Score: {res['score']:.4f}")
            print(f"Header: {res.get('contextual_header')}")
            print(f"Text: {res['chunk_text']}")
