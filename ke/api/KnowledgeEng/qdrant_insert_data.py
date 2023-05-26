import openai
import os
import numpy as np
from datasets import load_dataset
import qdrant_client
from qdrant_client import QdrantClient
from qdrant_client.http.models import Batch
import json
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from qdrant_client.http.models import Distance, VectorParams
import qdrant_client.http as http_config
import datetime
import logging
from time import time
import config as cfg

http_config.HTTP_CLIENT_TIMEOUT = 60 

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)

qdrant_client = QdrantClient(
    url = cfg.qdrant_url, #"https://a29a4a5f-b731-4ffa-befd-5c3f702c66f3.us-east-1-0.aws.cloud.qdrant.io:6333", 
    api_key = cfg.qdrant_api_key #"bD7Kx0EQ3hPe2FJjzjNpXr7E4mZatk9MAhqwNHi4EBOPdNqKcRW7HA"
)


openai.api_key = cfg.openai_api_key#"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"
collection_name=cfg.collection_name#"kbDocs_30Incidents_v2"
MODEL = cfg.embedding_model#text-embedding-ada-002"
  

def process_data(input_text):
    page_content=[]
    idsVal=[]
    metadatas = []
    payload=[]
    time_start = gettime()
    logger.info(f'Qdrant process preparing data..using collection name :: - {collection_name}') 
    idCount = 1
    #print(type(input_text))
    data = json.loads(input_text)
    print(data[cfg.product_key])
    tokenSize=data["TotalTokens"]
    metaData={ "id"           : idCount
            ,"Summary"      : data["Summary"] \
            ,"DocumentType" : data["DocumentType"] \
            ,"DocumentId"   : data["DocumentId"] \
            ,"Product"      : data["Product"] \
            ,"Version"      : data["Version"] \
            ,"title"        : data["Topic"]\
            ,"Sub-title"    : data["Sub-Topic"]\
            ,"tokenSize"    : tokenSize \
            #,"filename"     : filename \
            ,"source"       : data["url"]\
            }      
    idCount += 1
    record_texts = readchunks(data["Chunks"])
    page_content.extend(record_texts)
    record_metadatas = [{ "chunk": j,  **metaData                     
    } for j, page_content in enumerate(record_texts)]
    metadatas.extend(record_metadatas)
    encoding = tiktoken.encoding_for_model(MODEL)

    for i in range(len(metadatas)):
        if (metadatas[i]['chunk'] > 0):
            page_content[i] = metadatas[i]['title']+"\\n"+page_content[i]

    kbDocs = openai.Embedding.create( input= page_content, engine=MODEL)

    vectors=[]
    for i in range(len(kbDocs["data"])):
        vectors.append(kbDocs["data"][i]["embedding"])
        idsVal.append(i)
        tokenSize=encoding.encode(page_content[i])
        print(tokenSize)
        metadatas[i]["tokenSize"]=len(tokenSize)
        payload.append({"page_content":page_content[i], "metadata" : metadatas[i]})

    time_start = gettime()
    logger.info(f'Qdrant insert process begins :: - {int(time() * 1e+3) - time_start}ms')         
    qdrant_client.upsert(
            collection_name=collection_name,
            points=Batch(
                ids=idsVal,
                payloads=payload,
                vectors=vectors                    
            ),
    )
    logger.info(f'Qdrant insert process completed :: - {int(time() * 1e+3) - time_start}ms') 
    return

def readchunks(chunks):
    chunklist = []
    for chunk in chunks:            
           chunklist.append(chunk["Text"])      
    return chunklist

def create_collection():
    qdrant_client.recreate_collection( collection_name=collection_name
                                 ,vectors_config=VectorParams( size=1536
                                  ,distance=Distance.COSINE ),
                                 )

def gettime():
    time_start = int(time() * 1e+3)
    return time_start

#only for creating collection directly
#create_collection()
