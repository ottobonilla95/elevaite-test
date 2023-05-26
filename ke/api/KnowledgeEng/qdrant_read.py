import openai
import os
import numpy as np
from datasets import load_dataset
import qdrant_client
from qdrant_client import QdrantClient
from qdrant_client.http.models import Batch
import json
import config as cfg

qdrant_client = QdrantClient(
    url=cfg.qdrant_url, #"https://a29a4a5f-b731-4ffa-befd-5c3f702c66f3.us-east-1-0.aws.cloud.qdrant.io:6333", 
    api_key=cfg.qdrant_api_key #"bD7Kx0EQ3hPe2FJjzjNpXr7E4mZatk9MAhqwNHi4EBOPdNqKcRW7HA"
)

collection_name = cfg.collection_name

#qdrant_client.delete_collection(collection_name="kbDocs_30Incidents")

results=qdrant_client.scroll(collection_name=collection_name, limit=100)
#results=qdrant_client.scroll(collection_name="kbDocs_30Incidents", limit=100)
print (results)
#for point in results[0]:
#    print(str(point.id) + " : " + point.payload["metadata"]["Summary"] + " : " + point.payload["metadata"]["source"] + ":" + point.payload["metadata"]["page_content"])