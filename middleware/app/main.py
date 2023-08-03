from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from sse_starlette.sse import EventSourceResponse
import os
from dotenv import load_dotenv
import json
from langchain.callbacks.manager import AsyncCallbackManager
import openai
from .utils.callback import MyCustomCallbackHandler
from .utils.email_util.email_parser import EmailConversationParser

from collections import defaultdict
from .utils.email_util.email_parser import EmailConversationParser

# file imports
from .utils.incidentScoringChain import func_incidentScoringChain
from .utils._global import llm
from .utils.functions import (
    deletAllSessions,
    getIssuseContexFromDetails,
    generate_one_shot_response,
    NotenoughContext,
    finalFormatedOutput,
    faq_answer,
    faq_streaming_request,
    generate_email_content,
    streaming_request_upgraded,
    getReleatedChatText,
    storeSession,
    loadSession,
    deleteSession,
    insert2Memory,
)

import app.utils._global as _global
from .utils._global import updateStatus

from dotenv import load_dotenv

load_dotenv()
app = FastAPI()


origins = [
    "https://elevaite.iopex.ai",
    "http://localhost",
    "http://localhost:3000",
    "https://api.iopex.ai",
    "https://elevaite-cb.iopex.ai",
    "http://elevaite-cb.iopex.ai",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## Global variables
totalTokens = 0
scoreDiff = 5
qa_collection_name = os.environ.get("QDRANT_COLLECTION")
openai.api_key = os.environ["OPENAI_API_KEY"]
manager = AsyncCallbackManager([MyCustomCallbackHandler()])
MAX_KB_TOKENSIZE = 1000


llm.callback_manager = manager

memory = defaultdict()


@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/agent-assist")
@app.get("/in-warranty")
def get_Agent_incidentSolver(query: str, uid: str, sid: str, collection: str):
    if uid not in _global.tokenCount:
        _global.tokenCount[uid] = {sid: 0}
    updateStatus(uid, sid, "Main")
    chat_session_memory = loadSession(uid, sid)
    chat_session_memory = insert2Memory({"from": "human", "message": query}, chat_session_memory)
    storeSession(uid, sid, chat_session_memory)
    # streaming_request_upgraded(uid, sid, query, collection)
    return StreamingResponse(
        streaming_request_upgraded(uid, sid, query, collection),
        media_type="text/event-stream",
    )


# non agent version
@app.get("/out-of-warranty")
def get_Agent_incidentSolver(query: str, uid: str, sid: str, collection: str):
    memory = loadSession(uid, sid)
    final_result = ""
    memory = insert2Memory({"from": "human", "message": query}, memory)
    storeSession(uid, sid, memory)
    _global.currentStatus[uid][sid] = ""
    if uid not in _global.tokenCount:
        _global.tokenCount[uid] = {sid: 0}
    updateStatus(uid, sid, "Main")
    results = ""
    print(len(memory))
    final_answer = faq_answer(uid, sid, query, collection)
    if final_answer:
        return StreamingResponse(
            faq_streaming_request(final_answer), media_type="text/event-stream"
        )

    if len(memory) == 1:
        tenant = "Netskope"
        if collection == "kbDocs_netskope_v1":
            tenant = "Netskope"
        else:
            tenant = "Netgear"
        results = func_incidentScoringChain(uid, sid, query, tenant)
        if "NOT SUPPORTED" in results:
            final_result = "Not supported"
            memory = insert2Memory({"from": "ai", "message": final_result}, memory)
            storeSession(uid, sid, memory)
            return final_result
        else:
            res = json.loads(results)
            if res["Score"] > 7:
                context = getIssuseContexFromDetails(uid, sid, query, collection)

                return StreamingResponse(
                    finalFormatedOutput(uid, sid, query, context),
                    media_type="text/event-stream",
                )
                # final_result = finalFormatedOutput(query, context)
                # print(final_result)
                # memory = insert2Memory({"from": "ai", "message": final_result}, memory)
                # print("Total Ticket = " + str(_global.tokenCount))
                # return {"text": final_result}
            else:
                return StreamingResponse(
                    NotenoughContext(uid, sid, query), media_type="text/event-stream"
                )
                # print(final_result)
                # memory = insert2Memory({"from": "ai", "message": final_result}, memory)
                # print("Total Ticket = " + str(_global.tokenCount))
                # return {"text": final_result}

    else:
        output = getReleatedChatText(uid, sid, query)
        query_with_memory = f"Here is the past relevant messages for your reference delimited by three backticks: \
            \
        ```{output}``` \
        \n  \
        Here is the query for you to answer delimited by <>: \n \
        <{query}> \
        "
        query = query_with_memory
        context = getIssuseContexFromDetails(uid, sid, query, collection)
        return StreamingResponse(
            finalFormatedOutput(uid, sid, query, context),
            media_type="text/event-stream",
        )
        # final_result = finalFormatedOutput(query, context)
        # memory = insert2Memory({"from": "ai", "message": final_result}, memory)
        # print("Total Ticket = " + str(_global.tokenCount))
        # return {"text": final_result}


# @app.get("/email")
# def send_email(query: str):
#     context = getIssuseContexFromDetails(
#         "123123123", "123123123", query, "kbDocs_netgear_faq"
#     )
#     result = generate_email_content(query, context)
#     return {"text": result}

@app.post('/email')
async def email_request(request:Request):
    print("inside request")
    data = await request.json()    
    email_query = data['email_query']
    print("EMAIL QUERY TO DEBUG-------------------------\n",email_query)
    email_conversation_list = EmailConversationParser().get_email_conversations(email_query)
    print("Here is the list", email_conversation_list)
    idx_split = email_query.find("<iopexelevaite@gmail.com> wrote")
    print(idx_split)
    latest_message = past_messages = ""
    if idx_split !=-1:
        latest_message = str(email_query[:idx_split])
        past_messages = "<email_history>\n" + str(email_query[idx_split:]) + "\n</email_history>"
    else:
        latest_message= str(email_query)
    # email_conversation_list = EmailConversationParser().get_email_conversations(email_query)
    # print("Here is the list", email_conversation_list)
    
    context = getIssuseContexFromDetails(
        "123123123", "123123123", latest_message+past_messages, "kbDocs_netgear_faq"
    )
    print("This is context", context)
    output_data = generate_email_content(latest_message, past_messages, context)
    print(output_data)
    return {"text": output_data}

@app.get("/storeSession")
def store_memory(uid: str, sid: str):
    memory = loadSession(uid, sid)
    storeSession(uid, sid, memory)
    return {"Memory": "Stored"}


@app.get("/loadSession")
def load_memory(uid: str, sid: str):
    memory = loadSession(uid, sid)
    return memory


@app.get("/deleteSession")
def delete_session(uid: str, sid: str):
    deleteSession(uid, sid)
    return "Session cleared"


@app.get("/deleteAllSessions")
def delete_session(uid: str):
    deletAllSessions(uid)
    return "Deleted sessions"


@app.get("/currentStatus")
async def current_status(request: Request):
    async def status_generator():
        uid = request.query_params["uid"]
        sid = request.query_params["sid"]
        while True:
            if await request.is_disconnected():
                break
            if uid not in _global.prevStatus:
                _global.prevStatus[uid] = {sid: ""}
            if sid not in _global.prevStatus[uid]:
                _global.prevStatus[uid] = {sid: ""}
            if _global.prevStatus[uid][sid] != _global.currentStatus[uid][sid]:
                print(_global.prevStatus[uid][sid])
                _global.prevStatus[uid][sid] = _global.currentStatus[uid][sid]
                yield {"data": _global.currentStatus[uid][sid]}

    return EventSourceResponse(status_generator())



# Cisco endpoint
@app.post("/query")
async def send_response_with_chunks(request: Request):
    try: 
        load_dotenv()
        data = await request.json()  
        auth_token = request.headers["x-api-key"]
        if auth_token == None or auth_token != os.getenv("CISCO_API_KEY"):
            raise Exception("Authentication Error")
        print(data)
        query = data["query"]
        result = await generate_one_shot_response(query)    
        return(result)
    except Exception as error:
        res = {"error": "Authentication Error", "success": False}
        print(error)
        if str(error) == "'x-api-key'" or str(error) == "Authentication Error":
            response = JSONResponse(
                status_code=401, content=res, media_type="application/json"
            )
        else:
            res = {"error": str(error), "success": False}
            response = JSONResponse(
                status_code=500, content=res, media_type="application/json"
            )
        return response