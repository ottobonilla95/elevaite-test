from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
import pika
import uvicorn
from app.routers.applications import router as applications_router

from app.util.flowTest import HelloFlow
from app.util.argoTest import create_test_workflow
from app.util.RedisSingleton import RedisSingleton
from app.util.RabbitMQSingleton import RabbitMQSingleton
from app.util.elastic_seed import HelloElastic
from app.util.ElasticSingleton import ElasticSingleton


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    logging.info("Initializing...")
    rabbit = RabbitMQSingleton()
    rabbit.channel.queue_declare(queue="s3_ingest")
    redis = RedisSingleton()
    elastic = ElasticSingleton()
    yield
    # Add here code that runs when the service shuts down
    rabbit.connection.close()


app = FastAPI(lifespan=lifespan)

app.include_router(applications_router)


@app.get("/hc")
def healthCheck():
    return {"Hello": "World"}


@app.post("/helloflow")
def helloFlow():
    print("Starting MetaFlow")
    HelloFlow()
    return {}


@app.post("/helloargo")
def helloArgo():
    print("Starting Argo Workflows")
    res = create_test_workflow()
    return {"res": res}


@app.post("/helloelastic")
def helloElastic():
    print("Starting ElasticSearch")
    HelloElastic()
    return {}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
