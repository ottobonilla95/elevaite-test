from typing import Any

import dotenv
import os
import fastapi
import uuid
from datetime import datetime
from agents import CommandAgent, agent_schemas
from prompts import command_agent_system_prompt
from tools import tool_schemas
from starlette.middleware.cors import CORSMiddleware
from agents import toshiba_agent
import json


dotenv.load_dotenv(".env.local")

CX_ID = os.getenv("CX_ID_PERSONAL")
GOOGLE_API = os.getenv("GOOGLE_API_PERSONAL")

fronted_agents = {
    'w' : 'WebAgent',
    'd' : 'DataAgent',
    'a' : 'APIAgent',
    'r' : 'CommandAgent'

}

COMMAND_AGENT = CommandAgent(name="WebCommandAgent",
                                             agent_id=uuid.uuid4(),
                                             system_prompt=command_agent_system_prompt,
                                             persona="Command Agent",
                                             functions=[agent_schemas["ToshibaAgent"]],
                                                # functions=[tool_schemas["get_knowledge"]],
                                             routing_options={
                                                 "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
                                                 "respond": "If you think you have the answer, you can stop here.",
                                                 "give_up": "If you think you can't answer the query, you can give up and let the user know."
                                                 },

                                             short_term_memory=True,
                                             long_term_memory=False,
                                             reasoning=False,
                                             # input_type=["text", "voice"],
                                             # output_type=["text", "voice"],
                                             response_type="json",
                                             max_retries=5,
                                             timeout=None,
                                             deployed=False,
                                             status="active",
                                             priority=None,
                                             failure_strategies=["retry", "escalate"],
                                             session_id=None,
                                             last_active=datetime.now(),
                                            active_agents=[],
                                             collaboration_mode="single",
                                             )

origins = [
    "http://127.0.0.1:3002",
    "*"
    ]
app = fastapi.FastAPI(title="Agent Studio Backend", version="0.1.0")

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
            if fronted_agents[connection[0]] == "CommandAgent":
                connections.append(agent_schemas[fronted_agents[connection[-1]]])
        COMMAND_AGENT = CommandAgent(name="WebCommandAgent",
                                             agent_id=uuid.uuid4(),
                                             system_prompt=command_agent_system_prompt,
                                             persona="Command Agent",
                                             functions=connections,
                                             #    functions=[tool_schemas["add_numbers"]],
                                             routing_options={
                                                 "continue": "If you think you can't answer the query, you can continue to the next tool or do some reasoning.",
                                                 "respond": "If you think you have the answer, you can stop here.",
                                                 "give_up": "If you think you can't answer the query, you can give up and let the user know."
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
                                             collaboration_mode="single"
                                             )

        return {"status": f"response: ok"}
    except Exception as e:
        return {"status": f"Error: {e}"}

@app.get("/run")
def run(request: fastapi.Request):
    query = request.query_params.get("query")
    # res = json.loads(toshiba_agent.execute(query=query))["content"]
    res = "Part number is 1234567890"
    # res = COMMAND_AGENT.execute(query)
    return {"text": f"{res}", "refs": ["https://www.google.com"], "media": ["https://fastly.picsum.photos/id/13/2500/1667.jpg?hmac=SoX9UoHhN8HyklRA4A3vcCWJMVtiBXUg0W4ljWTor7s",
                                                                              "https://picsum.photos/seed/picsum/200/300",
                                                                              "https://www.w3schools.com/html/mov_bbb.mp4"]}
    # res = json.loads(toshiba_agent.execute(query=query))["content"]
    # print(res)
    # response = {"text": f"{res}", "refs": ["https://www.google.com"]}
    # return response


if __name__ == "__main__":
    import uvicorn

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
        allow_headers=['Content-Type', 'Authorization'],
    )

    uvicorn.run(app, host="localhost", port=8000)
