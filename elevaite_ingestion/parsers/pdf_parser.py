# import sys
# import os

# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# # print(base_dir)
# sys.path.append(base_dir)

# from tools.standard_tools.markitdown import MarkitdownTool
# from tools.standard_tools.docling import DoclingTool


# class PdfParser:
#     def __init__(self, tool="markitdown"):
#         if tool == "markitdown":
#             self.tool = MarkitdownTool()
#         elif tool == "docling":
#             self.tool = DoclingTool()
#         else:
#             raise ValueError(f"Unsupported tool: {tool}")

#     def parse(self, file_path):
#         try:
#             result = self.tool.process_file(file_path)
#             return {"content": result}
#         except Exception as e:
#             raise Exception(f"Failed to parse Pdf file: {file_path}. Error: {e}")

# # if __name__ == "__main__":
# #     file_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/input_data/OXO_Connect_6.0_sd_SystemServices_8AL91213USAM_1_en.pdf"

# #     try:
# #         parser = PdfParser(tool="markitdown")
# #         parsed_data = parser.parse(file_path)
# #         print("Parsed Content (Markitdown):", parsed_data)
# #         # parser = PdfParser(tool="docling")
# #         # parsed_data = parser.parse(file_path)
# #         # print("Parsed Content (Docling):", parsed_data)
# #     except Exception as e:
# #         print(f"Error: {e}")
############################################ working ##############################################
# import sys
# import os
# import fitz  # PyMuPDF for PDF text extraction
# import tempfile  # For temporary file storage

# # Add base directory to the system path
# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(base_dir)

# from tools.standard_tools.markitdown import MarkitdownTool
# from tools.standard_tools.docling import DoclingTool

# class PdfParser:
#     def __init__(self, tool="markitdown"):
#         if tool == "markitdown":
#             self.tool = MarkitdownTool()
#         elif tool == "docling":
#             self.tool = DoclingTool()
#         else:
#             raise ValueError(f"Unsupported tool: {tool}")

#     def parse(self, file_path):
#         """
#         Parses a PDF file and extracts content along with page numbers.

#         Args:
#             file_path (str): Path to the PDF file.

#         Returns:
#             dict: Extracted content with page numbers.
#         """
#         try:
#             doc = fitz.open(file_path)
#             extracted_content = []
#             page_numbers = []

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()  # Extract page text
                
#                 if text:  # Only process non-empty pages
#                     with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as temp_file:
#                         temp_file.write(text.encode("utf-8"))
#                         temp_file_path = temp_file.name
                    
#                     # Process file using MarkitdownTool
#                     processed_text = self.tool.process_file(temp_file_path)

#                     # Cleanup temp file
#                     os.remove(temp_file_path)

#                     extracted_content.append(processed_text)
#                     page_numbers.append(page_num + 1)  # Store page number (1-based index)

#             if not extracted_content:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             return {
#                 "content": extracted_content,  # List of extracted page content
#                 "page_numbers": page_numbers,  # List of page numbers
#                 "file_path": file_path  # Store file path metadata
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")

# # ✅ **Usage Example**
# if __name__ == "__main__":
#     file_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/kb_arlo.pdf"
#     parser = PdfParser(tool="markitdown")
#     parsed_data = parser.parse(file_path)
    
#     # Print a preview of extracted content
#     for i, content in enumerate(parsed_data["content"][:3]): 
#         print(f"Page {parsed_data['page_numbers'][i]}: {content[:200]}...") 


######################### with Line Document
# import sys
# import os
# import fitz

# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(base_dir)

# from tools.standard_tools.markitdown import MarkitdownTool
# from tools.standard_tools.docling import DoclingTool

# class LineDocument:
#     """Represents a single line of text in a PDF along with metadata."""
#     def __init__(self, line_text, page_no, line_no):
#         self.line_text = line_text.strip()
#         self.page_no = page_no
#         self.line_no = line_no

#     def to_dict(self):
#         """Convert to dictionary format for JSON serialization."""
#         return {"line_text": self.line_text, "page_no": self.page_no, "line_no": self.line_no}

