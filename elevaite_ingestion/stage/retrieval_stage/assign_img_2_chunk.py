# import torch
# from qdrant_client import QdrantClient
# from transformers import CLIPProcessor, CLIPModel
# from typing import List, Dict
# from tqdm import tqdm


# client = QdrantClient(url="http://3.101.65.253", port=5333)
# TEXT_COLLECTION = "toshiba_pdf_1"
# IMAGE_COLLECTION = "toshiba_images_1"

# device = "cpu"
# clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
# clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# def get_clip_text_embedding(text: str) -> List[float]:
#     """Get 512-d normalized CLIP embedding for text input."""
#     inputs = clip_processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(device)
#     with torch.no_grad():
#         outputs = clip_model.get_text_features(**inputs)
#     normalized = outputs / outputs.norm(dim=-1, keepdim=True)
#     return normalized.squeeze(0).cpu().tolist()

# def query_images(text_embedding: List[float], top_k: int = 20):
#     results = client.search(
#         collection_name=IMAGE_COLLECTION,
#         query_vector=text_embedding,
#         limit=top_k,
#         with_payload=True
#     )
#     return [
#         {
#             "image_name": r.payload.get("image_name"),
#             "image_path": r.payload.get("image_path"),
#             "page_no": r.payload.get("page_no"),
#             "score": r.score
#         } for r in results
#     ]

# def post_filter_by_page(chunk, retrieved_images, margin=1):
#     """
#     Filters retrieved images based on page proximity to the chunk's page_range.

#     Args:
#         chunk (dict): Chunk metadata with 'page_range'
#         retrieved_images (list): List of image dicts with 'page_no'
#         margin (int): Page tolerance, e.g., ±1

#     Returns:
#         List of filtered images
#     """
#     if not chunk.get("page_range"):
#         return []

#     pages = set()
#     for page in chunk["page_range"]:
#         pages.update([page + offset for offset in range(-margin, margin + 1)])

#     filtered = [img for img in retrieved_images if img.get("page_no") in pages]
#     return filtered

# def get_all_chunks(limit=5000):
#     return client.scroll(
#         collection_name=TEXT_COLLECTION,
#         with_payload=True,
#         with_vectors=False,
#         limit=limit
#     )[0]

# def assign_images_to_chunks():
#     chunks = get_all_chunks()
#     print(f"📦 Total Chunks Found: {len(chunks)}")

#     for chunk in tqdm(chunks, desc="Processing chunks"):
#         chunk_id = chunk.id
#         payload = chunk.payload

#         header = payload.get("contexual_header", "")
#         text = payload.get("chunk_text", "")
#         page_range = payload.get("page_range", [])

#         combined_text = f"{header} {text}".strip()
#         text_emb = get_clip_text_embedding(combined_text)

#         retrieved = query_images(text_emb, top_k=30)
#         filtered = post_filter_by_page(payload, retrieved)
#         print("#####################filtered_images")
#         print(filtered)

#         # best_match = filtered[0] if filtered else None
#         best_match = filtered

#         update_payload = {}
#         if best_match:
#             update_payload = {
#                 "matched_image_name": best_match["image_name"],
#                 "matched_image_path": best_match["image_path"],
#                 "matched_image_score": best_match["score"],
#                 "matched_image_page_no": best_match["page_no"]
#             }

#         full_payload = {**payload, **update_payload}

#         client.set_payload(
#             collection_name=TEXT_COLLECTION,
#             payload=full_payload,
#             points=[chunk_id]
#         )

#     print("✅ Completed assigning images to chunks!")

# if __name__ == "__main__":
#     assign_images_to_chunks()































































# ######################################
# # import torch
# # import re
# # from qdrant_client import QdrantClient
# # from transformers import CLIPProcessor, CLIPModel
# # from typing import List, Dict
# # from tqdm import tqdm

# # client = QdrantClient(url="http://3.101.65.253", port=5333)
# # TEXT_COLLECTION = "toshiba_pdf"
# # IMAGE_COLLECTION = "toshiba_images_1"

# # device = "cpu"
# # clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
# # clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

# # def get_clip_text_embedding(text: str) -> List[float]:
# #     inputs = clip_processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(device)
# #     with torch.no_grad():
# #         outputs = clip_model.get_text_features(**inputs)
# #     return (outputs / outputs.norm(dim=-1, keepdim=True)).squeeze(0).cpu().tolist()

# # def query_images(text_embedding: List[float], top_k: int = 10):
# #     results = client.search(
# #         collection_name=IMAGE_COLLECTION,
# #         query_vector=text_embedding,
# #         limit=top_k,
# #         with_payload=True
# #     )
# #     return [
# #         {
# #             "image_name": r.payload.get("image_name"),
# #             "image_path": r.payload.get("image_path"),
# #             "page_no": r.payload.get("page_no"),
# #             "score": r.score
# #         } for r in results
# #     ]

# # def get_all_chunks(limit=5000):
# #     return client.scroll(
# #         collection_name=TEXT_COLLECTION,
# #         with_payload=True,
# #         with_vectors=False,
# #         limit=limit
# #     )[0]

# # def get_all_images(limit=5000):
# #     return [
# #         {
# #             "image_name": p.payload.get("image_name"),
# #             "image_path": p.payload.get("image_path"),
# #             "page_no": p.payload.get("page_no")
# #         }
# #         for p in client.scroll(
# #             collection_name=IMAGE_COLLECTION,
# #             with_payload=True,
# #             with_vectors=False,
# #             limit=limit
# #         )[0]
# #     ]

# # def get_extended_page_images(page_range: List[int], all_images: List[dict], margin: int = 1):
# #     """Get all images from pages in (page_range ± margin)"""
# #     if not page_range:
# #         return []

