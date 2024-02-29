import asyncio
from datetime import datetime
import json
import os
from pprint import pprint
import sys
import threading
from elasticsearch import Elasticsearch
import lakefs
import redis
from unstructured.partition.html import partition_html
from unstructured.chunking.title import chunk_by_title

from dotenv import load_dotenv
import pika

from .preprocess import get_file_elements_internal
from . import vectordb


class PreProcessForm:
    creator: str
    name: str
    datasetId: str
    datasetName: str
    datasetProject: str
    datasetVersion: str | None
    datasetOutputURI: str | None
    queue: str
    maxIdleTime: str
    instanceId: str
    applicationId: str
    selectedPipeline: str

    def __init__(
        self,
        name: str,
        datasetId: str,
        datasetName: str,
        datasetProject: str,
        datasetVersion: str | None,
        datasetOutputURI: str | None,
        queue: str,
        maxIdleTime: str,
        instanceId: str,
        creator: str,
        applicationId: str,
        selectedPipeline: str,
    ) -> None:
        self.name = name
        self.datasetId = datasetId
        self.datasetName = datasetName
        self.datasetProject = datasetProject
        self.datasetVersion = datasetVersion
        self.datasetOutputURI = datasetOutputURI
        self.queue = queue
        self.maxIdleTime = maxIdleTime
        self.instanceId = instanceId
        self.creator = creator
        self.applicationId = applicationId
        self.selectedPipeline = selectedPipeline


def wrap_async_func(_data: PreProcessForm):
    asyncio.run(preprocess(_data))


def preprocess_callback(ch, method, properties, body):
    _data = json.loads(body)

    print(f" [x] Received {_data}")

    _formData = PreProcessForm(
        **_data["dto"],
        instanceId=_data["id"],
        applicationId=_data["application_id"],
    )

    t = threading.Thread(target=wrap_async_func, args=(_formData,))
    t.start()


