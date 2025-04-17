from typing import List, Tuple
import matplotlib.pyplot as plt
import numpy as np

def get_best_segments_greedy(relevance_values: list, max_length: int, overall_max_length: int, minimum_value: float):
    best_segments = []
    scores = []
    total_length = 0
    while total_length < overall_max_length:
        best_segment = None
        best_value = -1000
        for start in range(len(relevance_values)):
            if relevance_values[start] < 0:
                continue
            for end in range(start+1, min(start+max_length+1, len(relevance_values)+1)):
                if relevance_values[end-1] < 0:
                    continue
                if any(start < seg_end and end > seg_start for seg_start, seg_end in best_segments):
                    continue
                if total_length + end - start > overall_max_length:
                    continue
                segment_value = sum(relevance_values[start:end])
                if segment_value > best_value:
                    best_value = segment_value
                    best_segment = (start, end)
        if best_segment is None or best_value < minimum_value:
            break
        best_segments.append(best_segment)
        scores.append(best_value)
        total_length += best_segment[1] - best_segment[0]
    return best_segments, scores

def get_best_segments_sliding_window(relevance_values: List[float], max_length: int, overall_max_length: int, minimum_value: float) -> Tuple[List[Tuple[int, int]], List[float]]:
    best_segments = []
    scores = []
    total_length = 0
    used_indices = set()
    for window_size in range(max_length, 0, -1):
        for start in range(len(relevance_values) - window_size + 1):
            end = start + window_size
            if any(i in used_indices for i in range(start, end)):
                continue
            segment_score = sum(relevance_values[start:end])
            if segment_score >= minimum_value:
                best_segments.append((start, end))
                scores.append(segment_score)
                used_indices.update(range(start, end))
                total_length += (end - start)
            if total_length >= overall_max_length:
                break
        if total_length >= overall_max_length:
            break
    return best_segments, scores

def get_best_segments(relevance_values, max_length, overall_max_length, minimum_value, method="greedy"):
    if method == "sliding":
        return get_best_segments_sliding_window(relevance_values, max_length, overall_max_length, minimum_value)
    return get_best_segments_greedy(relevance_values, max_length, overall_max_length, minimum_value)

def plot_relevance_with_segments(chunk_values: List[float], segments: List[Tuple[int, int]]) -> None:
    plt.figure(figsize=(14, 6))
    plt.title("Query-Chuck Relevance with Selected Segments")
    plt.xlabel("Chunk Index")
    plt.ylabel("Relevance Score")
    plt.ylim(0, 1.05)
    plt.plot(range(len(chunk_values)), chunk_values, marker='o', label="Relevance Scores")
    for start, end in segments:
        plt.axvspan(start, end-1, color='green', alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.show()

def print_segments_with_metadata(segments: List[Tuple[int, int]], chunk_texts: List[str], chunks: List[dict], scores: List[float]) -> None:
    for i, (start, end) in enumerate(segments):
        print(f"\n🔹 Segment {i+1} (Score: {scores[i]:.4f})")
        meta = chunks[start]
        print(f"📄 File: {meta.get('filename')} | Pages: {meta.get('page_range')} | Header: {meta.get('contextual_header')}")
        for j in range(start, end):
            print(f"\nChunk {j}:{chunk_texts[j][:300]}...")

# if __name__ == "__main__":
#     from cohere_reranker import rerank_chunks, retrieve_chunks

#     user_query = "how to setup the Arlo pro 5 camera?"
#     chunks = retrieve_chunks(user_query, top_k=20)
#     chunk_texts = [chunk["chunk_text"] for chunk in chunks]
#     _, chunk_values = rerank_chunks(user_query, chunk_texts)

#     irrelevant_chunk_penalty = 0.2
#     max_length = 20
#     overall_max_length = 30
#     minimum_value = 0.3
#     method = "greedy"  # Change to "sliding" to try the other strategy

#     # relevance_values = [v - irrelevant_chunk_penalty for v in chunk_values]
#     relevance_values = chunk_values

#     best_segments, scores = get_best_segments(relevance_values, max_length, overall_max_length, minimum_value, method=method)

#     print("\nBest segment indices:", best_segments)
#     print("\nBest segment scores:", scores)
#     print_segments_with_metadata(best_segments, chunk_texts, chunks, scores)
#     plot_relevance_with_segments(chunk_values, best_segments)
