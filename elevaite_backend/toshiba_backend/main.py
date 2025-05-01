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
from utils import convert_messages_to_chat_history
from fastapi.responses import StreamingResponse


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

@app.post("/run")
def run(request: dict):
    start_time = datetime.now()
    refs = []
    media = []
    query = request.get("query")
    chat_history = request.get("messages")
    if chat_history:
        chat_history = convert_messages_to_chat_history(chat_history)
    else:
        chat_history = []
    chat_history.pop(-1)
    answer = toshiba_agent.execute2(query=query, chat_history=chat_history)
    # print(answer)

    try:
        content = json.loads(answer)["content"]
        res = content["Answer"]
        if content.get("References"):
            for i in content.get("References"):
                refs.append("Page: "+str(i["Page number"])+" File: "+str(i["Filename"]))
    except:
        res = answer
    print("Time taken by the backend: ",datetime.now()-start_time)
    return {"text": f"{res}", "refs": refs, "media": media}
#  Table structure: table: header, columns, row values, each column must have same number of rows.
# table: json format: {"header":"XYZ", column_labels: ["A", "B", "C"], "rows": [[1, 2, 3], [4, 5, 6], [7, 8, 9]]}
# alternative: {"header":"XYZ" optional, values:[ object, object, object]}; Each object has label and values
# object.label = "A", object.values = [1,2,3]
#  Send example object to Thanos. For tables and sources pills



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
