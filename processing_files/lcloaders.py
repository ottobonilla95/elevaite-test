from langchain.document_loaders import UnstructuredURLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List
import sys
from langchain.vectorstores import Qdrant
from langchain.embeddings import HuggingFaceEmbeddings
from qdrant_client import QdrantClient

HUGGINGFACE_EMBEDDINGS = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L12-v2")
QDRANT_URL = "your_quardrant_cluster_endpoint"
QDRANT_APIKEY = "" # This will come from secrets

def get_document_from_url(list_of_urls: List) -> List:
    if (len(list_of_urls) > 0):
        loader = UnstructuredURLLoader(urls=list_of_urls)
        document = loader.load()
        print(document[0].page_content)
        return document

def get_text_chunks_from_document(document: str, chunk_size: int, chunk_overlap: int):
    text_splitter = RecursiveCharacterTextSplitter( chunk_size=chunk_size, chunk_overlap  = chunk_overlap)
    text_chunks = text_splitter.create_documents([document[0].page_content])
    print("---Chunks- Total Count -- {}".format(len(text_chunks)))
    print (text_chunks)
    return text_chunks

def load_chunks_to_vector_db(text_chunks: List):
    qdrant_client = QdrantClient(
        QDRANT_URL, 
        prefer_grpc=True,
        api_key=QDRANT_APIKEY,
    )

    qdrant = Qdrant(
        client=qdrant_client, collection_name="pan_docs_st_mini", 
        embedding_function=HUGGINGFACE_EMBEDDINGS.embed_query
    )
    document_ids = qdrant.add_documents(documents=text_chunks)
    print(document_ids)



def main():
    if (len(sys.argv) > 1):
        list_of_urls = sys.argv[1:]
        document = get_document_from_url(list_of_urls=list_of_urls)
        text_chunks = get_text_chunks_from_document(document=document, chunk_size=1500, chunk_overlap=20)
        #load_chunks_to_vector_db(text_chunks=text_chunks)

if __name__ == "__main__":
    main()