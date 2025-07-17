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
from database_connection import ChatRequest
from pydantic import BaseModel
from shared_state import database_connection
from query_reformulator import reformulate_query_final
from extract_sources import extract_sources_from_text
from add_columns import add_columns
import pandas as pd
from openai import AsyncOpenAI

if not os.getenv("KUBERNETES_SERVICE_HOST"):
    dotenv.load_dotenv(".env")


CX_ID = os.getenv("CX_ID_PERSONAL")
GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")


origins = ["http://127.0.0.1:3002", "*"]


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


app = FastAPI(
    title="Agent Studio Backend",
    version="0.1.0",
    lifespan=lifespan,
    root_path="/api/core",
    docs_url="/docs",
)

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
            "X-Accel-Buffering": "no",
        },
    )


@app.post("/run")
async def run(request: Request):
    """
    Endpoint to run the Toshiba agent and stream responses back to the frontend.
    """
    # Parse the JSON body
    data = await request.json()
    print(data)
    original_query = data.get("query")

    start_time = datetime.now()
    # Convert messages to chat history format if needed
    chat_history = data.get("messages", [])

    if chat_history:
        chat_history = convert_messages_to_chat_history(chat_history)
        # Remove the last message if it exists (likely the current query)
        if chat_history:
            chat_history = chat_history[:-1]
    else:
        chat_history = []
    await update_status(data.get("uid"), "Reformulating query...")

    try:
        query = reformulate_query_final(original_query, chat_history)
    except Exception as e:
        print(f"Error reformulating query: {str(e)}")
        query = data.get("query")
    user_id = data.get("uid")

    if not query:
        return {"error": "No query provided"}

    if not user_id:
        return {"error": "No user ID provided"}

    print(f"Time taken for request processing: {datetime.now() - start_time}")

    async def response_generator():
        agent_flow_id = str(uuid.uuid4())
        full_response = ""
        try:
            print("Query: ", query)
            async for chunk in toshiba_agent.execute3(
                query=query,
                qid=data.get("qid"),
                session_id=data.get("sid"),
                chat_history=chat_history,
                user_id=user_id,
                agent_flow_id=agent_flow_id,
            ):
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
                print("Current Time Naive: ", current_time_naive)

                data_log = ChatRequest(
                    qid=qid_uuid,
                    session_id=sid_uuid,
                    request=query,
                    original_request=original_query,
                    user_id=user_id,
                    request_timestamp=start_time,
                    response=full_response,
                    response_timestamp=current_time_naive,
                    agent_flow_id=agent_flow_id,
                    sr_ticket_id=""
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
    start_time = datetime.now()
    user_id = request.query_params.get("uid")

    # Get sessions in a single database call
    sessions = set(await database_connection.get_past_sessions(user_id))

    # Use gather to fetch all session messages concurrently
    session_results = await asyncio.gather(
        *(database_connection.get_session_messages(session) for session in sessions)
    )

    past_sessions = []
    for res in session_results:
        if not res:  # Skip empty results
            continue

        messages = []
        # Process all messages in a session at once
        for r in res:
            # Add user message
            # print("Response: ", r.response)
            sources = await extract_sources_from_text(r.response)
            # print("Sources: ", sources)
            messages.append(
                MessageObject(
                    id=uuid.uuid4(),
                    userName=r.user_id,
                    isBot=False,
                    text=r.request,
                    date=r.request_timestamp,
                )
            )
            # Add bot message
            messages.append(
                MessageObject(
                    id=r.qid,
                    userName="ElevAIte",
                    isBot=True,
                    text=r.response,
                    date=r.response_timestamp,
                    vote=r.vote,
                    feedback=r.feedback,
                    sources=sources,
                )
            )

        # Create session object
        session_info = SessionObject(
            id=res[0].session_id,
            label=(
                res[-1].response[:30] + "..."
                if str(res[0].sr_ticket_id) != "BE"
                else "Batch Evaluation"
            ),
            creationDate=res[0].request_timestamp,
            messages=messages,
        )
        past_sessions.append(session_info)

    # Don't close the connection here as it might be needed elsewhere
    # Let the lifespan handler manage connection closing
    print(f"Time taken for fetching past sessions: {datetime.now() - start_time}")
    return past_sessions


@app.post("/batchEvaluation")
async def batch_evaluation(request: Request):
    session_info = SessionObject(
        id=uuid.uuid4(),
        label="Batch Evaluation",
        creationDate=datetime.now(),
        messages=[
            MessageObject(
                id=uuid.uuid4(),
                userName="User",
                isBot=False,
                text="Batch evaluation completed",
                date=datetime.now(),
            ),
            MessageObject(
                id=uuid.uuid4(),
                userName="ElevAIte",
                isBot=True,
                text="Please refresh the page to view the results.",
                date=datetime.now(),
            ),
        ],
    )
    # yield session_info
    print("Processing batch file")
    print("Request: ", request)
    # try:
    form = await request.form()
    print("Form: ", form)
    file = form["file"]
    print("File: ", file)
    df = pd.read_excel(file.file)
    # Process the file and save the results to the database
    # This is a placeholder for the actual implementation
    print(df.head())
    print("Processing batch file:", file)
    session_id = uuid.uuid4()
    user_id = form["user_id"]
    print("User ID: ", user_id)
    response_counter = 0
    source_counter = 0
    for index, row in df.iterrows():
        request_timestamp = datetime.now()
        print(row)
        print("Question: ", row["Question"])
        print("Answer: ", row["Answer"])
        print("Sources: ", row["Source"])
        qid = uuid.uuid4()
        user_id = user_id
        agent_flow_id = uuid.uuid4()
        chat_history = []
        original_query = row["Question"]
        try:
            query = reformulate_query_final(original_query)
        except Exception as e:
            print(f"Error reformulating query: {str(e)}")
            query = original_query
        response = toshiba_agent.execute(query=query,qid=qid, session_id=session_id, chat_history=chat_history, user_id=user_id, agent_flow_id=agent_flow_id)
        print("Response: ", response)
        sources = await extract_sources_from_text(response)
        print("Sources: ", sources)
        await asyncio.sleep(1)
        # Evaluate if the response and the sources are correct using llm

        response_prompt = f"""
        Evaluate if the response generated by the Toshiba agent and the sources cited are correct.
        Sources are correct if any of the sources cited are correct. That is, if the desired source is present in any of the sources cited, the sources are correct.
        Question: {row["Question"]}
        Correct Answer: {row["Answer"]}
        Correct Sources: {row["Source"]}
        Response Generated by the Agent including the sources: {response}
        
        Output in JSON format:
        {{
            "is_response_correct": <True/False>,
            "is_sources_correct": <True/False>,
            "feedback": "<Your feedback to the agent>"
        }}
        """

        eval_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        eval_response = await eval_client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": "You are an evaluator."},
                {"role": "user", "content": response_prompt}
            ],
            temperature=0.6,
            response_format={"type": "json_object"},
            max_tokens=2000,
            stream=False,
        )
        evaluation = eval_response.choices[0].message.content

        # Read evaluation json
        evaluation = json.loads(evaluation)
        if evaluation["is_response_correct"]:
            response_counter += 1
        if evaluation["is_sources_correct"]:
            source_counter += 1

        response = response + "\n\nEvaluation: \n\n" + "Is Response Correct: " + \
                   str(evaluation["is_response_correct"]) + "\n\n" + "Is Sources Correct: " +\
                   str(evaluation["is_sources_correct"]) + "\n\n" + "Feedback: " + evaluation["feedback"] +\
                   "\n\n" + "Response Counter: " + str(response_counter)+" / " + str(index+1) + \
                   "\n\n" + "Source Counter: " + str(source_counter) + " / " + str(index+1)

        data_log = ChatRequest(
            qid=qid,
            session_id=session_id,
            request=query,
            original_request=original_query,
            user_id=user_id,
            request_timestamp=request_timestamp,
            response=response,
            response_timestamp=datetime.now(),
            agent_flow_id=agent_flow_id,
            sr_ticket_id="BE"
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
    return session_info


    # except Exception as e:
    #     return {"message": f"Error processing batch file: {str(e)}"}

if __name__ == "__main__":
    asyncio.run(add_columns())
    import uvicorn

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    uvicorn.run(app, host="0.0.0.0", port=8000)