# class PdfParser:
#     def __init__(self, tool="markitdown"):
#         if tool == "markitdown":
#             self.tool = MarkitdownTool()
#         elif tool == "docling":
#             self.tool = DoclingTool()
#         else:
#             raise ValueError(f"Unsupported tool: {tool}")

#     def parse(self, file_path):
#         """
#         Parses a PDF file and extracts content at the line level with metadata.

#         Args:
#             file_path (str): Path to the PDF file.

#         Returns:
#             dict: Extracted content with line-level metadata.
#         """
#         try:
#             doc = fitz.open(file_path)
#             extracted_lines = []
#             file_path_metadata = file_path

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()

#                 if text: 
#                     lines = text.split("\n") 
#                     for line_no, line_text in enumerate(lines, start=1):
#                         if line_text.strip():  # Ignore empty lines
#                             extracted_lines.append(LineDocument(line_text, page_num + 1, line_no))

#             if not extracted_lines:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             return {
#                 "lines": [line.to_dict() for line in extracted_lines], 
#                 "file_path": file_path_metadata
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")

# if __name__ == "__main__":
#     file_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/kb_arlo.pdf"
#     parser = PdfParser(tool="markitdown")
#     parsed_data = parser.parse(file_path)
    
#     # Print a preview of extracted content
#     for line in parsed_data["lines"][:10]:  # Show first 10 lines for testing
#         print(line)


################### with SentenceDocument ######### working monday
# import sys
# import os
# import fitz
# import re
# import pysbd
# # import nltk
# # nltk.download('punkt')
# # from nltk.tokenize import sent_tokenize

# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(base_dir)

# # from tools.standard_tools.markitdown import MarkitdownTool
# # from tools.standard_tools.docling import DoclingTool

# class SentenceDocument:
#     """Represents a single sentence in a PDF along with metadata."""
#     def __init__(self, sentence_text, page_no, sentence_no, filename):
#         self.sentence_text = sentence_text.strip()
#         self.page_no = page_no
#         self.sentence_no = sentence_no
#         self.filename = filename

#     def to_dict(self):
#         """Convert to dictionary format for JSON serialization."""
#         return {
#             "sentence_text": self.sentence_text,
#             "page_no": self.page_no,
#             "sentence_no": self.sentence_no,
#             "filename": self.filename
#         }

# class PdfParser:
#     """Parses a PDF file and extracts sentences with metadata."""
#     def __init__(self):
#         self.segmenter = pysbd.Segmenter(language="en", clean=True)
#     # def __init__(self, tool="markitdown"):
#     #     if tool == "markitdown":
#     #         self.tool = MarkitdownTool()
#     #     elif tool == "docling":
#     #         self.tool = DoclingTool()
#     #     else:
#     #         raise ValueError(f"Unsupported tool: {tool}")
#     def clean_text(self, text):
#         """Cleans extracted text by removing unwanted characters and artifacts."""
#         text = re.sub(r'\u202c|\u202d', '', text) 
#         text = re.sub(r'\s+', ' ', text).strip()
#         text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)  
#         text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)

#         return text

#     def split_sentences(self, text):
#         """
#         Uses `pySBD` for more robust sentence segmentation.
#         """
#         text = self.clean_text(text)
#         return self.segmenter.segment(text)

#     def parse(self, file_path):
#         """
#         Parses a PDF file and extracts sentences with metadata.

#         Args:
#             file_path (str): Path to the PDF file.

#         Returns:
#             dict: Extracted content with sentence-level metadata.
#         """
#         try:
#             doc = fitz.open(file_path)
#             extracted_sentences = []
#             filename = os.path.basename(file_path) 

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()

#                 if text:
#                     sentences = self.split_sentences(text)
#                     for sentence_no, sentence_text in enumerate(sentences, start=1):
#                         if sentence_text.strip():
#                             extracted_sentences.append(SentenceDocument(sentence_text, page_num + 1, sentence_no, filename))

#             if not extracted_sentences:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             return {
#                 "sentences": [sentence.to_dict() for sentence in extracted_sentences],
#                 "file_path": file_path,
#                 "filename": filename
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")


