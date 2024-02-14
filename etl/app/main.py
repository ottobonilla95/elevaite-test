from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
import uvicorn
from app.routers.applications import router as applications_router

from app.util.RedisSingleton import RedisSingleton
from app.util.elastic_seed import HelloElastic
from app.util.ElasticSingleton import ElasticSingleton
from app.db import models
from app.db.database import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    logging.info("Initializing...")
    redis = RedisSingleton()
    elastic = ElasticSingleton()
    yield
    # Add here code that runs when the service shuts down


models.Base.metadata.create_all(bind=engine)

app = FastAPI(lifespan=lifespan)

app.include_router(applications_router)


@app.get("/hc")
def healthCheck():
    return {"Hello": "World"}


@app.post("/helloelastic")
def helloElastic():
    print("Starting ElasticSearch")
    HelloElastic()
    return {}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
