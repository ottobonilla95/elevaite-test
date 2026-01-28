# import fitz  # PyMuPDF
# import camelot
# import os
# import re
# import json

# def extract_images_and_text(pdf_path, output_dir):
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
#             if len(text.strip()) > 20:  # skip small/irrelevant ones
#                 paragraphs.append({
#                     "para_id": f"{page_num+1}_{i+1}",
#                     "text": text.strip(),
#                     "coords": [x0, y0, x1, y1]
#                 })

#         # Extract and save images
#         # Extract and save images
#         images = []
#         for img_index, img in enumerate(image_blocks):
#             xref = img[0]
#             pix = fitz.Pixmap(doc, xref)
#             image_path = os.path.join(output_dir, f"page_{page_num+1}_img_{img_index+1}.png")

#             try:
#                 # Convert to RGB if the image is not already RGB (e.g., CMYK, grayscale, etc.)
#                 if pix.colorspace.n != 3:  # not RGB
#                     pix = fitz.Pixmap(fitz.csRGB, pix)

#                 pix.save(image_path)
#             except Exception as e:
#                 print(f"[Warning] Skipping image on page {page_num+1}, index {img_index+1} due to: {e}")
#                 continue

#             images.append({
#                 "image_id": f"img_{page_num+1}_{img_index+1}",
#                 "image_path": image_path,
#                 "caption": None,
#                 "matched_by": None
#             })


#         # Match captions (heuristic: "Figure" or "Fig.")
#         figure_pattern = re.compile(r"(Figure|Fig\.?)\s*\d+.*", re.IGNORECASE)
#         for para in paragraphs:
#             if figure_pattern.match(para["text"]):
#                 # Try matching with image on same page
#                 for img in images:
#                     if img["caption"] is None:
#                         img["caption"] = para["text"]
#                         img["matched_by"] = "heuristic"
#                         break

#         # Extract tables using Camelot
#         tables = []
#         try:
#             camelot_tables = camelot.read_pdf(pdf_path, pages=str(page_num+1), flavor='lattice')
#             for i, table in enumerate(camelot_tables):
#                 tables.append({
#                     "table_id": f"tbl_{page_num+1}_{i+1}",
#                     "table_html": table.df.to_html(index=False, header=False),
#                     "extracted_with": "camelot"
#                 })
#         except Exception as e:
#             print(f"Error extracting table on page {page_num+1}: {e}")

#         all_data.append({
#             "page_number": page_num + 1,
#             "text_paragraphs": paragraphs,
#             "images": images,
#             "tables": tables
#         })

#     return all_data

# # Run it on a PDF
# pdf_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/4820-2Lx5LxPlanningInstallationServiceGuide (2).pdf"  # change this to your PDF file
# output_dir = "extracted_multimodal_images"

# result = extract_images_and_text(pdf_path, output_dir)

# # Save as JSON
# with open("pdf_layers.json", "w") as f:
#     json.dump(result, f, indent=2)

# print("✅ PDF parsed and structured JSON saved as 'pdf_layers.json'")

# import fitz
# import os
# import re
# import json

# def extract_images_with_captions(pdf_path, output_dir):
#     os.makedirs(output_dir, exist_ok=True)
#     doc = fitz.open(pdf_path)
#     pdf_filename = os.path.basename(pdf_path)
#     all_images = []

#     for page_num in range(len(doc)):
#         page = doc.load_page(page_num)
#         text_blocks = page.get_text("blocks")  # includes bbox and text
#         image_blocks = page.get_images(full=True)

#         # Extract candidate caption paragraphs
#         captions = []
#         figure_pattern = re.compile(r"(Figure|Fig\.?)\s*\d+.*", re.IGNORECASE)
#         for (x0, y0, x1, y1, text, *_rest) in text_blocks:
#             if figure_pattern.match(text.strip()):
#                 captions.append({
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