# if __name__ == "__main__":
#     file_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/kb_arlo.pdf"
#     parser = PdfParser()
#     parsed_data = parser.parse(file_path)
#     # print(parsed_data)

#     for sentence in parsed_data["sentences"][:50]:
#         print(sentence)

############################### working monday ########################

# import sys
# import os
# import fitz  # PyMuPDF
# import re
# import pysbd

# class SentenceDocument:
#     """Represents a single paragraph extracted from a PDF along with metadata."""
#     def __init__(self, paragraph_text, page_no, paragraph_no, filename):
#         self.paragraph_text = paragraph_text.strip()
#         self.page_no = page_no
#         self.paragraph_no = paragraph_no
#         self.filename = filename

#     def to_dict(self):
#         """Convert to dictionary format for JSON serialization."""
#         return {
#             "paragraph_text": self.paragraph_text,
#             "page_no": self.page_no,
#             "paragraph_no": self.paragraph_no,
#             "filename": self.filename
#         }

# class PdfParser:
#     """Parses a PDF file and extracts paragraphs with metadata."""
    
#     def __init__(self):
#         self.segmenter = pysbd.Segmenter(language="en", clean=True)

#     def clean_text(self, text):
#         """Cleans extracted text by removing unwanted characters and artifacts."""
#         text = re.sub(r'\u202c|\u202d', '', text)  # Remove control characters
#         text = re.sub(r'\s+', ' ', text).strip()
#         text = re.sub(r'(?<=[a-z])(?=[A-Z])', ' ', text)
#         text = re.sub(r'(\d)([a-zA-Z])', r'\1 \2', text)
#         return text

#     def split_sentences(self, text):
#         """Uses `pySBD` for better sentence segmentation."""
#         text = self.clean_text(text)
#         return self.segmenter.segment(text)

#     def group_sentences_into_paragraphs(self, sentences, page_no, filename):
#         """Groups sentences into paragraphs based on structure & topic continuity."""
#         grouped_paragraphs = []
#         buffer = []

#         for sentence_no, sentence_text in enumerate(sentences, start=1):
#             if not sentence_text.strip():
#                 continue  # Skip empty sentences
            
#             if len(buffer) > 0 and sentence_text[0].isupper():
#                 grouped_paragraphs.append(" ".join(buffer))  # Store previous paragraph
#                 buffer = []  # Reset buffer for new paragraph

#             buffer.append(sentence_text)

#         if buffer:
#             grouped_paragraphs.append(" ".join(buffer))  # Store the last paragraph

#         return [SentenceDocument(paragraph, page_no, idx + 1, filename).to_dict() 
#                 for idx, paragraph in enumerate(grouped_paragraphs)]

#     def parse(self, file_path):
#         """
#         Parses a PDF file and extracts paragraphs with metadata.

#         Args:
#             file_path (str): Path to the PDF file.

#         Returns:
#             dict: Extracted content with structured paragraphs and metadata.
#         """
#         try:
#             doc = fitz.open(file_path)
#             extracted_paragraphs = []
#             filename = os.path.basename(file_path)

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()

#                 if text:
#                     sentences = self.split_sentences(text)
#                     paragraphs = self.group_sentences_into_paragraphs(sentences, page_num + 1, filename)
#                     extracted_paragraphs.extend(paragraphs)

#             if not extracted_paragraphs:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             return {
#                 "paragraphs": extracted_paragraphs,
#                 "file_path": file_path,
#                 "filename": filename
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")

# if __name__ == "__main__":
#     file_path = "/Users/dheeraj/Desktop/elevaite/hp_manual.pdf"  # Update with actual path
#     parser = PdfParser()
#     parsed_data = parser.parse(file_path)

#     for paragraph in parsed_data["paragraphs"][:10]:  # Print first 10 paragraphs
#         print(paragraph)



######################### finla sentiecne document










# import sys
# import os
# import fitz
# import spacy

# base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# sys.path.append(base_dir)

# from tools.standard_tools.markitdown import MarkitdownTool
# from tools.standard_tools.docling import DoclingTool