async def preprocess(data: PreProcessForm) -> None:
    LAKEFS_ACCESS_KEY_ID = os.getenv("LAKEFS_ACCESS_KEY_ID")
    LAKEFS_SECRET_ACCESS_KEY = os.getenv("LAKEFS_SECRET_ACCESS_KEY")
    LAKEFS_ENDPOINT_URL = os.getenv("LAKEFS_ENDPOINT_URL")
    LAKEFS_STORAGE_NAMESPACE = os.getenv("LAKEFS_STORAGE_NAMESPACE")
    REDIS_HOST = os.getenv("REDIS_HOST")
    REDIS_PORT = os.getenv("REDIS_PORT")
    REDIS_USERNAME = os.getenv("REDIS_USERNAME")
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD")
    ELASTIC_SSL_FINGERPRINT = os.getenv("ELASTIC_SSL_FINGERPRINT")
    ELASTIC_HOST = os.getenv("ELASTIC_HOST")

    clt = lakefs.Client(
        host=LAKEFS_ENDPOINT_URL,
        username=LAKEFS_ACCESS_KEY_ID,
        password=LAKEFS_SECRET_ACCESS_KEY,
    )

    r = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
        username=REDIS_USERNAME,
        password=REDIS_PASSWORD,
    )

    r.ping()

    # Create the client instance
    es = Elasticsearch(
        ELASTIC_HOST,
        ssl_assert_fingerprint=ELASTIC_SSL_FINGERPRINT,
        basic_auth=("elastic", ELASTIC_PASSWORD),
    )

    if not es.ping():
        raise Exception("Could not connect to ElasticSearch")

    repo = None

    for _repo in lakefs.repositories(client=clt):
        if _repo.id == data.datasetProject:
            repo = _repo

    count = 0
    size = 0
    for o in repo.branch("main").objects():
        count += 1
        size += o.size_bytes

    # size = sum(1 for _ in src_bucket.objects.all())

    avg_size = 0

    try:
        avg_size = size / count
    except:
        avg_size = 0

    _data = {
        "total_items": count,
        "ingested_items": 0,
        "ingested_size": 0,
        "avg_size": avg_size,
        "total_size": size,
        "ingested_chunks": 0,
    }

    r.json().set(data.instanceId, ".", _data)

    resp = es.get(index="application", id=data.applicationId)
    application = resp["_source"]
    _pipeline = None
    _entry_step = None
    _first_step = None
    _second_step = None
    _final_step = None

    for p in application["pipelines"]:
        if p["id"] == data.selectedPipeline:
            _pipeline = p
            break

    for s in _pipeline["steps"]:
        if s["id"] == _pipeline["entry"]:
            _entry_step = s["id"]
            break

    for s in _pipeline["steps"]:
        if _entry_step in s["dependsOn"]:
            _first_step = s["id"]
            break

    for s in _pipeline["steps"]:
        if _first_step in s["dependsOn"]:
            _second_step = s["id"]
            break

    for s in _pipeline["steps"]:
        if _second_step in s["dependsOn"]:
            _final_step = s["id"]
            break

    instances = resp["_source"]["instances"]
    for instance in instances:
        if instance["id"] == data.instanceId:
            instance["status"] = "running"
            for pss in instance["pipelineStepStatuses"]:
                if pss["step"] == _entry_step:
                    pss["status"] = "completed"
                    pss["endTime"] = datetime.utcnow().isoformat()[:-3] + "Z"

                if pss["step"] == _first_step:
                    pss["status"] = "running"
                    pss["startTime"] = datetime.utcnow().isoformat()[:-3] + "Z"

    es.update(
        index="application",
        id=data.applicationId,
        body=json.dumps({"doc": {"instances": instances}}, default=vars),
    )

    chunks_as_json = []
    page_as_json = []
    findex = 0
    try:

        for object in repo.branch("main").objects():
            with repo.branch("main").object(object.path).reader(pre_sign=False) as fd:
                # while fd.tell() < file_size:
                #     print(fd.read(10))
                #     fd.seek(10, os.SEEK_CUR)
                file_chunks = get_file_elements_internal(
                    file=fd.read(), filepath=object.path
                )
                chunks_as_json.extend(file_chunks)
                r.json().numincrby(data.instanceId, ".ingested_size", object.size_bytes)
                r.json().numincrby(data.instanceId, ".ingested_items", 1)
                r.json().numincrby(
                    data.instanceId, ".ingested_chunks", len(file_chunks)
                )
            findex += 1
            if findex % 10 == 0:
                print(findex)

        res = r.json().get(data.instanceId)
        resp = es.get(index="application", id=data.applicationId)
        application = resp["_source"]
        instances = resp["_source"]["instances"]
        _pipeline = None

        for p in application["pipelines"]:
            if p["id"] == data.selectedPipeline:
                _pipeline = p

        for instance in instances:
            if instance["id"] == data.instanceId:
                instance["chartData"] = {
                    "totalItems": res["total_items"],
                    "ingestedItems": res["ingested_items"],
                    "avgSize": res["avg_size"],
                    "totalSize": res["total_size"],
                    "ingestedSize": res["ingested_size"],
                    "ingestedChunks": res["ingested_chunks"],
                }
                for pss in instance["pipelineStepStatuses"]:
                    if pss["step"] == _first_step:
                        pss["status"] = "completed"
                        pss["endTime"] = datetime.utcnow().isoformat()[:-3] + "Z"

                    if pss["step"] == _second_step:
                        pss["status"] = "running"
                        pss["startTime"] = datetime.utcnow().isoformat()[:-3] + "Z"

        es.update(
            index="application",
            id=data.applicationId,
            body=json.dumps({"doc": {"instances": instances}}, default=vars),
        )

        # Save the chunks_as_json.json on lakefs

        # pprint(chunks_as_json)
        print("Number of chunks " + str(len(chunks_as_json)))
        # payloads = json.load(chunks_as_json)
        await vectordb.recreate_collection(collection=data.datasetProject)
        await vectordb.insert_records(
            collection=data.datasetProject, payload_with_contents=chunks_as_json
        )

        res = r.json().get(data.instanceId)
        resp = es.get(index="application", id=data.applicationId)
        instances = resp["_source"]["instances"]
        for instance in instances:
            if instance["id"] == data.instanceId:
                instance["status"] = "completed"
                instance["endTime"] = datetime.utcnow().isoformat()[:-3] + "Z"
                instance["chartData"] = {
                    "totalItems": res["total_items"],
                    "ingestedItems": res["ingested_items"],
                    "avgSize": res["avg_size"],
                    "totalSize": res["total_size"],
                    "ingestedSize": res["ingested_size"],
                    "ingested_chunks": res["ingested_chunks"],
                }
                for pss in instance["pipelineStepStatuses"]:
                    if pss["step"] == _second_step:
                        pss["status"] = "completed"
                        pss["endTime"] = datetime.utcnow().isoformat()[:-3] + "Z"
                    if pss["step"] == _final_step:
                        pss["status"] = "running"
                        pss["startTime"] = datetime.utcnow().isoformat()[:-3] + "Z"

        es.update(
            index="application",
            id=data.applicationId,
            body=json.dumps({"doc": {"instances": instances}}, default=vars),
        )
    except Exception as e:
        print("Error")
        print(e)
        resp = es.get(index="application", id=data.applicationId)
        instances = resp["_source"]["instances"]
        for instance in instances:
            if instance["id"] == data.instanceId:
                instance["status"] = "failed"
                instance["endTime"] = datetime.utcnow().isoformat()[:-3] + "Z"
                instance["comment"] = e
                for pss in instance["pipelineStepStatuses"]:
                    if pss["endTime"] == None and pss["startTime"] != None:
                        pss["status"] = "failed"
                        pss["endTime"] = datetime.utcnow().isoformat()[:-3] + "Z"

        es.update(
            index="application",
            id=data.applicationId,
            body=json.dumps({"doc": {"instances": instances}}, default=vars),
        )
