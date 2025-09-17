import os
import time
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
from dotenv import load_dotenv

from elevaite_ingestion.stage.post_retrieval.generate_answer_openai import generate_answer
from elevaite_ingestion.stage.post_retrieval.cohere_reranker import rerank_chunks, retrieve_chunks
from elevaite_ingestion.stage.post_retrieval.rse import (
    get_best_segments_greedy,
    plot_relevance_with_segments,
    print_segments_with_metadata,
)

load_dotenv()

st.set_page_config(page_title="Stage 6: RSE", layout="wide")

st.markdown("### Query the Knowledge Base")
query = st.text_input("Enter your query:")

if query:
    st.markdown("---")
    with st.spinner("Running retrieval and reranking..."):
        chunks = retrieve_chunks(query, top_k=20)
        chunk_texts = [chunk["chunk_text"] for chunk in chunks]
        _, chunk_values = rerank_chunks(query, chunk_texts)

    irrelevant_chunk_penalty = 0.2
    max_length = 4
    overall_max_length = 12
    minimum_value = 0.4

    relevance_values = [v - irrelevant_chunk_penalty for v in chunk_values]
    start_time = time.time()
    best_segments, scores = get_best_segments_greedy(
        relevance_values, max_length, overall_max_length, minimum_value
    )
    end_time = time.time()
    retrieval_time = (end_time - start_time) * 1000

    st.markdown("### Relevance Scores and Selected Segments")
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.set_title("Query-Chunk Relevance with Selected Segments")
    ax.set_xlabel("Chunk Index")
    ax.set_ylabel("Relevance Score")
    ax.set_ylim(0, 1.05)
    ax.plot(range(len(chunk_values)), chunk_values, marker='o', label="Relevance Scores")
    for start, end in best_segments:
        ax.axvspan(start, end - 1, color='green', alpha=0.3)
    ax.legend()
    st.pyplot(fig)
    st.markdown("---")

    st.markdown("### Selected Segments with Metadata")
    for i, (start, end) in enumerate(best_segments):
        with st.expander(f"SEGMENT {i+1} | Score: {scores[i]:.4f} | Retrieval latency: {retrieval_time:.2f} ms"):
            for j in range(start, end):
                meta = chunks[j]
                st.markdown(f"**Chunk {j}**")
                st.markdown(f"- Filename: `{meta.get('filename')}`")
                st.markdown(f"- Pages: `{meta.get('page_range')}`")
                st.markdown(f"- Matched Image Path: `{meta.get('matched_image_path')}`")
                st.markdown(f"- Header: `{meta.get('contextual_header')}`")
                st.code(chunk_texts[j], language="markdown")

                image_path = meta.get("matched_image_path")
                if image_path and os.path.exists(image_path):
                    if st.checkbox("Display matched Image", key=f"show_img_{j}"):
                        st.image(image_path, caption="Matched Figure", use_container_width=True)
                elif image_path:
                    st.warning(f"Image not found at: {image_path}")

    st.markdown("---")

    st.markdown("### Answer Generated from Top Segment")
    top_segment_texts = []
    for j in range(best_segments[0][0], best_segments[0][1]):
        meta = chunks[j]
        header = meta.get("contextual_header", "")
        top_segment_texts.append(f"{header}\n{chunk_texts[j]}")

    if st.button("Generate Answer"):
        with st.spinner("Generating answer from top segment..."):
            generation_start_time = time.time()
            answer = generate_answer(query, top_segment_texts)
            generation_end_time = time.time()
            total_generation_time = (generation_end_time - generation_start_time)
            st.markdown(f"Generation latency: {total_generation_time:.2f} seconds")
        st.success(answer)

    st.markdown("---")