# nlp = spacy.load("en_core_web_sm")

# class SentenceDocument:
#     """Represents a single sentence in a PDF along with metadata."""
#     def __init__(self, sentence_text, page_no, sentence_no):
#         self.sentence_text = sentence_text.strip()
#         self.page_no = page_no
#         self.sentence_no = sentence_no

#     def to_dict(self):
#         """Convert to dictionary format for JSON serialization."""
#         return {
#             "sentence_text": self.sentence_text,
#             "page_no": self.page_no,
#             "sentence_no": self.sentence_no
#         }

# class PdfParser:
#     def __init__(self, tool="markitdown"):
#         if tool == "markitdown":
#             self.tool = MarkitdownTool()
#         elif tool == "docling":
#             self.tool = DoclingTool()
#         else:
#             raise ValueError(f"Unsupported tool: {tool}")

#     def parse(self, file_path):
#         """
#         Parses a PDF file and extracts sentences with metadata using SpaCy.

#         Args:
#             file_path (str): Path to the PDF file.

#         Returns:
#             dict: Extracted content with sentence-level metadata.
#         """
#         try:
#             doc = fitz.open(file_path)
#             extracted_sentences = []

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()

#                 if text:
#                     spacy_doc = nlp(text)
#                     sentences = [sent.text.strip() for sent in spacy_doc.sents]
#                     for sentence_no, sentence_text in enumerate(sentences, start=1):
#                         if sentence_text:
#                             extracted_sentences.append(SentenceDocument(sentence_text, page_num + 1, sentence_no))

#             if not extracted_sentences:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             return {
#                 "sentences": [sentence.to_dict() for sentence in extracted_sentences],
#                 "file_path": file_path
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")


# if __name__ == "__main__":
#     file_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/kb_arlo.pdf"
#     parser = PdfParser(tool="markitdown")
#     parsed_data = parser.parse(file_path)

#     for sentence in parsed_data["sentences"][:15]:
#         print(sentence)



# import sys
# import os
# import fitz
# import re
# import pysbd

# class ParagraphDocument:
#     """Represents a paragraph in a PDF with metadata."""
#     def __init__(self, paragraph_text, page_no, paragraph_no, filename):
#         self.paragraph_text = paragraph_text.strip()
#         self.page_no = page_no
#         self.paragraph_no = paragraph_no
#         self.filename = filename  # ✅ Store the original filename

#     def to_dict(self):
#         """Convert to dictionary format for JSON serialization."""
#         return {
#             "paragraph_text": self.paragraph_text,
#             "page_no": self.page_no,
#             "paragraph_no": self.paragraph_no,
#             "filename": self.filename  # ✅ Ensure correct filename
#         }

# class PdfParser:
#     """Parses a PDF and extracts paragraphs while keeping original filenames."""
#     def __init__(self):
#         self.segmenter = pysbd.Segmenter(language="en", clean=True)

#     def clean_text(self, text):
#         """Cleans extracted text by removing unwanted artifacts."""
#         text = re.sub(r'\u202c|\u202d', '', text)
#         text = re.sub(r'\s+', ' ', text).strip()
#         return text

#     def split_into_paragraphs(self, text):
#         """Splits text into paragraphs based on double line breaks."""
#         text = self.clean_text(text)
#         paragraphs = re.split(r"\n\s*\n+", text)  # ✅ Split at double newlines
#         return [p.strip() for p in paragraphs if p.strip()]  

#     def parse(self, file_path, original_filename):
#         """
#         Parses a PDF file and extracts paragraphs with metadata.

#         Args:
#             file_path (str): Path to the PDF file.
#             original_filename (str): The actual filename to store.

#         Returns:
#             dict: Extracted content with paragraph metadata.
#         """
#         try:
#             doc = fitz.open(file_path)
#             extracted_paragraphs = []

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()

#                 if text:
#                     paragraphs = self.split_into_paragraphs(text)
#                     for paragraph_no, paragraph_text in enumerate(paragraphs, start=1):
#                         extracted_paragraphs.append(
#                             ParagraphDocument(paragraph_text, page_num + 1, paragraph_no, original_filename)
#                         )

