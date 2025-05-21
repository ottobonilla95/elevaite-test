import os
import uuid
import dotenv
import fastapi
from datetime import datetime
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Use local imports
from agents import agent_schemas
from agents.command_agent import CommandAgent
from prompts import command_agent_system_prompt
from db.database import Base, engine, get_db
from db.init_db import init_db
from api import prompt_router, agent_router
from db import crud

from contextlib import asynccontextmanager

# # Add the current directory to the Python path
# current_dir = os.path.dirname(os.path.abspath(__file__))
# if current_dir not in sys.path:
#     sys.path.append(current_dir)

dotenv.load_dotenv(".env.local")

CX_ID = os.getenv("CX_ID_PERSONAL")
GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")

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


@app.get("/deployment/codes")
def get_deployment_codes(db: Session = fastapi.Depends(get_db)):
    """
    Get a mapping of deployment codes to agent names.
    This endpoint is used by the frontend to display available agents.
    """
    available_agents = crud.get_available_agents(db)

    code_map = {}
    for agent in available_agents:
        deployment_code = getattr(agent, "deployment_code", None)
        if deployment_code is not None and str(deployment_code).strip() != "":
            code_map[str(deployment_code)] = str(agent.name)

    return code_map


@app.post("/deploy")
def deploy(request: dict, db: Session = fastapi.Depends(get_db)):
    global COMMAND_AGENT
    print(request)
    try:
        agents = []
        for i in request["agents"]:
            code = i[0]
            db_agent = crud.get_agent_by_deployment_code(db, code)
            if db_agent is None:
                return {
                    "status": f"Error: Agent with deployment code '{code}' not found"
                }
            agents.append(str(db_agent.name))

        connections = []
        for i in request["connections"]:
            connection = i.split("->")
            source_code = connection[0]
            target_name = connection[-1]

            source_agent = crud.get_agent_by_deployment_code(db, source_code)
            if source_agent is None:
                return {
                    "status": f"Error: Agent with deployment code '{source_code}' not found"
                }
            source_name = str(source_agent.name)

            if source_name == "CommandAgent":
                if target_name in agent_schemas:
                    connections.append(agent_schemas[target_name])
                else:
                    target_agent = crud.get_agent_by_name(db, target_name)
                    if (
                        target_agent is not None
                        and str(target_agent.name) in agent_schemas
                    ):
                        connections.append(agent_schemas[str(target_agent.name)])

        COMMAND_AGENT = CommandAgent(
            name="WebCommandAgent",
            agent_id=uuid.uuid4(),
            system_prompt=command_agent_system_prompt,
            persona="Command Agent",
            functions=connections,
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
