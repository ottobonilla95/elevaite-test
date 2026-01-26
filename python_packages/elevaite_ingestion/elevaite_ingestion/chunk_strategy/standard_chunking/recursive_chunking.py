import uuid
from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter


async def chunk_text(parsed_data: Dict, chunking_params: Dict) -> List[Dict]:
    """
    Chunk text using recursive character text splitter.

    Args:
        parsed_data: Dict containing 'paragraphs' or 'content' from parsing stage
        chunking_params: Dict with 'chunk_size' and 'chunk_overlap' settings

    Returns:
        List of chunk dictionaries with chunk_id, chunk_text, filename, page_range
    """
    chunk_size = chunking_params.get("chunk_size", 500)
    chunk_overlap = chunking_params.get("chunk_overlap", 50)

    # Extract paragraphs from parsed data (consistent with semantic chunker)
    paragraphs = parsed_data.get("paragraphs", [])
    if not paragraphs:
        return []

    filename = parsed_data.get("filename", "unknown")

    try:
        # Build full text from paragraphs
        full_text = "\n".join([p.get("paragraph_text", "") for p in paragraphs])
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

        docs = text_splitter.create_documents([full_text])

        chunks = []
        for i, doc in enumerate(docs):
            chunk_content = doc.page_content.strip()

            # Find contributing paragraphs to determine page range
            contributing_paragraphs = [
                p
                for p in paragraphs
                if p.get("paragraph_text", "") in chunk_content
                or chunk_content in p.get("paragraph_text", "")
            ]

            # Get page numbers from contributing paragraphs
            page_numbers = (
                list(set(p.get("page_no", 1) for p in contributing_paragraphs))
                if contributing_paragraphs
                else [1]
            )

            chunk_data = {
                "chunk_id": str(uuid.uuid4()),
                "chunk_text": chunk_content,
                "filename": filename,
                "page_range": sorted(page_numbers),
            }
            chunks.append(chunk_data)

        return chunks

    except Exception as e:
        print(f"Error during recursive chunking: {e}")
        return []
