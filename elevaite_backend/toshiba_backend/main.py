from fastapi import FastAPI, Request, Body
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from datetime import datetime
from contextlib import asynccontextmanager
from agents import toshiba_agent
from data_classes import SessionObject, MessageObject
from utils import convert_messages_to_chat_history
import dotenv
import os
from shared_state import session_status, update_status, get_status
import uuid
from database_connection import ChatRequest, DatabaseConnection
from pydantic import BaseModel
from shared_state import database_connection
from query_reformulator import reformulate_query_final
dotenv.load_dotenv(".env")



CX_ID = os.getenv("CX_ID_PERSONAL")
GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")


origins = [
    "http://127.0.0.1:3002",
    "*"
    ]



@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize the database
    try:
        await database_connection.init_db()
        print("Database initialized successfully")
    except Exception as e:
        print(f"Failed to initialize database: {str(e)}")
        # You might want to exit the application here if DB init is critical
        # import sys
        # sys.exit(1)

    yield

    # Shutdown: clean up resources
    try:
        await database_connection.close_db()
    except Exception as e:
        print(f"Error during application shutdown: {str(e)}")

app = FastAPI(title="Agent Studio Backend", version="0.1.0", lifespan=lifespan)

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
            yield f"data: Processing...\n\n"


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

@app.post("/run")
async def run(request: Request):
    """
    Endpoint to run the Toshiba agent and stream responses back to the frontend.
    """
    # Parse the JSON body
    data = await request.json()
    print(data)

    start_time = datetime.now()
    await update_status(data.get("uid"), "Reformulating query...")
    try:
        query = reformulate_query_final(data.get("query"))
    except Exception as e:
        print(f"Error reformulating query: {str(e)}")
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

    async def response_generator():
        agent_flow_id = str(uuid.uuid4())
        full_response = ""
        try:
            async for chunk in toshiba_agent.execute3(query=query,qid= data.get("qid"), session_id=data.get("sid"), chat_history=chat_history, user_id=user_id, agent_flow_id=agent_flow_id):
                if chunk:
                    if isinstance(chunk, dict):
                        await update_status(user_id, chunk[user_id])
                        await asyncio.sleep(0.1)
                        continue

                    full_response += chunk
                    yield f"{chunk if isinstance(chunk, str) else ''}"
            # yield "Hi."

        except Exception as e:
            error_msg = f"Error during streaming: {str(e)}"
            print(error_msg)
            yield f"{json.dumps({'error': error_msg})}\n\n"
        finally:
            # Safely convert string IDs to UUIDs with validation
            try:
                qid = data.get("qid")
                sid = data.get("sid")

                # Validate and convert qid
                if qid and isinstance(qid, str):
                    qid_uuid = uuid.UUID(qid)
                else:
                    # Generate a new UUID if qid is missing or invalid
                    qid_uuid = uuid.uuid4()
                    print(f"Generated new qid: {qid_uuid}")

                # Validate and convert sid
                if sid and isinstance(sid, str):
                    try:
                        sid_uuid = uuid.UUID(sid)
                    except ValueError:
                        # Generate a new UUID if sid is not a valid UUID string
                        sid_uuid = uuid.uuid4()
                        print(f"Invalid sid format, generated new sid: {sid_uuid}")
                else:
                    # Generate a new UUID if sid is missing
                    sid_uuid = uuid.uuid4()
                    print(f"Missing sid, generated new sid: {sid_uuid}")

                # Use timezone-naive datetime for request_timestamp and response_timestamp
                current_time_naive = datetime.now()

                data_log = ChatRequest(
                    qid=qid_uuid,
                    session_id=sid_uuid,
                    request=query,
                    user_id=user_id,
                    request_timestamp=start_time,
                    response=full_response,
                    response_timestamp=current_time_naive,
                    agent_flow_id=agent_flow_id
                )
                print("Data Log: ",data_log)
                try:
                    success = await database_connection.save_chat_request(data_log)
                    if success:
                        print("Chat request saved to database successfully")
                    else:
                        print("Failed to save chat request to database")
                except Exception as e:
                    print(f"Unexpected error saving chat request: {str(e)}")
            except Exception as e:
                print(f"Error preparing chat request data: {str(e)}")

    # Return the streaming response
    return StreamingResponse(
        response_generator(),
        media_type="text/event-stream",
        headers={
            "Content-Type": "text/event-stream",
            "Cache-Control": "no-cache no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Transfer-Encoding": "chunked"
        }
    )


