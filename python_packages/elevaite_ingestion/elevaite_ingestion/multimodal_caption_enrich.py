# import fitz  # PyMuPDF
# import os
# import re
# import json

# def extract_images_with_rich_caption(pdf_path, output_dir, context_window=100):
#     os.makedirs(output_dir, exist_ok=True)
#     doc = fitz.open(pdf_path)
#     all_data = []

#     for page_num in range(len(doc)):
#         page = doc.load_page(page_num)
#         text_blocks = page.get_text("blocks")
#         image_blocks = page.get_images(full=True)

#         # Extract paragraphs
#         paragraphs = []
#         for i, (x0, y0, x1, y1, text, *_rest) in enumerate(text_blocks):
#             if len(text.strip()) > 20:
#                 paragraphs.append({
#                     "para_id": f"{page_num+1}_{i+1}",
#                     "text": text.strip(),
#                     "bbox": [x0, y0, x1, y1]
#                 })

#         # Extract and save images
#         images = []
#         for img_index, img in enumerate(image_blocks):
#             xref = img[0]
#             x0, y0, x1, y1 = img[1], img[2], img[3], img[4]
#             x0, x1 = min(x0, x1), max(x0, x1)
#             y0, y1 = min(y0, y1), max(y0, y1)
#             bbox = fitz.Rect(x0, y0, x1, y1)

#             try:
#                 pix = fitz.Pixmap(doc, xref)
#                 if pix.colorspace.n != 3:
#                     pix = fitz.Pixmap(fitz.csRGB, pix)
#                 image_path = os.path.join(output_dir, f"page_{page_num+1}_img_{img_index+1}.png")
#                 pix.save(image_path)
#             except Exception as e:
#                 print(f"[Warning] Skipping image on page {page_num+1}, index {img_index+1} due to: {e}")
#                 continue

#             images.append({
#                 "image_id": f"img_{page_num+1}_{img_index+1}",
#                 "image_path": image_path,
#                 "bbox": [x0, y0, x1, y1],
#                 "caption": None,
#                 "above_text": [],
#                 "below_text": [],
#                 "rich_caption": "",
#                 "matched_by": None,
#                 "page_no": page_num + 1
#             })

#         # Heuristic caption matching: "Figure X"
#         figure_pattern = re.compile(r"(Figure|Fig\.?)\s*\d+.*", re.IGNORECASE)
#         for para in paragraphs:
#             if figure_pattern.match(para["text"]):
#                 for img in images:
#                     if img["caption"] is None:
#                         img["caption"] = para["text"]
#                         img["matched_by"] = "heuristic"
#                         break

#         # Add above/below text
#         for img in images:
#             x0, y0, x1, y1 = img["bbox"]
#             caption_bbox = None

#             # Try to locate the caption's coordinates
#             for para in paragraphs:
#                 if para["text"] == img["caption"]:
#                     caption_bbox = para["bbox"]
#                     break

#             # -------- Above Text (from image box) --------
#             for para in paragraphs:
#                 if para["text"] == img["caption"]:
#                     continue
#                 px0, py0, px1, py1 = para["bbox"]
#                 if px1 < x0 or px0 > x1:
#                     continue  # skip if horizontally misaligned
#                 if py1 <= y0 and (y0 - py1) <= context_window:
#                     img["above_text"].append(para["text"])

#             # -------- Below Text (prefer from caption box) --------
#             base_y = caption_bbox[3] if caption_bbox else y1

#             for para in paragraphs:
#                 if para["text"] == img["caption"]:
#                     continue
#                 px0, py0, px1, py1 = para["bbox"]
#                 if px1 < x0 or px0 > x1:
#                     continue
#                 if py0 >= base_y and (py0 - base_y) <= context_window:
#                     img["below_text"].append(para["text"])

#             # Combine all into rich_caption
#             rich_caption = (img["caption"] or "") + " " + " ".join(img["above_text"] + img["below_text"])
#             img["rich_caption"] = rich_caption.strip()

