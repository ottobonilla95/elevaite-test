import uuid
from typing import List, Dict


async def chunk_text(parsed_data: Dict, chunking_params: Dict) -> List[Dict]:
    """
    Custom sentence-based chunking strategy that uses paragraphs from parsed data
    and splits them into sentence-based chunks.

    Args:
        parsed_data: Dict containing 'paragraphs' from parsing stage
        chunking_params: Dict with 'max_chunk_size' setting

    Returns:
        List of chunk dictionaries with chunk_id, chunk_text, filename, page_range
    """
    max_chunk_size = chunking_params.get("max_chunk_size", 500)

    # Extract paragraphs from parsed data
    paragraphs = parsed_data.get("paragraphs", [])
    if not paragraphs:
        return []

    filename = parsed_data.get("filename", "unknown")

    chunks = []
    current_chunk_text = ""
    current_page_numbers = set()

    for paragraph in paragraphs:
        paragraph_text = paragraph.get("paragraph_text", "").strip()
        page_no = paragraph.get("page_no", 1)

        # If adding this paragraph exceeds the max_chunk_size, save the current chunk and start a new one
        if len(current_chunk_text) + len(paragraph_text) > max_chunk_size and current_chunk_text:
            chunks.append(
                {
                    "chunk_id": str(uuid.uuid4()),
                    "chunk_text": current_chunk_text.strip(),
                    "filename": filename,
                    "page_range": sorted(list(current_page_numbers)),
                }
            )
            # Reset chunk
            current_chunk_text = ""
            current_page_numbers = set()

        # Add paragraph to the current chunk
        current_chunk_text = (current_chunk_text + " " + paragraph_text).strip()
        current_page_numbers.add(page_no)

    # Save the last chunk if it has content
    if current_chunk_text:
        chunks.append(
            {
                "chunk_id": str(uuid.uuid4()),
                "chunk_text": current_chunk_text.strip(),
                "filename": filename,
                "page_range": sorted(list(current_page_numbers)),
            }
        )

    return chunks
