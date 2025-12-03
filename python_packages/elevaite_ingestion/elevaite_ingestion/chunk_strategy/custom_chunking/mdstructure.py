import uuid
from typing import List, Dict


async def chunk_text(parsed_data: Dict, chunking_params: Dict) -> List[Dict]:
    """
    Markdown structure-based chunking that respects code blocks and paragraph boundaries.

    Args:
        parsed_data: Dict containing 'paragraphs' from parsing stage
        chunking_params: Dict with 'chunk_size' setting

    Returns:
        List of chunk dictionaries with chunk_id, chunk_text, filename, page_range
    """
    chunk_size = chunking_params.get("chunk_size", 2000)

    # Extract paragraphs from parsed data
    paragraphs = parsed_data.get("paragraphs", [])
    if not paragraphs:
        return []

    filename = parsed_data.get("filename", "unknown")

    # Build full text from paragraphs
    full_text = "\n\n".join([p.get("paragraph_text", "") for p in paragraphs])

    raw_chunks = []
    start = 0
    text_length = len(full_text)

    while start < text_length:
        end = start + chunk_size
        if end >= text_length:
            raw_chunks.append(full_text[start:].strip())
            break

        chunk = full_text[start:end]
        code_block = chunk.rfind("```")
        if code_block != -1 and code_block > chunk_size * 0.3:
            end = start + code_block
        elif "\n\n" in chunk:
            last_break = chunk.rfind("\n\n")
            if last_break > chunk_size * 0.3:
                end = start + last_break
        elif ". " in chunk:
            last_period = chunk.rfind(". ")
            if last_period > chunk_size * 0.3:
                end = start + last_period + 1

        chunk = full_text[start:end].strip()
        if chunk:
            raw_chunks.append(chunk)

        start = max(start + 1, end)

    # Convert to standard format with metadata
    chunks = []
    for chunk_text_content in raw_chunks:
        # Find contributing paragraphs to determine page range
        page_numbers = set()
        for p in paragraphs:
            p_text = p.get("paragraph_text", "")
            if p_text in chunk_text_content or chunk_text_content in p_text:
                page_numbers.add(p.get("page_no", 1))

        chunks.append(
            {
                "chunk_id": str(uuid.uuid4()),
                "chunk_text": chunk_text_content,
                "filename": filename,
                "page_range": sorted(list(page_numbers)) if page_numbers else [1],
            }
        )

    return chunks


# def create_chunks_from_lines(line_documents, chunk_size=5):
#     """
#     Groups LineDocument objects into semantic chunks.

#     Args:
#         line_documents (list): List of LineDocument objects.
#         chunk_size (int): Number of lines per chunk.

#     Returns:
#         list: List of chunk dictionaries with metadata.
#     """
#     chunks = []
#     current_chunk = []
#     current_metadata = {"source_files": set(), "page_numbers": set()}

#     for line_doc in line_documents:
#         if len(current_chunk) >= chunk_size:
#             chunks.append({
#                 "chunk_number": len(chunks),
#                 "content": "\n".join(current_chunk),
#                 "source_files": list(current_metadata["source_files"]),
#                 "page_numbers": sorted(current_metadata["page_numbers"])
#             })
#             current_chunk = []
#             current_metadata = {"source_files": set(), "page_numbers": set()}

#         # Append new line to the chunk
#         current_chunk.append(line_doc.text)
#         current_metadata["source_files"].add(line_doc.source_file)
#         current_metadata["page_numbers"].add(line_doc.page_number)

#     if current_chunk:
#         chunks.append({
#             "chunk_number": len(chunks),
#             "content": "\n".join(current_chunk),
#             "source_files": list(current_metadata["source_files"]),
#             "page_numbers": sorted(current_metadata["page_numbers"])
#         })

#     return chunks