#         all_data.extend(images)

#     return all_data
    

# pdf_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/4820-2Lx5LxPlanningInstallationServiceGuide (2).pdf"
# output_dir = "extracted_images_with_context_2"

# results = extract_images_with_rich_caption(pdf_path, output_dir)

# with open("enriched_image_context_2.json", "w") as f:
#     json.dump(results, f, indent=2)

# print("✅ Saved image captions and context to 'enriched_image_context_2.json'")




####################
# import fitz
# import os
# import re
# import json
# # from sklearn.metrics.pairwise import cosine_similarity
# # from sentence_transformers import SentenceTransformer

# # # Load a pre-trained sentence transformer model for embeddings
# # model = SentenceTransformer('all-MiniLM-L6-v2')

# def extract_images_with_captions(pdf_path, output_dir, context_window=150):
#     os.makedirs(output_dir, exist_ok=True)
#     doc = fitz.open(pdf_path)
#     pdf_filename = os.path.basename(pdf_path)
#     all_images = []

#     for page_num in range(len(doc)):
#         page = doc.load_page(page_num)
#         text_blocks = page.get_text("blocks")  
#         image_blocks = page.get_images(full=True)

#         all_text_blocks = []
#         for (x0, y0, x1, y1, text, *_rest) in text_blocks:
#             if len(text.strip()) > 15:
#                 all_text_blocks.append({
#                     "text": text.strip(),
#                     "bbox": [x0, y0, x1, y1]
#                 })

#         # Extract and save images
#         for img_index, img in enumerate(image_blocks):
#             xref = img[0]
#             bbox = fitz.Rect(img[1], img[2], img[3], img[4])
#             pix = fitz.Pixmap(doc, xref)
#             image_path = os.path.join(output_dir, f"page_{page_num+1}_img_{img_index+1}.png")

#             try:
#                 if pix.colorspace.n != 3:
#                     pix = fitz.Pixmap(fitz.csRGB, pix)
#                 pix.save(image_path)
#             except Exception as e:
#                 print(f"[Warning] Skipping image on page {page_num+1}, index {img_index+1} due to: {e}")
#                 continue

#             # Extract surrounding text
#             surrounding_texts = []
#             for block in all_text_blocks:
#                 block_y_center = (block["bbox"][1] + block["bbox"][3]) / 2
#                 vertical_distance = abs(block_y_center - bbox.y0)
#                 if vertical_distance <= context_window:
#                     surrounding_texts.append(block["text"])

#             # Enrich caption with surrounding text
#             enriched_caption = " ".join(surrounding_texts)

#             all_images.append({
#                 "image_id": f"img_{page_num+1}_{img_index+1}",
#                 "img_path": image_path,
#                 "caption": enriched_caption.strip(),
#                 "filename": pdf_filename,
#                 "page_no": page_num + 1,
#                 "bounding_box": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
#                 "embedding": None  # Placeholder for embedding
#             })

#     return all_images


# def assign_images_to_chunks(images_info, chunks, threshold=0.7):
#     """
#     Assign images to chunks based on cosine similarity between enriched captions and chunk texts.
#     """
#     assigned_images = []

#     # Generate embeddings for chunks
#     chunk_texts = [chunk["text"] for chunk in chunks]
#     chunk_embeddings = model.encode(chunk_texts)

#     # Generate embeddings for enriched captions and assign images
#     for image in images_info:
#         enriched_caption = image["caption"]
#         if not enriched_caption:
#             continue

#         # Generate embedding for the enriched caption
#         caption_embedding = model.encode([enriched_caption])[0]

#         # Compute cosine similarity with all chunks
#         similarities = cosine_similarity([caption_embedding], chunk_embeddings)[0]
#         best_match_idx = similarities.argmax()
#         best_match_score = similarities[best_match_idx]