#             # Heuristic: match with nearest caption below the image
#             matched_caption = None
#             for cap in captions:
#                 if cap["bbox"][1] >= bbox.y1:  # caption is below image
#                     matched_caption = cap["text"]
#                     break

#             all_images.append({
#                 "image_id": f"img_{page_num+1}_{img_index+1}",
#                 "img_path": image_path,
#                 "caption": matched_caption,
#                 "filename": pdf_filename,
#                 "page_no": page_num + 1,
#                 "bounding_box": [bbox.x0, bbox.y0, bbox.x1, bbox.y1]
#             })

#     return all_images

# # === Run It ===
# pdf_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/4820-2Lx5LxPlanningInstallationServiceGuide (2).pdf"  # Change to your actual PDF path
# output_dir = "extracted_images_omly"
# images_info = extract_images_with_captions(pdf_path, output_dir)

# # Save to JSON
# with open("extracted_images.json", "w") as f:
#     json.dump(images_info, f, indent=2)

# print("✅ Images extracted and saved to 'extracted_images.json'")


import fitz
import os
import re
import json


def extract_images_with_captions(pdf_path, output_dir, context_window=150):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    pdf_filename = os.path.basename(pdf_path)
    all_images = []

    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        text_blocks = page.get_text("blocks")
        image_blocks = page.get_images(full=True)

        all_text_blocks = []
        for x0, y0, x1, y1, text, *_rest in text_blocks:
            if len(text.strip()) > 15:
                all_text_blocks.append({"text": text.strip(), "bbox": [x0, y0, x1, y1]})

        captions = []
        figure_pattern = re.compile(r"(Figure|Fig\.?)\s*\d+.*", re.IGNORECASE)
        for block in all_text_blocks:
            if figure_pattern.match(block["text"]):
                captions.append(block)

        # Extract and save images
        for img_index, img in enumerate(image_blocks):
            xref = img[0]
            bbox = fitz.Rect(img[1], img[2], img[3], img[4])
            pix = fitz.Pixmap(doc, xref)
            image_path = os.path.join(
                output_dir, f"page_{page_num + 1}_img_{img_index + 1}.png"
            )

            try:
                if pix.colorspace.n != 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                pix.save(image_path)
            except Exception as e:
                print(
                    f"[Warning] Skipping image on page {page_num + 1}, index {img_index + 1} due to: {e}"
                )
                continue

            matched_caption = None
            caption_bbox = None
            for cap in captions:
                cap_y0 = cap["bbox"][1]
                if cap_y0 >= bbox.y1:
                    matched_caption = cap["text"]
                    caption_bbox = cap["bbox"]
                    break

            rich_caption = matched_caption or ""
            if matched_caption:
                cap_center_y = (caption_bbox[1] + caption_bbox[3]) / 2
                nearby_texts = []

                for block in all_text_blocks:
                    block_y_center = (block["bbox"][1] + block["bbox"][3]) / 2
                    vertical_distance = abs(block_y_center - cap_center_y)
                    if (
                        block["text"] != matched_caption
                        and vertical_distance <= context_window
                    ):
                        nearby_texts.append(block["text"])

                nearby_texts = sorted(nearby_texts, key=lambda t: t)
                rich_caption += " " + " ".join(nearby_texts)

            all_images.append(
                {
                    "image_id": f"img_{page_num + 1}_{img_index + 1}",
                    "img_path": image_path,
                    "caption": matched_caption,
                    "rich_caption": rich_caption.strip(),
                    "filename": pdf_filename,
                    "page_no": page_num + 1,
                    "bounding_box": [bbox.x0, bbox.y0, bbox.x1, bbox.y1],
                }
            )

    return all_images


pdf_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/4820-2Lx5LxPlanningInstallationServiceGuide (2).pdf"
output_dir = "extracted_images_only"
images_info = extract_images_with_captions(pdf_path, output_dir)

# Save to JSON
with open("extracted_images.json", "w") as f:
    json.dump(images_info, f, indent=2)

print(" Images extracted and saved to 'extracted_images.json'")
