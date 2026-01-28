import os
import sys
from typing import Dict, List

base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
# print(base_path)
sys.path.append(base_path)
from agentic_chunking.agentic_chunk import AgenticChunker


def chunk_text(input_data: Dict) -> List[Dict]:
    """
    Uses AgenticChunker to merge semantically similar paragraphs.
    """
    try:
        filename = input_data.get("filename", "unknown_file")

        if "paragraphs" in input_data:
            paragraphs_data = input_data["paragraphs"]
            if not paragraphs_data:
                raise ValueError(f"No paragraphs found in PDF: {filename}")

            whole_document_text = " ".join(
                [para["paragraph_text"] for para in paragraphs_data]
            )

            chunker = AgenticChunker()
            for para in paragraphs_data:
                chunker._create_new_chunk(
                    para["paragraph_text"],
                    para["page_no"],
                    filename,
                    whole_document_text,
                )

            return [chunker.get_chunks()]
        else:
            raise ValueError(f"No paragraphs found in input data: {filename}")

    except Exception as e:
        print(
            f"❌ Error during chunking ({input_data.get('filename', 'unknown_file')}): {e}"
        )
        return []
