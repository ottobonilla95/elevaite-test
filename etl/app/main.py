from fastapi import FastAPI
import uvicorn
from app.routers.applications import router as applications_router

from app.util.flowTest import HelloFlow
from app.util.argoTest import create_test_workflow


app = FastAPI()

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
def helloFlow():
    print("Starting Argo Workflows")
    res = create_test_workflow()
    return {"res": res}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
