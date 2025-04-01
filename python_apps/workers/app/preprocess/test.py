import os
import time
from typing import List
from langchain_community.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores.qdrant import Qdrant
from langchain_community.document_loaders.lakefs import LakeFSLoader
from langchain_core.documents import Document


def langchain_pp_batch(
    key_id: str,
    secret: str,
    endpoint: str,
    repo: str,
    ref: str,
    qdrant_url: str,
    qdrant_collection: str,
):
    start = time.time()
    lakefs_loader = LakeFSLoader(
        lakefs_access_key=key_id,
        lakefs_secret_key=secret,
        lakefs_endpoint=endpoint,
    )
    lakefs_loader.set_repo(repo)
    lakefs_loader.set_ref(ref)
    # lakefs_loader.set_path(path)
    docs = lakefs_loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
    docs = splitter.split_documents(docs)
    embeddings = OpenAIEmbeddings()
    qdrant = Qdrant.from_documents(
        docs,
        embeddings,
        url=qdrant_url,
        # prefer_grpc=True,
        collection_name=qdrant_collection,
    )
    end = time.time()
    print("batch")
    print(end - start)


def langchain_pp_one_by_one(
    key_id: str,
    secret: str,
    endpoint: str,
    repo: str,
    ref: str,
    qdrant_url: str,
    qdrant_collection: str,
):
    start = time.time()
    lakefs_loader = LakeFSLoader(
        lakefs_access_key=key_id,
        lakefs_secret_key=secret,
        lakefs_endpoint=endpoint,
    )
    lakefs_loader.set_repo(repo)
    lakefs_loader.set_ref(ref)
    # lakefs_loader.set_path(path)
    docs = lakefs_loader.load()
    splitter = RecursiveCharacterTextSplitter(chunk_size=2000, chunk_overlap=100)
    split_docs: List[Document] = []
    for doc in docs:
        _doc = splitter.split_documents([doc])
        split_docs.extend(_doc)

    # docs = splitter.split_documents(docs)
    embeddings = OpenAIEmbeddings()

    for split_doc in split_docs:
        qdrant = Qdrant.from_documents(
            documents=[split_doc],
            embedding=embeddings,
            url=qdrant_url,
            # prefer_grpc=True,
            collection_name=qdrant_collection,
        )
    end = time.time()
    print(end - start)


if __name__ == "__main__":
    os.environ["OPENAI_API_KEY"] = ""
    print("starting test")
    langchain_pp_batch(
        key_id="",
        secret="",
        endpoint="https://elevaite-ke.iopex.ai",
        qdrant_url="http://localhost:6333",
        qdrant_collection="test-batch-1",
        repo="default-project-compassionate-lalande",
        ref="main",
    )
    langchain_pp_one_by_one(
        key_id="",
        secret="",
        endpoint="https://elevaite-ke.iopex.ai",
        qdrant_url="http://localhost:6333",
        qdrant_collection="test-one-by-one-1",
        repo="default-project-compassionate-lalande",
        ref="main",
    )
