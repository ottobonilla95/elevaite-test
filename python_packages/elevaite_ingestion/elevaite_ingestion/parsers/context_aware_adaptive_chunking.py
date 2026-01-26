import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from custom_parser import PdfParser, enrich_sentence_with_context
import json
import openai
import os
from typing import List
from dotenv import load_dotenv
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found. Please set it in the environment variables.")

client = openai.OpenAI(api_key=api_key) 

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Get embeddings for a list of texts using OpenAI's embedding model.

    Args:
        texts (List[str]): List of text strings.

    Returns:
        List[List[float]]: List of embeddings.
    """
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=texts  
        )
        return [data.embedding for data in response.data]
    except Exception as e:
        print(f"❌ Error generating embedding: {e}")
        return [[0] * 1536 for _ in texts]

def adaptive_chunking(sentences, drop_threshold=0.3, force_split_on_page_change=False):
    """
    Performs adaptive semantic chunking based on dynamic similarity drop detection.

    Args:
        sentences (list): List of enriched SentenceDocument objects.
        drop_threshold (float): Minimum drop in similarity score required to trigger a chunk split.
        force_split_on_page_change (bool): If True, forces a chunk split when a new page starts.

    Returns:
        list: List of chunks with metadata.
    """
    sentence_texts = [sent.sentence_text for sent in sentences]
    embeddings = np.array(get_embeddings(sentence_texts))

    if embeddings.ndim == 1: 
        embeddings = embeddings.reshape(1, -1)

    similarities = [
        cosine_similarity(embeddings[i].reshape(1, -1), embeddings[i + 1].reshape(1, -1))[0][0] 
        for i in range(len(embeddings) - 1)
    ]

    print("\n🔎 **Similarity Scores Between Consecutive Sentences**")
    print(similarities) 

    mean_sim = np.mean(similarities)
    std_sim = np.std(similarities)
    threshold = mean_sim - (std_sim * drop_threshold)

    print(f"\n🔹 **Adaptive Threshold: {threshold:.3f} (Mean: {mean_sim:.3f}, Std Dev: {std_sim:.3f})**")

    chunks = []
    current_chunk = []
    chunk_page_numbers = set()
    
    for i, sentence in enumerate(sentences):
        if i > 0:
            similarity = similarities[i - 1]

            if similarity < threshold and current_chunk:
                print(f"\n🛑 **Chunk Split at Sentence {i+1} (Similarity: {similarity:.2f})**")
                chunks.append({
                    "text": " ".join(current_chunk),
                    "pages": sorted(list(chunk_page_numbers))
                })
                current_chunk = []
                chunk_page_numbers = set()

            if force_split_on_page_change and sentences[i - 1].page_no != sentence.page_no:
                print(f"\n📄 **Chunk Split at Page Change: {sentence.page_no}**")
                chunks.append({
                    "text": " ".join(current_chunk),
                    "pages": sorted(list(chunk_page_numbers))
                })
                current_chunk = []
                chunk_page_numbers = set()

        current_chunk.append(sentence.sentence_text)
        chunk_page_numbers.add(sentence.page_no)

    if current_chunk:
        chunks.append({
            "text": " ".join(current_chunk),
            "pages": sorted(list(chunk_page_numbers))
        })

    return chunks

if __name__ == "__main__":
    file_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/INPUT/kb_arlo_check.pdf"
    
    parser = PdfParser()
    sentence_objects = parser.parse(file_path)
    enriched_sentences = enrich_sentence_with_context(sentence_objects)
    adaptive_chunks = adaptive_chunking(enriched_sentences)

    with open("adaptive_chunks.json", "w") as f:
        json.dump(adaptive_chunks, f, indent=4)
