
import os
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from scipy.stats import beta
from typing import List, Dict
import cohere
from dotenv import load_dotenv
load_dotenv()

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(base_path)

from retrieval_stage.retrieve_qdrant import retrieve_chunks

cohere_client = cohere.Client(os.getenv("COHERE_API_KEY"))

def transform(x: float):
    """
    Transformation function to map the absolute relevance value to a value that is more uniformly distributed between 0 and 1.
    """
    a, b = 0.4, 0.4
    return beta.cdf(x, a, b)

def cohere_rerank(query: str, chunks: List[Dict], top_k: int = 20) -> List[Dict]:
    inputs = [chunk["chunk_text"] for chunk in chunks]
    response = cohere_client.rerank(
        query=query,
        documents=inputs,
        top_n=top_k,
        model="rerank-english-v3.0"
    )
    return [chunks[result.index] for result in response.results]

def rerank_chunks(query: str, chunks: List[str]):
    """
    Use Cohere Rerank API to rerank the search results and compute relevance values.
    """
    model = "rerank-english-v3.0"
    client = cohere.Client(api_key=os.environ["COHERE_API_KEY"])
    decay_rate = 30

    reranked_results = client.rerank(model=model, query=query, documents=chunks)
    results = reranked_results.results
    reranked_indices = [result.index for result in results]
    reranked_similarity_scores = [result.relevance_score for result in results]
    print("##############ranked_similarity")
    print(reranked_similarity_scores)

    similarity_scores = [0] * len(chunks)
    chunk_values = [0] * len(chunks)
    for i, index in enumerate(reranked_indices):
        absolute_relevance_value = transform(reranked_similarity_scores[i])
        similarity_scores[index] = absolute_relevance_value
        chunk_values[index] = np.exp(-i / decay_rate) * absolute_relevance_value

    return similarity_scores, chunk_values


def plot_relevance_scores(chunk_values: List[float], start_index: int = None, end_index: int = None) -> None:
    """
    Visualize the relevance scores of each chunk in the document to the search query.
    """
    plt.figure(figsize=(12, 5))
    plt.title("Reelevancy of each chunk in the document to the search query")
    plt.ylim(0, 1)
    plt.xlabel("Chunk index")
    plt.ylabel("Query-chunk relevance")
    if start_index is None:
        start_index = 0
    if end_index is None:
        end_index = len(chunk_values)
    plt.scatter(range(start_index, end_index), chunk_values[start_index:end_index])
    plt.show()


# if __name__ == "__main__":
#     # user_query = "what is the angle of the Tower of Pisa?"
#     user_query = "provide lists the humidity and temperature limits for the 4820 SurePoint Solution"
#     start_time = time.time()

#     retrieved_chunks = retrieve_chunks(user_query, top_k=20)
#     print(f"\nRetrieved {len(retrieved_chunks)} chunks in {(time.time() - start_time):.2f} seconds")

#     if retrieved_chunks:
#         print("\n--- Cohere Rerank + Relevance Scoring ---")
#         chunk_texts = [chunk["chunk_text"] for chunk in retrieved_chunks]
#         similarity_scores, chunk_values = rerank_chunks(user_query, chunk_texts)

#         for i, val in enumerate(chunk_values):
#             print(f"Chunk {i} - Score: {val:.4f} | Text: {chunk_texts[i]}")

#         plot_relevance_scores(chunk_values)