#             if not extracted_paragraphs:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             return {
#                 "paragraphs": [paragraph.to_dict() for paragraph in extracted_paragraphs],
#                 "file_path": file_path,
#                 "filename": original_filename  # ✅ Ensure original filename is stored
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")





############## spacy 
# import os
# import fitz
# import spacy
# import re
# from typing import List, Dict

# class ParagraphDocument:
#     """Represents a paragraph in a PDF with metadata."""
#     def __init__(self, paragraph_text, page_no, paragraph_no, filename):
#         self.paragraph_text = paragraph_text.strip()
#         self.page_no = page_no
#         self.paragraph_no = paragraph_no
#         self.filename = filename  # ✅ Store the original filename

#     def to_dict(self):
#         """Convert to dictionary format for JSON serialization."""
#         return {
#             "paragraph_text": self.paragraph_text,
#             "page_no": self.page_no,
#             "paragraph_no": self.paragraph_no,
#             "filename": self.filename  # ✅ Ensure correct filename
#         }

# # class PdfParser:
# #     """Parses a PDF and extracts paragraphs while keeping original filenames."""
# #     def __init__(self):
# #         self.nlp = spacy.load("en_core_web_sm")  # ✅ Load Spacy NLP Model

# #     def clean_text(self, text: str) -> str:
# #         """Cleans extracted text by removing unwanted artifacts."""
# #         text = re.sub(r'\u202c|\u202d', '', text)
# #         text = re.sub(r'\s+', ' ', text).strip()
# #         return text

# #     def split_into_paragraphs(self, text: str) -> List[str]:
# #         """
# #         Uses Spacy NLP to split text into meaningful paragraphs.
# #         - Ensures **context is preserved**.
# #         - Prevents **incorrect short breaks**.
# #         - Merges fragments to maintain **logical paragraph flow**.
# #         """
# #         text = self.clean_text(text)
# #         doc = self.nlp(text)

# #         paragraphs = []
# #         current_paragraph = []

# #         for sent in doc.sents:
# #             current_paragraph.append(sent.text.strip())

# #             # ✅ **Only split at full stops, question marks, or exclamations**
# #             if sent.text.endswith((".", "!", "?")):
# #                 paragraphs.append(" ".join(current_paragraph))
# #                 current_paragraph = []

# #         # ✅ **Merge any remaining text as a final paragraph**
# #         if current_paragraph:
# #             paragraphs.append(" ".join(current_paragraph))

# #         return [p for p in paragraphs if p.strip()]  # ✅ Remove empty paragraphs
# import re
# import spacy

# class PdfParser:
#     def __init__(self):
#         self.nlp = spacy.load("en_core_web_sm")

#     def clean_text(self, text: str) -> str:
#         """Cleans text to remove unwanted characters & normalize spaces."""
#         text = re.sub(r'\u202c|\u202d', '', text)  # Remove Unicode markers
#         text = re.sub(r'\s+', ' ', text).strip()  # Normalize extra spaces
#         return text

#     def split_into_paragraphs(self, text: str) -> list:
#         """
#         Splits text into paragraphs while ensuring **numbered sections** stay connected.
#         - Uses SpaCy for **context-aware splitting**.
#         - Prevents **isolated numbers** from becoming separate paragraphs.
#         """
#         text = self.clean_text(text)
#         doc = self.nlp(text)

#         paragraphs = []
#         current_paragraph = []

#         for sent in doc.sents:
#             sentence_text = sent.text.strip()

#             # ✅ **Merge section numbers (like "3.") with next line**
#             if re.fullmatch(r"\d+\.", sentence_text):
#                 if current_paragraph:
#                     current_paragraph[-1] += " " + sentence_text  # Merge with previous paragraph
#                 else:
#                     current_paragraph.append(sentence_text)  # Start new paragraph if empty
#                 continue  

#             current_paragraph.append(sentence_text)

#             # ✅ **Only split at full stops, question marks, or exclamations**
#             if sentence_text.endswith((".", "!", "?")):
#                 paragraphs.append(" ".join(current_paragraph))
#                 current_paragraph = []

