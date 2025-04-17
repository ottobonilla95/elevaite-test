from typing import List, Dict

def chunk_text(sentences_data: List[Dict], max_chunk_size: int = 500) -> List[Dict]:
    """
    Custom sentence-based chunking strategy that ensures full sentences are retained
    while keeping metadata such as page numbers and sentence numbers.

    Args:
        sentences_data (List[Dict]): List of sentences with metadata (page_no, sentence_no).
        max_chunk_size (int): The maximum number of characters allowed in a chunk.

    Returns:
        List[Dict]: Chunked text data with metadata.
    """
    chunks = []
    current_chunk = []
    current_chunk_text = ""
    current_page_numbers = set()
    current_sentence_numbers = []

    for sentence in sentences_data:
        sentence_text = sentence["sentence_text"].strip()
        page_no = sentence["page_no"]
        sentence_no = sentence["sentence_no"]

        # If adding this sentence exceeds the max_chunk_size, save the current chunk and start a new one
        if len(current_chunk_text) + len(sentence_text) > max_chunk_size:
            chunks.append({
                "chunk_number": len(chunks) + 1,
                "content": current_chunk_text.strip(),
                "page_no": list(current_page_numbers),  # Preserve all pages in this chunk
                "sentence_range": current_sentence_numbers,  # Preserve sentence_no
                "file_path": sentences_data[0].get("file_path", "unknown")
            })
            # Reset chunk
            current_chunk = []
            current_chunk_text = ""
            current_page_numbers = set()
            current_sentence_numbers = []

        # Add sentence to the current chunk
        current_chunk.append(sentence_text)
        current_chunk_text = " ".join(current_chunk)
        current_page_numbers.add(page_no)
        current_sentence_numbers.append((page_no, sentence_no))

    # Save the last chunk if it has content
    if current_chunk:
        chunks.append({
            "chunk_number": len(chunks) + 1,
            "content": current_chunk_text.strip(),
            "page_no": list(current_page_numbers),
            "sentence_range": current_sentence_numbers,
            "file_path": sentences_data[0].get("file_path", "unknown")
        })

    return chunks
