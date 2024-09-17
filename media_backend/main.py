from fastapi import FastAPI, HTTPException
from model import InferencePayload
from llm_rag_inference import perform_inference
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3004",  # Your frontend URL
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Allows requests from this origin
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/")
async def post_message(inference_payload: InferencePayload):
    try:
        return perform_inference(inference_payload)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)