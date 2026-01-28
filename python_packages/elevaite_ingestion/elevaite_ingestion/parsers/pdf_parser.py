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
            "filename": self.filename,
        }


class PdfParser:
    """Parses a PDF and extracts paragraphs while keeping original filenames."""

    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=700,
            chunk_overlap=100,
            separators=["\n\n", "\n", ". ", "? ", "! "],
        )

    def clean_text(self, text: str) -> str:
        """Cleans extracted text by removing unwanted artifacts."""
        text = re.sub(r"\u202c|\u202d", "", text)
        text = re.sub(r"\s+", " ", text).strip()
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
                            ParagraphDocument(
                                paragraph_text,
                                page_num + 1,
                                paragraph_count,
                                original_filename,
                            )
                        )
                        paragraph_count += 1

            if not extracted_paragraphs:
                raise ValueError(f"No extractable content found in {file_path}")

            return {
                "paragraphs": [
                    paragraph.to_dict() for paragraph in extracted_paragraphs
                ],
                "file_path": file_path,
                "filename": original_filename,
            }

        except Exception as e:
            raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")
