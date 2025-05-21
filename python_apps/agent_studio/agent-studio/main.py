import os
import uuid
import dotenv
import fastapi
from datetime import datetime
from starlette.middleware.cors import CORSMiddleware

# Use local imports
from agents import agent_schemas
from agents.command_agent import CommandAgent
from prompts import command_agent_system_prompt
from db.database import Base, engine
from db.init_db import init_db
from api import prompt_router, agent_router

from contextlib import asynccontextmanager

# # Add the current directory to the Python path
# current_dir = os.path.dirname(os.path.abspath(__file__))
# if current_dir not in sys.path:
#     sys.path.append(current_dir)

dotenv.load_dotenv(".env.local")

CX_ID = os.getenv("CX_ID_PERSONAL")
GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")

fronted_agents = {
    "w": "WebAgent",
    "d": "DataAgent",
    "a": "APIAgent",
    "r": "CommandAgent",
    "h": "HelloWorldAgent",
    "c": "ConsolePrinterAgent",
}

COMMAND_AGENT = None

origins = ["http://127.0.0.1:3002", "*"]


@asynccontextmanager
async def lifespan(app_instance: fastapi.FastAPI):
    Base.metadata.create_all(bind=engine)
    init_db()
    yield

    pass


app = fastapi.FastAPI(title="Agent Studio Backend", version="0.1.0", lifespan=lifespan)

app.include_router(prompt_router)
app.include_router(agent_router)


@app.get("/")
def status():
    return {"status": "ok"}


@app.get("/hc")
def health_check():
    return {"status": "ok"}


@app.post("/deploy")
def deploy(request: dict):
    global COMMAND_AGENT
    print(request)
    try:
        agents = []
        for i in request["agents"]:
            print(i[0])
            agents.append(fronted_agents[i[0]])
        connections = []
        for i in request["connections"]:
            print(i)
            connection = i.split("->")
            print(fronted_agents[connection[0]] == "CommandAgent")
            if fronted_agents[connection[0]] == "CommandAgent":
                print("Connection: ", connection[-1])
                connections.append(agent_schemas[fronted_agents[connection[-1]]])
        COMMAND_AGENT = CommandAgent(
            name="WebCommandAgent",
            agent_id=uuid.uuid4(),
            system_prompt=command_agent_system_prompt,
            persona="Command Agent",
            functions=connections,
            #    functions=[tool_schemas["add_numbers"]],
            routing_options={
                "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
                "respond": "If you think you have the answer, you can stop here.",
                "give_up": "If you think you can't answer the query, you can give up and let the user know.",
            },
            short_term_memory=True,
            long_term_memory=False,
            reasoning=False,
            input_type=["text", "voice"],
            output_type=["text", "voice"],
            response_type="json",
            max_retries=5,
            timeout=None,
            deployed=False,
            status="active",
            priority=None,
            failure_strategies=["retry", "escalate"],
            session_id=None,
            last_active=datetime.now(),
            collaboration_mode="single",
        )

        return {"status": "response: ok"}
    except Exception as e:
        print(e)
        return {"status": f"Error: {e}"}


@app.post("/run")
def run(request: dict):
    if COMMAND_AGENT is not None:
        res = COMMAND_AGENT.execute(query=request["query"])

        return {"status": "ok", "response": f"{res}"}


@app.post("/run_stream")
def run_stream(request: dict):
    chat_history = request["chat_history"]
    print("Chat History: ", chat_history)
    print("*" * 10)
    gpt_chat_history = ""

    for i in chat_history[:-1]:
        gpt_chat_history += f"{i['actor']}: {i['content']}\n"

    async def response_stream():
        if COMMAND_AGENT is not None:
            for chunk in COMMAND_AGENT.execute_stream(
                request["query"], gpt_chat_history
            ):
                yield chunk
            return

    return fastapi.responses.StreamingResponse(
        response_stream(), media_type="text/event-stream"
    )


if __name__ == "__main__":
    import uvicorn

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
    )

    uvicorn.run(app, host="localhost", port=8000)
