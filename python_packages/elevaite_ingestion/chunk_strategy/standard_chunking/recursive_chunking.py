from typing import List, Dict
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(sentences_data: List[Dict], chunk_size: int = 100, chunk_overlap: int = 20) -> List[Dict]:

    try:
        full_text = "\n".join([sentence["sentence_text"] for sentence in sentences_data])
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False
        )

        docs = text_splitter.create_documents([full_text])

        chunks = []
        for i, doc in enumerate(docs):
            chunk_text = doc.page_content.strip()

            contributing_sentences = [
                sentence for sentence in sentences_data if sentence["sentence_text"] in chunk_text
            ]

            page_numbers = list(set(sentence["page_no"] for sentence in contributing_sentences))

            chunk_data = {
                "chunk_number": i + 1,
                "content": chunk_text,
                "page_no": page_numbers,
                "file_path": sentences_data[0].get("file_path", "unknown")
            }
            chunks.append(chunk_data)

        return chunks

    except Exception as e:
        print(f"Error during recursive chunking: {e}")
        return []
