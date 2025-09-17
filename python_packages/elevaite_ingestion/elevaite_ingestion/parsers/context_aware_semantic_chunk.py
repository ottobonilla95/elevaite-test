import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from openai import OpenAI
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
        return [[0] * 1536 for _ in texts]  # Return zero vectors to maintain shape consistency

def semantic_chunking(sentences, threshold=0.8, force_split_on_page_change=True):
    """
    Performs sequential semantic chunking based on cosine similarity of consecutive sentences.

    Args:
        sentences (list): List of enriched SentenceDocument objects.
        threshold (float): Similarity threshold to define chunk boundaries.
        force_split_on_page_change (bool): If True, forces a chunk split when a new page starts.

    Returns:
        list: List of chunks with metadata.
    """
    sentence_texts = [sent.sentence_text for sent in sentences]
    embeddings = np.array(get_embeddings(sentence_texts))

    if embeddings.ndim == 1:  # If only one sentence, reshape properly
        embeddings = embeddings.reshape(1, -1)

    # Compute cosine similarity between consecutive sentences
    similarities = [
        cosine_similarity(embeddings[i].reshape(1, -1), embeddings[i + 1].reshape(1, -1))[0][0] 
        for i in range(len(embeddings) - 1)
    ]

    print("\n🔎 **Similarity Scores Between Consecutive Sentences**")
    print(similarities)  # ✅ Debugging similarity scores

    chunks = []
    current_chunk = []
    chunk_page_numbers = set()
    
    for i, sentence in enumerate(sentences):
        if i > 0:
            similarity = similarities[i - 1]

            # ✅ Force chunk split if similarity drops below the threshold
            if similarity < threshold and current_chunk:
                print(f"\n🛑 **Chunk Split at Sentence {i+1} (Similarity: {similarity:.2f})**")
                chunks.append({
                    "text": " ".join(current_chunk),
                    "pages": sorted(list(chunk_page_numbers))
                })
                current_chunk = []
                chunk_page_numbers = set()

            # ✅ Force chunk split if page changes
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
    semantic_chunks = semantic_chunking(enriched_sentences)

    with open("semantic_chunks.json", "w") as f:
        json.dump(semantic_chunks, f, indent=4)