#         # ✅ **Merge any remaining text as a final paragraph**
#         if current_paragraph:
#             paragraphs.append(" ".join(current_paragraph))

#         return [p for p in paragraphs if p.strip()]  # ✅ Remove empty paragraphs


#     def parse(self, file_path: str, original_filename: str) -> Dict:
#         """
#         Parses a PDF file and extracts paragraphs with metadata.

#         Args:
#             file_path (str): Path to the PDF file.
#             original_filename (str): The actual filename to store.

#         Returns:
#             dict: Extracted content with paragraph metadata.
#         """
#         try:
#             doc = fitz.open(file_path)
#             extracted_paragraphs = []
#             paragraph_count = 1

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()

#                 if text:
#                     paragraphs = self.split_into_paragraphs(text)
#                     for paragraph_text in paragraphs:
#                         extracted_paragraphs.append(
#                             ParagraphDocument(paragraph_text, page_num + 1, paragraph_count, original_filename)
#                         )
#                         paragraph_count += 1  # ✅ **Ensure paragraph numbering is sequential**

#             if not extracted_paragraphs:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             return {
#                 "paragraphs": [paragraph.to_dict() for paragraph in extracted_paragraphs],
#                 "file_path": file_path,
#                 "filename": original_filename  # ✅ Ensure original filename is stored
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")



############## working by monday
import os
import fitz
import re
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter

class ParagraphDocument:
    """Represents a paragraph in a PDF with metadata."""
    def __init__(self, paragraph_text, page_no, paragraph_no, filename):
        self.paragraph_text = paragraph_text.strip()
        self.page_no = page_no
        self.paragraph_no = paragraph_no
        self.filename = filename

    def to_dict(self):
        """Convert to dictionary format for JSON serialization."""
        return {
            "paragraph_text": self.paragraph_text,
            "page_no": self.page_no,
            "paragraph_no": self.paragraph_no,
            "filename": self.filename 
        }

class PdfParser:
    """Parses a PDF and extracts paragraphs while keeping original filenames."""
    
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,  
            chunk_overlap=100, 
            separators=["\n\n", "\n", ". ", "? ", "! "]
        )

    def clean_text(self, text: str) -> str:
        """Cleans extracted text by removing unwanted artifacts."""
        text = re.sub(r'\u202c|\u202d', '', text)
        text = re.sub(r'\s+', ' ', text).strip()
        return text

    def split_into_paragraphs(self, text: str) -> List[str]:
        """
        Uses RecursiveCharacterTextSplitter for **context-aware** paragraph splitting.
        - Ensures **logical paragraph flow**.
        - Prevents incorrect short breaks.
        """
        text = self.clean_text(text)
        return self.text_splitter.split_text(text)

    def parse(self, file_path: str, original_filename: str) -> Dict:
        """
        Parses a PDF file and extracts paragraphs with metadata.

        Args:
            file_path (str): Path to the PDF file.
            original_filename (str): The actual filename to store.

        Returns:
            dict: Extracted content with paragraph metadata.
        """
        try:
            doc = fitz.open(file_path)
            extracted_paragraphs = []
            paragraph_count = 1

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()

                if text:
                    paragraphs = self.split_into_paragraphs(text)
                    for paragraph_text in paragraphs:
                        extracted_paragraphs.append(
                            ParagraphDocument(paragraph_text, page_num + 1, paragraph_count, original_filename)
                        )
                        paragraph_count += 1 

            if not extracted_paragraphs:
                raise ValueError(f"No extractable content found in {file_path}")

            return {
                "paragraphs": [paragraph.to_dict() for paragraph in extracted_paragraphs],
                "file_path": file_path,
                "filename": original_filename  
            }

        except Exception as e:
            raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")

# # if __name__ == "__main__":
# #     file_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/kb_arlo.pdf"
# #     original_filename = "kb_arlo.pdf"
    
# #     parser = PdfParser()
# #     parsed_data = parser.parse(file_path, original_filename)

