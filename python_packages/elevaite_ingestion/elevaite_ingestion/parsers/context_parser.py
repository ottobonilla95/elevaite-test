import re
import fitz  # PyMuPDF
from nltk.tokenize import sent_tokenize

# ==============================
# PDF Parsing & Sentence Extraction
# ==============================


class SentenceDocument:
    """Represents a single sentence in a PDF along with metadata."""

    def __init__(self, sentence_text, page_no, sentence_no):
        self.sentence_text = sentence_text.strip()
        self.page_no = page_no
        self.sentence_no = sentence_no

    def to_dict(self):
        """Convert to dictionary format for JSON serialization."""
        return {
            "sentence_text": self.sentence_text,
            "page_no": self.page_no,
            "sentence_no": self.sentence_no,
        }


class PdfParser:
    """Parses a PDF file and extracts sentences with metadata."""

    def __init__(self):
        pass

    def parse(self, file_path):
        """
        Parses a PDF file and extracts sentences with metadata.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            list: List of SentenceDocument objects.
        """
        try:
            doc = fitz.open(file_path)
            extracted_sentences = []

            list_pattern = re.compile(
                r"^(\d+\.|\•|\-)\s"
            )  # Matches "1.", "•", "-" at the start

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()

                if text:
                    sentences = sent_tokenize(text)
                    merged_sentences = []
                    buffer = ""

                    for sentence in sentences:
                        sentence = sentence.strip()

                        if list_pattern.match(
                            sentence
                        ):  # If sentence starts with a list marker
                            if (
                                buffer
                            ):  # Save previous buffer before starting a new list item
                                merged_sentences.append(buffer.strip())
                            buffer = sentence  # Start a new buffer
                        else:
                            buffer += " " + sentence  # Merge into the previous sentence

                    # ✅ Step 3: Append last buffered sentence
                    if buffer:
                        merged_sentences.append(buffer.strip())

                    # ✅ Step 4: Create SentenceDocument objects
                    for sentence_no, sentence_text in enumerate(
                        merged_sentences, start=1
                    ):
                        if sentence_text.strip():
                            extracted_sentences.append(
                                SentenceDocument(
                                    sentence_text, page_num + 1, sentence_no
                                )
                            )

            if not extracted_sentences:
                raise ValueError(f"No extractable content found in {file_path}")

            return extracted_sentences

        except Exception as e:
            raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")


if __name__ == "__main__":
    file_path = (
        "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/INPUT/kb_arlo_check.pdf"
    )

    parser = PdfParser()
    sentence_objects = parser.parse(file_path)

    print("\n########## 1️⃣ Extracted Sentences ##########")
    for idx, sentence in enumerate(sentence_objects[:30]):
        print(f"Sentence {idx + 1}: {sentence.sentence_text} (Page {sentence.page_no})")
    print("###########################################\n")