# #     pages = set()
# #     for page in page_range:
# #         pages.update(range(page - margin, page + margin + 1))

# #     return [img for img in all_images if img["page_no"] in pages]

# # def assign_images_to_chunks():
# #     chunks = get_all_chunks()
# #     all_images = get_all_images()
# #     print(f"📦 Total Chunks Found: {len(chunks)}")
# #     print(f"🖼️ Total Images Found: {len(all_images)}")

# #     for chunk in tqdm(chunks, desc="Processing chunks"):
# #         chunk_id = chunk.id
# #         payload = chunk.payload

# #         header = payload.get("contexual_header", "")
# #         text = payload.get("chunk_text", "")
# #         page_range = payload.get("page_range", [])

# #         combined_text = f"{header} {text}".strip()
# #         text_emb = get_clip_text_embedding(combined_text)

# #         retrieved = query_images(text_emb, top_k=10)
# #         semantic_filtered = [img for img in retrieved if img["page_no"] in page_range]

# #         update_payload = {}

# #         # 🧠 STEP 1: Try semantic match (filtered by page)
# #         if semantic_filtered:
# #             best_match = semantic_filtered[0]
# #             update_payload.update({
# #                 "matched_image_name": best_match["image_name"],
# #                 "matched_image_path": best_match["image_path"],
# #                 "matched_image_score": best_match["score"],
# #                 "matched_image_page_no": best_match["page_no"],
# #                 "matched_by": "semantic"
# #             })

# #         # 🧠 STEP 2: If figure mention exists, assign all images from page_range ± 1
# #         if re.search(r"Figure\s+\d+", text) and page_range:
# #             nearby_images = get_extended_page_images(page_range, all_images, margin=1)
# #             update_payload["matched_image_candidates"] = nearby_images

# #             # Set fallback only if semantic match is missing
# #             if not semantic_filtered:
# #                 update_payload["matched_by_fallback"] = "heuristic"

# #         # Merge and upsert
# #         full_payload = {**payload, **update_payload}
# #         client.set_payload(collection_name=TEXT_COLLECTION, payload=full_payload, points=[chunk_id])

# #     print("✅ Completed assigning images to chunks!")

# # if __name__ == "__main__":
# #     assign_images_to_chunks()


import torch
from qdrant_client import QdrantClient
from transformers import CLIPProcessor, CLIPModel
from typing import List, Dict
from tqdm import tqdm

client = QdrantClient(url="http://3.101.65.253", port=5333)
TEXT_COLLECTION = "toshiba_pdf_1"
IMAGE_COLLECTION = "toshiba_images_1"

device = "cpu"
clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

def get_clip_text_embedding(text: str) -> List[float]:
    """Get 512-d normalized CLIP embedding for text input."""
    inputs = clip_processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(device)
    with torch.no_grad():
        outputs = clip_model.get_text_features(**inputs)
    normalized = outputs / outputs.norm(dim=-1, keepdim=True)
    return normalized.squeeze(0).cpu().tolist()

def query_images(text_embedding: List[float], top_k: int = 20):
    results = client.search(
        collection_name=IMAGE_COLLECTION,
        query_vector=text_embedding,
        limit=top_k,
        with_payload=True
    )
    return [
        {
            "image_name": r.payload.get("image_name"),
            "image_path": r.payload.get("image_path"),
            "page_no": r.payload.get("page_no"),
            "score": r.score
        } for r in results
    ]

def post_filter_by_page(chunk, retrieved_images, margin=1):
    """
    Filters retrieved images based on page proximity to the chunk's page_range.

    Args:
        chunk (dict): Chunk metadata with 'page_range'
        retrieved_images (list): List of image dicts with 'page_no'
        margin (int): Page tolerance, e.g., ±1

    Returns:
        List of filtered images
    """
    if not chunk.get("page_range"):
        return []

    pages = set()
    for page in chunk["page_range"]:
        pages.update([page + offset for offset in range(-margin, margin + 1)])

    filtered = [img for img in retrieved_images if img.get("page_no") in pages]
    return filtered

def get_all_chunks(limit=5000):
    return client.scroll(
        collection_name=TEXT_COLLECTION,
        with_payload=True,
        with_vectors=False,
        limit=limit
    )[0]

def assign_images_to_chunks():
    chunks = get_all_chunks()
    print(f"📦 Total Chunks Found: {len(chunks)}")

    for chunk in tqdm(chunks, desc="Processing chunks"):
        chunk_id = chunk.id
        payload = chunk.payload

        header = payload.get("contexual_header", "")
        text = payload.get("chunk_text", "")
        page_range = payload.get("page_range", [])

        combined_text = f"{header} {text}".strip()
        text_emb = get_clip_text_embedding(combined_text)

        retrieved = query_images(text_emb, top_k=30)
        filtered = post_filter_by_page(payload, retrieved)
        print("#####################filtered_images")
        print(filtered)

        update_payload = {}
        if filtered:
            update_payload["matched_image_candidates"] = filtered
            # Optional: pick top-1 as default if needed
            update_payload.update({
                "matched_image_name": filtered[0]["image_name"],
                "matched_image_path": filtered[0]["image_path"],
                "matched_image_score": filtered[0]["score"],
                "matched_image_page_no": filtered[0]["page_no"]
            })

        full_payload = {**payload, **update_payload}

        client.set_payload(
            collection_name=TEXT_COLLECTION,
            payload=full_payload,
            points=[chunk_id]
        )

    print("✅ Completed assigning images to chunks!")

if __name__ == "__main__":
    assign_images_to_chunks()
