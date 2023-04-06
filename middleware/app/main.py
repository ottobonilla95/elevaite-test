from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from typing import Union
import qdrant_client
from qdrant_client import QdrantClient
import openai
app = FastAPI()


origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openai.api_key = "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"
embedding_model = "text-embedding-ada-002"
collection_name = "kbDocs_openAI"
MODEL = "text-embedding-ada-002"
qdrant_client = QdrantClient(
    url="https://a29a4a5f-b731-4ffa-befd-5c3f702c66f3.us-east-1-0.aws.cloud.qdrant.io:6333", 
    api_key="bD7Kx0EQ3hPe2FJjzjNpXr7E4mZatk9MAhqwNHi4EBOPdNqKcRW7HA"
)
@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/answer")
def read_answer():
    return("Here is the answer")

@app.get("/query/")
def read_item(query: str):
    # retrieve based on ask
    print(query)
    vectorized_ask = openai.Embedding.create( input= query, engine=MODEL)
    result = qdrant_client.search(
        collection_name=collection_name,
        query_vector=vectorized_ask["data"][0]["embedding"],
        limit=3,
        with_vectors=True,
        with_payload=True,
    )
    context = "Context:"+result[0].payload['Text'] + result[1].payload['Text'] + result[2].payload['Text'] + "Answer only from the provided context. Here is the Question:" + query
    completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": context}])
    return completion.choices[0].message.content
