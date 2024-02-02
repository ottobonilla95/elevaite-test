import os
import json
import vectordb
import asyncio
import time


async def insert_vectors(collection=None, BASE_DIR: str = None):
    for subdir, dirs, files in os.walk(BASE_DIR):
        payloads = []
        for file in files:
            print(os.path.join(subdir, file))
            with open(os.path.join(subdir, file), "r") as metadata:
                payload = json.load(metadata)
            payloads.append(payload)
        await vectordb.insert_records(
            collection=collection, payload_with_contents=payloads
        )


async def create_qdrant_collection(collection_name: str):
    await vectordb.recreate_collection(collection=collection_name)