#         if best_match_score >= threshold:
#             assigned_chunk = chunks[best_match_idx]
#             assigned_images.append({
#                 "image_id": image["image_id"],
#                 "img_path": image["img_path"],
#                 "caption": enriched_caption,
#                 "assigned_chunk": assigned_chunk["id"],
#                 "similarity_score": best_match_score
#             })

#     return assigned_images


# # Example usage
# pdf_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/4820-2Lx5LxPlanningInstallationServiceGuide (2).pdf"
# output_dir = "extracted_images_qwen"

# # Extract images and enriched captions
# images_info = extract_images_with_captions(pdf_path, output_dir)

# # Save the extracted images and enriched captions to a JSON file
# with open("extracted_text_img.json", "w") as f:
#     json.dump(images_info, f, indent=2)

# print("Images extracted and enriched captions saved to 'extracted_text_img.json'.")

####################################################################
import fitz
import os
import re
import json

def extract_images_with_captions(pdf_path, output_dir, context_window=150, min_image_size=(100, 100)):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    pdf_filename = os.path.basename(pdf_path)
    all_images = []

   
    undesired_keywords = ["logo", "header", "footer", "confidential", "company", "name"]
    undesired_pattern = re.compile("|".join(undesired_keywords), re.IGNORECASE)

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_blocks = page.get_text("blocks")  
        image_blocks = page.get_images(full=True)

        all_text_blocks = []
        for (x0, y0, x1, y1, text, *_rest) in text_blocks:
            if len(text.strip()) > 15:
                all_text_blocks.append({
                    "text": text.strip(),
                    "bbox": [x0, y0, x1, y1]
                })

        for img_index, img in enumerate(image_blocks):
            xref = img[0]
            bbox = fitz.Rect(img[1], img[2], img[3], img[4])
            pix = fitz.Pixmap(doc, xref)

            # Filter based on image size
            if pix.width < min_image_size[0] or pix.height < min_image_size[1]:
                print(f"[Filtered] Skipping small image on page {page_num+1}, index {img_index+1}")
                continue

           
            page_height = page.rect.height
            if bbox.y0 < page_height * 0.1 or bbox.y1 > page_height * 0.9:
                print(f"[Filtered] Skipping header/footer image on page {page_num+1}, index {img_index+1}")
                continue

           
            image_path = os.path.join(output_dir, f"page_{page_num+1}_img_{img_index+1}.png")
            try:
                if pix.colorspace.n != 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                pix.save(image_path)
            except Exception as e:
                print(f"[Warning] Skipping image on page {page_num+1}, index {img_index+1} due to: {e}")
                continue

           
            surrounding_texts = []
            for block in all_text_blocks:
                block_y_center = (block["bbox"][1] + block["bbox"][3]) / 2
                vertical_distance = abs(block_y_center - bbox.y0)
                if vertical_distance <= context_window:
                    surrounding_texts.append(block["text"])

            # Enrich caption with surrounding text
            enriched_caption = " ".join(surrounding_texts)

            # Filter based on caption content
            if undesired_pattern.search(enriched_caption):
                print(f"[Filtered] Skipping undesired image on page {page_num+1}, index {img_index+1} (Caption: {enriched_caption})")
                continue

            all_images.append({
                "image_id": f"img_{page_num+1}_{img_index+1}",
                "img_path": image_path,
                "caption": enriched_caption.strip(),
                "filename": pdf_filename,
                "page_no": page_num + 1,
                "bounding_box": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                "embedding": None
            })

    return all_images



pdf_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/4820-2Lx5LxPlanningInstallationServiceGuide (2).pdf"
output_dir = "extracted_images_only_a"

images_info = extract_images_with_captions(pdf_path, output_dir)

with open("extracted_text_img_a.json", "w") as f:
    json.dump(images_info, f, indent=2)

print("Images extracted and enriched captions: 'extracted_text_img.json'.")