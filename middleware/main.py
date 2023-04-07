from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from typing import Union
import qdrant_client
import pandas as pd
from qdrant_client import QdrantClient
import openai
app = FastAPI()


origins = ["https://elevaite.iopex.ai/"]

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
    print("Text chunk 1: ", result[0].payload['Text'], result[0].score, result[0].payload['url'])
    print("Text chunk 2: ", result[1].payload['Text'], result[1].score, result[1].payload['url'])
    print("Text chunk 3: ", result[2].payload['Text'], result[2].score, result[2].payload['url'])
    data = [query, 
            result[0].payload['Text'], result[0].score, result[0].payload['url'], 
            result[1].payload['Text'], result[1].score, result[1].payload['url'],
            result[2].payload['Text'], result[2].score, result[2].payload['url'],
            ]
    context = "Context:"+result[0].payload['Text'] + result[1].payload['Text'] + result[2].payload['Text'] + "Answer from the provided context only. Answer should be embedded in HTML tags." + query
    # completion = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=[{"role": "user", "content": context}])
    completion = openai.Completion.create(model="text-davinci-003", prompt=context, temperature=0, max_tokens=2500)
    data = [{"query":query, 
            "text_1":result[0].payload['Text'], "score":result[0].score, "url_1":result[0].payload['url'], "topic_1":result[0].payload['Topic'], 
            "text_2":result[1].payload['Text'], "score":result[1].score, "url_2":result[1].payload['url'], "topic_2":result[1].payload['Topic'], 
            "text_3":result[2].payload['Text'], "score":result[2].score, "url_3":result[2].payload['url'], "topic_3":result[2].payload['Topic'], 
            "answer":completion.choices[0].text}
            ]
    # columns=["query", "text_1", "score", "url_1", "text_2", "score", "url_2", "text_3", "score", "url_3", "answer"]
    df = pd.DataFrame(data)
    # print(df)
    df.to_csv("out.csv")
    return {"text":completion.choices[0].text, 
            "url_1":result[0].payload['url'], "topic_1":result[0].payload['Sub-Topic'],
            "url_2":result[1].payload['url'], "topic_2":result[1].payload['Sub-Topic'],
            "url_3":result[2].payload['url'], "topic_3":result[2].payload['Sub-Topic']}