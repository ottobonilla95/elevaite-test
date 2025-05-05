from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from typing import Dict, List, Any, AsyncGenerator
from datetime import datetime
from agents import toshiba_agent
from utils import convert_messages_to_chat_history
import dotenv
import os
from shared_state import session_status, update_status, get_status

dotenv.load_dotenv(".env")

CX_ID = os.getenv("CX_ID_PERSONAL")
GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")

TEST_TEXT = """
The Bulk Coin Recycler (BCR) is a component of the Toshiba 6800 Self Checkout System 7, specifically located within the cash cabinet unit. It is responsible for handling coin transactions, including the recycling of coins for future use. 
| Identifier | Part Name ||------------|-------------------------|
| A | Coin input/output chute |
| B | Coin validator (acceptor) |
| C | Coin hoppers |
| D | Hopper tray door |

6800 Hardware Service Guide (2).pdf, Page 41, 6800 Hardware Service Guide (2).pdf, Page 264
"""


origins = [
    "http://127.0.0.1:3002",
    "*"
    ]
app = FastAPI(title="Agent Studio Backend", version="0.1.0")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def status():
    return {"status": "ok"}
@app.get("/hc")
def health_check():
    return {"status": "ok"}
# Your existing endpoint for status updates
@app.get("/currentStatus")
async def get_current_status(uid: str, sid: str):
    """Endpoint to report real-time agent status updates based on actual processing."""
    print("uid", uid)
    print("sid", sid)
    print("session_status", session_status)

    async def status_generator():
        print("uid in generator", uid)
        print("sid in generator", sid)
        print("session_status", session_status)
        if uid not in session_status:
            await update_status(uid, "Processing...")


        last_status = None
        counter = 0
        while True:
            current_status = await get_status(uid)
            counter += 1

            # Only send updates when status changes
            if current_status != last_status:
                yield f"data: {current_status}\n\n"
                last_status = current_status

            # Short polling interval
            await asyncio.sleep(0.1)

            # If status indicates completion, finish the stream
            if counter > 100:
                break

    return StreamingResponse(
        status_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


# Your main streaming response endpoint
# @app.post("/run2")
# async def stream_response(request: Request):
#     """Endpoint that returns a streaming response for chatbot messages."""
#     # Parse the request body
#     data = await request.json()
#
#     # Extract request parameters
#     query = data.get("query", "")
#     user_id = data.get("uid", "")
#     session_id = data.get("sid", "")
#     message_history = data.get("messages", [])
#     collection = data.get("collection", "")
#     session_id = "sessionId_0"
#
#     # Create a streaming generator
#     async def generate_chatbot_response() -> AsyncGenerator[str, None]:
#         # This is where you would implement your actual chatbot logic
#         # For example, call an LLM API or process the query
#
#         # For demonstration purposes, simulating a streaming response
#         # In a real implementation, you would stream tokens from your LLM
#         response_parts = [
#             "I'm ",
#             "thinking ",
#             "about ",
#             "your ",
#             "question ",
#             "regarding ",
#             f"{query}. ",
#             "Here's ",
#             "what ",
#             "I ",
#             "found: ",
#             "The answer ",
#             "to your ",
#             "question ",
#             "is that ",
#             "streaming ",
#             "responses ",
#             "provide ",
#             "a much ",
#             "better ",
#             "user ",
#             "experience ",
#             "for ",
#             "chatbots!"
#         ]
#
#         for part in response_parts:
#             # Format each chunk as a Server-Sent Event
#             yield f"data: {part}\n\n"
#             print(session_status)
#             await update_status(user_id, part)
#             # Simulate processing time
#             await asyncio.sleep(1)
#
#     # Return the streaming response with appropriate headers
#     return StreamingResponse(
#         generate_chatbot_response(),
#         media_type="text/event-stream",
#         headers={
#             "Content-Type": "text/event-stream",
#             "Cache-Control": "no-cache",
#             "Connection": "keep-alive",
#             "X-Accel-Buffering": "no"
#         },
#     )


@app.post("/run")
async def run(request: Request):
    """
    Endpoint to run the Toshiba agent and stream responses back to the frontend.
    """
    # Parse the JSON body
    data = await request.json()

    start_time = datetime.now()
    query = data.get("query")
    user_id = data.get("uid")
    chat_history = data.get("messages", [])

    if not query:
        return {"error": "No query provided"}

    if not user_id:
        return {"error": "No user ID provided"}

    # Convert messages to chat history format if needed
    if chat_history:
        chat_history = convert_messages_to_chat_history(chat_history)
        # Remove the last message if it exists (likely the current query)
        if chat_history:
            chat_history = chat_history[:-1]
    else:
        chat_history = []

    print(f"Time taken for request processing: {datetime.now() - start_time}")

    # Define the streaming generator function
    async def response_generator():
        # yield TEST_TEXT
        # return
        try:
            async for chunk in toshiba_agent.execute3(query=query, chat_history=chat_history, user_id=user_id):
                if chunk:
                    if isinstance(chunk, dict):
                        await update_status(user_id, chunk[user_id])
                        await asyncio.sleep(0.1)

                    yield f"{chunk if isinstance(chunk, str) else ''}"

            # Send a completion signal
            # yield f"<END>"

        except Exception as e:
            error_msg = f"Error during streaming: {str(e)}"
            print(error_msg)
            yield f"{json.dumps({'error': error_msg})}\n\n"

    # Return the streaming response
    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


if __name__ == "__main__":
    import uvicorn

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization'],
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)