# #     for paragraph in parsed_data["paragraphs"][:10]:  # Show first 10 paragraphs
# #         print(paragraph)

#################### workimng with images
# import os
# import fitz
# import re
# from typing import List, Dict
# from langchain.text_splitter import RecursiveCharacterTextSplitter

# class ParagraphDocument:
#     """Represents a paragraph in a PDF with metadata."""
#     def __init__(self, paragraph_text, page_no, paragraph_no, filename):
#         self.paragraph_text = paragraph_text.strip()
#         self.page_no = page_no
#         self.paragraph_no = paragraph_no
#         self.filename = filename

#     def to_dict(self):
#         """Convert to dictionary format for JSON serialization."""
#         return {
#             "paragraph_text": self.paragraph_text,
#             "page_no": self.page_no,
#             "paragraph_no": self.paragraph_no,
#             "filename": self.filename 
#         }

# class PdfParser:
#     """Parses a PDF and extracts paragraphs while keeping original filenames."""
    
#     def __init__(self):
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=700,  
#             chunk_overlap=100, 
#             separators=["\n\n", "\n", ". ", "? ", "! "]
#         )

#     def clean_text(self, text: str) -> str:
#         """Cleans extracted text by removing unwanted artifacts."""
#         text = re.sub(r'\u202c|\u202d', '', text)
#         text = re.sub(r'\s+', ' ', text).strip()
#         return text

#     def split_into_paragraphs(self, text: str) -> List[str]:
#         """
#         Uses RecursiveCharacterTextSplitter for **context-aware** paragraph splitting.
#         - Ensures **logical paragraph flow**.
#         - Prevents incorrect short breaks.
#         """
#         text = self.clean_text(text)
#         return self.text_splitter.split_text(text)

#     def extract_figures(self, doc: fitz.Document, output_dir: str) -> List[Dict]:
#         os.makedirs(output_dir, exist_ok=True)
#         figures = []
#         for page_num in range(len(doc)):
#             page = doc[page_num]
#             images = page.get_images(full=True)
#             for idx, img in enumerate(images):
#                 xref = img[0]
#                 base_image = doc.extract_image(xref)
#                 image_bytes = base_image["image"]
#                 ext = base_image["ext"]
#                 image_name = f"figure_p{page_num+1}_{idx+1}.{ext}"
#                 image_path = os.path.join(output_dir, image_name)
#                 with open(image_path, "wb") as img_file:
#                     img_file.write(image_bytes)
#                 figures.append({
#                     "page_no": page_num + 1,
#                     "image_name": image_name,
#                     "image_path": image_path
#                 })
#         return figures

     
#     def parse(self, file_path: str, original_filename: str, image_output_dir: str = "./figures") -> Dict:
#         """
#         Parses a PDF file and extracts paragraphs with metadata.

#         Args:
#             file_path (str): Path to the PDF file.
#             original_filename (str): The actual filename to store.
#             image_output_dir (str): Directory to store extracted figure images.

#         Returns:
#             dict: Extracted content with paragraph and figure metadata.
#         """
#         try:
#             doc = fitz.open(file_path)
#             extracted_paragraphs = []
#             paragraph_count = 1

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()

#                 if text:
#                     paragraphs = self.split_into_paragraphs(text)
#                     for paragraph_text in paragraphs:
#                         extracted_paragraphs.append(
#                             ParagraphDocument(paragraph_text, page_num + 1, paragraph_count, original_filename)
#                         )
#                         paragraph_count += 1 

#             if not extracted_paragraphs:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             figure_data = self.extract_figures(doc, output_dir=image_output_dir)

#             return {
#                 "paragraphs": [paragraph.to_dict() for paragraph in extracted_paragraphs],
#                 "figures": figure_data,
#                 "file_path": file_path,
#                 "filename": original_filename  
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")


##################################################################################
# import os
# import fitz  # PyMuPDF
# import re
# from typing import List, Dict
# from langchain.text_splitter import RecursiveCharacterTextSplitter
# from PIL import Image
# import cv2
# import numpy as np
# import layoutparser as lp

