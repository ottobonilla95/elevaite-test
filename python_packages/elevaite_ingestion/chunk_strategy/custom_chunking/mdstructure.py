from typing import List


def chunk_text(text: str, chunk_size: int = 2000) -> List[str]:
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        chunk = text[start:end]
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

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        start = max(start + 1, end)

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
