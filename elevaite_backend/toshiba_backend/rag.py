import os
import sys
import time
from qdrant_client import QdrantClient
from qdrant_client.http import models
import matplotlib.pyplot as plt
from typing import List, Dict

import os
from typing import List
from dotenv import load_dotenv
import openai

def get_chunks(query: str):

    load_dotenv('.env.local')
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found. Please set it in the environment variables.")

    client = openai.OpenAI(api_key=api_key)

    def get_embedding(text: str) -> List[float]:
        try:
            response = client.embeddings.create(
                model="text-embedding-ada-002",
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            # print(f"Error generating embedding: {e}")
            return [0] * 1536

    path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sys.path.append(path)

    # from embedding_factory.openai_embedder import get_embedding
    # from utils.logger import get_logger
    # from config.vector_db_config import VECTOR_DB_CONFIG

    # logger = get_logger(__name__)

    # qdrant_config = VECTOR_DB_CONFIG.get("qdrant", {})

    # qdrant_url = qdrant_config.get("host")
    # qdrant_port = qdrant_config.get("port")
    # collection_name = qdrant_config.get("collection_name")
    # print('##################collection name')
    # print(collection_name)
    qdrant_url = "http://3.101.65.253"
    qdrant_port = 5333
    collection_name = "toshiba_pdf_7"

    client = QdrantClient(url=qdrant_url, port=qdrant_port)

    # try:
    #     collections = client.get_collections().collections
    #     collection_names = [col.name for col in collections]
    #
    #     if collection_name not in collection_names:
    #         logger.error(f" Collection '{collection_name}' does not exist in Qdrant.")
    #         sys.exit(1)
    #     else:
    #         logger.info(f"Collection '{collection_name}' found in Qdrant!")

    # except Exception as e:
    #     logger.error(f" Failed to fetch Qdrant collections: {e}")
    #     sys.exit(1)


    def retrieve_chunks(query: str, top_k: int = 20):
        """
        Retrieve top-k similar chunks from Qdrant based on a query.

        Args:
            query (str): User query to search for similar chunks.
            top_k (int): Number of top similar chunks to retrieve.

        Returns:
            list: List of dictionaries with chunk_id, score, and chunk_text.
        """
        try:
            query_embedding = get_embedding(query)
        except Exception as e:
            # logger.error(f"Failed to generate embedding: {e}")
            return []

        try:
            response = client.search(
                collection_name=collection_name,
                query_vector=query_embedding,
                limit=top_k,
                with_payload=True,
            )
        except Exception as e:
            # logger.error(f"Query to Qdrant failed: {e}")
            return []

        if not response:
            # logger.info(" No matches found.")
            return []

        results = []
        for match in response:
            chunk_id = match.id
            score = match.score
            contextual_header = match.payload.get("contexual_header")
            chunk_text = match.payload.get("chunk_text", "No text found")
            filename = match.payload.get("filename", "Unknwoun")
            page_range = match.payload.get("page_range", "Unknwoun")

            # result = {
            #     "chunk_id": chunk_id,
            #     "score": score,
            #     "contextual_header": contextual_header,
            #     "chunk_text": chunk_text,
            #     "filename": filename,
            #     "page_range": page_range,
            #     "start_paragraph": start_paragraph,
            #     "end_paragraph": end_paragraph
            # }

            result = {
                "chunk_id": chunk_id,
                "score": score,
                "contextual_header": contextual_header,
                "chunk_text": chunk_text,
                "filename": filename,
                "page_range": page_range,
                "matched_image_path": match.payload.get("matched_image_path"),

            }

            results.append(result)
            # logger.info(f"==>Chunk ID: {chunk_id} | Score: {score:.4f} | Text Length: {len(chunk_text)}")

        return results

    res = retrieve_chunks(query)
    # for r in res:
    #     # print(r.keys())
    #     print(f"Chunk ID: {r['chunk_id']}, Score: {r['score']:.4f}, Text Length: {len(r['chunk_text'])}, Filename: {r['filename']}, Page Range: {r['page_range']}")
    res = "Here is the retrieved info from Toshiba DB"+f"\n\n".join(f"Chunk {i}:"+res["chunk_text"] for i,res in enumerate(res))
    # print(res)
    return res

# print(get_chunks("What is the description for the part number 3AC01317900"))
print(get_chunks("What is the description for the part number 3AC00668900"))