# Vote model for the API endpoint
class VoteRequest(BaseModel):
    message_id: str
    user_id: str
    vote: int
    session_id: str

# Feedback model for the API endpoint
class FeedbackRequest(BaseModel):
    message_id: str
    user_id: str
    feedback: str
    session_id: str

@app.post("/vote")
async def update_vote(vote_request: VoteRequest = Body(...)):
    """Update the vote for a message in the database."""
    try:
        # Validate and convert message_id to UUID
        try:
            message_id = uuid.UUID(vote_request.message_id)
        except ValueError:
            return {"message": f"Invalid message_id format: {vote_request.message_id}"}

        # Validate and convert session_id to UUID
        try:
            session_id = uuid.UUID(vote_request.session_id)
        except ValueError:
            return {"message": f"Invalid session_id format: {vote_request.session_id}"}

        # Call the dedicated update_vote function
        success = await database_connection.update_vote(
            message_id=message_id,
            user_id=vote_request.user_id,
            vote=vote_request.vote,
            session_id=session_id
        )

        if success:
            return {"message": "Vote updated successfully"}
        else:
            return {"message": "Failed to update vote"}
    except Exception as e:
        error_type = type(e).__name__
        print(f"Error updating vote: {error_type} - {str(e)}")
        return {"message": f"Error updating vote: {str(e)}"}

@app.post("/feedback")
async def update_feedback(feedback_request: FeedbackRequest = Body(...)):
    """Update the feedback for a message in the database."""
    try:
        # Validate and convert message_id to UUID
        try:
            message_id = uuid.UUID(feedback_request.message_id)
        except ValueError:
            return {"message": f"Invalid message_id format: {feedback_request.message_id}"}

        # Validate and convert session_id to UUID
        try:
            session_id = uuid.UUID(feedback_request.session_id)
        except ValueError:
            return {"message": f"Invalid session_id format: {feedback_request.session_id}"}

        # Call the dedicated update_feedback function
        success = await database_connection.update_feedback(
            message_id=message_id,
            user_id=feedback_request.user_id,
            feedback=feedback_request.feedback,
            session_id=session_id
        )

        if success:
            return {"message": "Feedback updated successfully"}
        else:
            return {"message": "Failed to update feedback"}
    except Exception as e:
        error_type = type(e).__name__
        print(f"Error updating feedback: {error_type} - {str(e)}")
        return {"message": f"Error updating feedback: {str(e)}"}

@app.get("/pastSessions")
async def get_past_sessions(request: Request):
    print("Getting past sessions")
    print("Request: ", request)
    sessions = set(await database_connection.get_past_sessions(request.query_params.get("uid")))
    past_sessions = []
    for session in sessions:
        res = await database_connection.get_session_messages(session)
        messages = []
        for r in res:
            messages.append(
                MessageObject(id=uuid.uuid4(), userName=r.user_id, isBot=False, text=r.request, date=r.request_timestamp))
            messages.append(
                MessageObject(id=r.qid, userName="ElevAIte", isBot=True, text=r.response, date=r.response_timestamp,
                              vote=r.vote, feedback=r.feedback))
        session_info = SessionObject(id=session, label=res[0].response[:20], creationDate=res[0].request_timestamp,
                                     messages=messages)
        past_sessions.append(session_info)
    await database_connection.close_db()
    return past_sessions

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