# class ParagraphDocument:
#     def __init__(self, paragraph_text, page_no, paragraph_no, filename):
#         self.paragraph_text = paragraph_text.strip()
#         self.page_no = page_no
#         self.paragraph_no = paragraph_no
#         self.filename = filename

#     def to_dict(self):
#         return {
#             "paragraph_text": self.paragraph_text,
#             "page_no": self.page_no,
#             "paragraph_no": self.paragraph_no,
#             "filename": self.filename
#         }

# class PdfParser:
#     def __init__(self):
#         self.text_splitter = RecursiveCharacterTextSplitter(
#             chunk_size=700,
#             chunk_overlap=100,
#             separators=["\n\n", "\n", ". ", "? ", "! "]
#         )
#         self.model = lp.Detectron2LayoutModel(
#             config_path="lp://PubLayNet/faster_rcnn_R_50_FPN_3x/config",
#             model_path=os.path.abspath(os.path.join(os.path.dirname(__file__), "layoutparser_models", "faster_rcnn_R_50_FPN_3x.pth")),
#             label_map={0: "Text", 1: "Title", 2: "List", 3: "Table", 4: "Figure"},
#             extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", 0.8]
#         )


#     def clean_text(self, text: str) -> str:
#         text = re.sub(r'\u202c|\u202d', '', text)
#         text = re.sub(r'\s+', ' ', text).strip()
#         return text

#     def split_into_paragraphs(self, text: str) -> List[str]:
#         text = self.clean_text(text)
#         return self.text_splitter.split_text(text)

#     def extract_figures(self, doc: fitz.Document, image_output_dir: str) -> List[Dict]:
#         os.makedirs(image_output_dir, exist_ok=True)
#         figures = []

#         for page_num in range(len(doc)):
#             page = doc[page_num]
#             text_blocks = page.get_text("blocks")
#             pix = page.get_pixmap(dpi=300)
#             img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape((pix.height, pix.width, pix.n))
#             if pix.n == 4:
#                 img_array = cv2.cvtColor(img_array, cv2.COLOR_RGBA2RGB)

#             image_name_prefix = f"figure_p{page_num+1}_"
#             layout = self.model.detect(img_array)
#             idx = 1

#             for block in layout:
#                 if block.type == "Figure":
#                     x1, y1, x2, y2 = map(int, block.coordinates)
#                     figure_crop = img_array[y1:y2, x1:x2]
#                     image_name = f"{image_name_prefix}{idx}.png"
#                     image_path = os.path.join(image_output_dir, image_name)
#                     cv2.imwrite(image_path, figure_crop)

#                     caption_text = None
#                     closest_dist = float('inf')
#                     for b in text_blocks:
#                         tx, ty, bx, by, text, *_ = b
#                         text = text.strip()
#                         if re.match(r"Figure\s*\d+[\.:\-]?", text, re.IGNORECASE):
#                             dist = min(abs(ty - y2), abs(by - y1))
#                             if dist < closest_dist and dist < 200:
#                                 closest_dist = dist
#                                 caption_text = text

#                     figures.append({
#                         "page_no": page_num + 1,
#                         "image_name": image_name,
#                         "image_path": image_path,
#                         "bbox": [x1, y1, x2, y2],
#                         "caption": caption_text
#                     })
#                     idx += 1

#         return figures

#     def parse(self, file_path: str, original_filename: str, image_output_dir: str = "./figures") -> Dict:
#         try:
#             doc = fitz.open(file_path)
#             extracted_paragraphs = []
#             paragraph_count = 1

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()
#                 if text:
#                     paragraphs = self.split_into_paragraphs(text)
#                     for paragraph_text in paragraphs:
#                         extracted_paragraphs.append(
#                             ParagraphDocument(paragraph_text, page_num + 1, paragraph_count, original_filename)
#                         )
#                         paragraph_count += 1

#             if not extracted_paragraphs:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             figure_data = self.extract_figures(doc, image_output_dir)

#             return {
#                 "paragraphs": [p.to_dict() for p in extracted_paragraphs],
#                 "figures": figure_data,
#                 "file_path": file_path,
#                 "filename": original_filename
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")
