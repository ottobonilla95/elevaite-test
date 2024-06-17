from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv
from fastapi import Depends, FastAPI
import uvicorn
from sqlalchemy.orm import Session

# from app.routers.applications import router as applications_router
from app.routers.instances import router as instances_router
from app.routers.configurations import router as configuration_router
from app.routers.datasets import router as datasets_router
from app.routers.collections import router as collections_router
from app.routers.service_now import router as service_now_router
from app.routers.pipelines import router as pipelines_router

from app.util.RedisSingleton import RedisSingleton
from app.util.ElasticSingleton import ElasticSingleton
from elevaitelib.orm.db import models
from elevaitelib.orm.db.database import engine

# from app.util.db_seed import seed_db
from elevaitelib.schemas import application as application_schemas
from app.routers.deps import get_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv()
    logging.info("Initializing...")
    redis = RedisSingleton()
    elastic = ElasticSingleton()
    yield
    # Add here code that runs when the service shuts down


# models.Base.metadata.create_all(bind=engine)

app = FastAPI(lifespan=lifespan)

# app.include_router(applications_router)
app.include_router(pipelines_router)
app.include_router(instances_router)
app.include_router(configuration_router)
app.include_router(datasets_router)
# app.include_router(projects_router)
app.include_router(collections_router)
app.include_router(service_now_router)


@app.get("/hc")
def healthCheck():
    return {"Hello": "World"}


# @app.post("/seed", response_model=list[application_schemas.Application])
# def seed(
#     db: Session = Depends(get_db),
# ) -> list[application_schemas.Application]:
#     return seed_db(db=db)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
