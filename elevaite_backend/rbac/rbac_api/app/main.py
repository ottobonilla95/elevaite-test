
from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
import logging
from rbac_api.utils.RedisSingleton import RedisSingleton
from fastapi import FastAPI, Depends
from rbac_api.app.routes.main import attach_routes
import uvicorn
from elevaitedb.db.database import engine
from elevaitedb.db import models
from rbac_api.utils.seed_db import seed_db as seed
from rbac_api.utils.deps import get_db
from sqlalchemy.orm import Session

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(override = True)
    logging.info("Initializing...")
    redis = RedisSingleton()
    yield


app = FastAPI()
models.Base.metadata.create_all(bind=engine)
# Attach all routes to the app
attach_routes(app)

@app.get("/hc", tags=["testing"])
def healthCheck():
    return {"msg": "Hello World"}

@app.post("/seed", tags=["testing"])
def seed_db(db: Session = Depends(get_db)):
    load_dotenv()
    seed(db)
    return {"msg": "DB seeded"}
# This block is only necessary if you want to run the server with `python main.py`
# In production, you should use Uvicorn or Gunicorn with Uvicorn workers from the command lineif __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9005)
