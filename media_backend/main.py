from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from model import InferencePayload
from llm_rag_inference import perform_inference
from fastapi.responses import StreamingResponse
import json

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

# Serves the static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/")
async def post_message(inference_payload: InferencePayload):
    try:
        async def event_generator():
            async for chunk in perform_inference(inference_payload):
                yield f"data: {json.dumps(chunk)}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)