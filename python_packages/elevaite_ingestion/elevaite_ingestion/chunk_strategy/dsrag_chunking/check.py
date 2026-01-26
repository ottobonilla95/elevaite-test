# import os
# import pdfplumber
# from PIL import Image
# import pytesseract
# import camelot
# import pandas as pd

# class DocumentLine:
#     def __init__(self, text, page_no, line_start_no, line_end_no, source="text", cropped_table_path=None, cropped_image_path=None):
#         self.text = text.strip()  # Remove leading/trailing whitespace
#         self.page_no = page_no
#         self.line_start_no = line_start_no
#         self.line_end_no = line_end_no
#         self.source = source  # "text", "table", or "image"
#         self.cropped_table_path = cropped_table_path
#         self.cropped_image_path = cropped_image_path

#     def __repr__(self):
#         return f"Page {self.page_no}, Line {self.line_start_no}-{self.line_end_no} ({self.source}): {self.text}"

# def sanitize_bbox(bbox, page_bbox):
#     """
#     Ensure the bounding box is within the page's dimensions.
#     """
#     x0, top, x1, bottom = bbox
#     page_x0, page_top, page_x1, page_bottom = page_bbox

#     # Clamp coordinates to the page's bounding box
#     x0 = max(page_x0, min(x0, page_x1))
#     top = max(page_top, min(top, page_bottom))
#     x1 = max(page_x0, min(x1, page_x1))
#     bottom = max(page_top, min(bottom, page_bottom))

#     return (x0, top, x1, bottom)

# def extract_text_from_image(image_path):
#     """
#     Use OCR to extract text from an image.
#     """
#     return pytesseract.image_to_string(Image.open(image_path))

# def parse_pdf_to_lines(pdf_path, output_dir="output/", max_line_length=100):
#     """
#     Parse a single PDF file into a list of DocumentLine objects.
#     Handles text, tables, and images.
#     Saves cropped tables and images to the specified output directory.
#     """
#     document_lines = []
#     os.makedirs(output_dir, exist_ok=True)  # Create output directory if it doesn't exist

#     with pdfplumber.open(pdf_path) as pdf:
#         for page_no, page in enumerate(pdf.pages, start=1):
#             page_bbox = page.bbox  # Get the page's bounding box

#             # Extract text
#             text = page.extract_text()
#             if text:
#                 lines = text.split('\n')
#                 for line_no, line in enumerate(lines, start=1):
#                     if line.strip():  # Ignore empty lines
#                         doc_line = DocumentLine(
#                             text=line[:max_line_length],  # Truncate long lines
#                             page_no=page_no,
#                             line_start_no=line_no,
#                             line_end_no=line_no,
#                             source="text"
#                         )
#                         document_lines.append(doc_line)

#             # Extract tables
#             tables = page.find_tables()
#             for table_idx, table in enumerate(tables):
#                 # Sanitize table bounding box
#                 sanitized_bbox = sanitize_bbox(table.bbox, page_bbox)
#                 try:
#                     # Save cropped table as an image
#                     cropped_table_path = os.path.join(output_dir, f"page_{page_no}_table_{table_idx}.png")
#                     table_image = page.within_bbox(sanitized_bbox).to_image().original
#                     table_image.save(cropped_table_path)

#                     # Convert table to text
#                     table_data = table.extract()
#                     table_df = pd.DataFrame(table_data)
#                     table_text = table_df.to_string(index=False, header=False)

#                     doc_line = DocumentLine(
#                         text=table_text,
#                         page_no=page_no,
#                         line_start_no=len(document_lines) + 1,
#                         line_end_no=len(document_lines) + len(table_data),
#                         source="table",
#                         cropped_table_path=cropped_table_path
#                     )
#                     document_lines.append(doc_line)
#                 except Exception as e:
#                     print(f"Error processing table on page {page_no}: {e}")

#             # Extract images
#             images = page.images
#             for img_idx, img in enumerate(images):
#                 # Sanitize image bounding box
#                 sanitized_bbox = sanitize_bbox((img['x0'], img['top'], img['x1'], img['bottom']), page_bbox)
#                 try:
#                     # Save cropped image
#                     cropped_image_path = os.path.join(output_dir, f"page_{page_no}_image_{img_idx}.png")
#                     cropped_image = page.within_bbox(sanitized_bbox).to_image().original
#                     cropped_image.save(cropped_image_path)

#                     # Extract text using OCR
#                     ocr_text = extract_text_from_image(cropped_image_path)

#                     doc_line = DocumentLine(
#                         text=ocr_text,
#                         page_no=page_no,
#                         line_start_no=len(document_lines) + 1,
#                         line_end_no=len(document_lines) + 1,
#                         source="image",
#                         cropped_image_path=cropped_image_path
#                     )
#                     document_lines.append(doc_line)
#                 except Exception as e:
#                     print(f"Error processing image on page {page_no}: {e}")

#     return document_lines

# def parse_directory_to_lines(directory_path, output_dir="output/", max_line_length=100):
#     """
#     Parse all PDFs in a directory into a list of DocumentLine objects.
#     """
#     all_document_lines = []
#     for filename in os.listdir(directory_path):
#         if filename.endswith(".pdf"):
#             pdf_path = os.path.join(directory_path, filename)
#             print(f"Parsing {filename}...")
#             document_lines = parse_pdf_to_lines(pdf_path, output_dir, max_line_length)
#             all_document_lines.extend(document_lines)
#     return all_document_lines

# if __name__ == "__main__":
#     directory_path = "check_dir"
#     output_dir = "output/"
#     # Parse all PDFs into DocumentLine objects
#     document_lines = parse_directory_to_lines(directory_path, output_dir)
#     # Print the first 5 lines for verification
#     for line in document_lines[:50]:
#         print(line)


from unstructured.partition.pdf import partition_pdf
import os


def parse_pdf_with_unstructured(pdf_path, output_dir="output/"):
    """
    Parse a PDF using the `unstructured` library.
    """
    os.makedirs(output_dir, exist_ok=True)
    elements = partition_pdf(pdf_path, strategy="auto")  # Use "hi_res" for scanned PDFs
    parsed_data = []

    for idx, element in enumerate(elements):
        element_type = element.__class__.__name__
        text = element.text.strip() if hasattr(element, "text") else ""
        metadata = element.metadata.to_dict() if hasattr(element, "metadata") else {}

        # Save cropped images if available
        if element_type == "Image":
            image_path = os.path.join(output_dir, f"image_{idx}.png")
            with open(image_path, "wb") as img_file:
                img_file.write(element.image_bytes)
            metadata["cropped_image_path"] = image_path

        parsed_data.append({"type": element_type, "text": text, "metadata": metadata})

    return parsed_data


if __name__ == "__main__":
    pdf_path = "pdf_dir/OXO_Connect_6.0_sd_SystemServices_8AL91213USAM_1_en.pdf"
    output_dir = "output/"
    parsed_data = parse_pdf_with_unstructured(pdf_path, output_dir)

    for item in parsed_data[:20]:
        print(item)
