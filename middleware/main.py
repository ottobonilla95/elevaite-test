from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
import asyncio
import os
import json
from langchain.callbacks.manager import AsyncCallbackManager
import openai
from callback import MyCustomCallbackHandler
from langchain.chat_models import ChatOpenAI

from collections import defaultdict

#file imports
from incidentScoringChain import func_incidentScoringChain
from _global import llm
from functions import (
    deletAllSessions,
    getIssuseContexFromDetails,
    NotenoughContext,
    finalFormatedOutput,
    getReleatedChatText,
    storeSession,
    loadSession,
    deleteSession,
    insert2Memory,
)

import _global
from _global import currentStatus
from _global import updateStatus
import logging
from time import time

from dotenv import load_dotenv
from langchain import ConversationChain


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

memory = _global.chatHistory

@app.get("/")
def read_root():
    return {"Hello": "World"}

# non agent version
@app.get("/query")
def get_Agent_incidentSolver(query:str, uid:str, sid:str):
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
    if len(memory) == 1:
        results = func_incidentScoringChain(uid, sid, query)
        if "NOT SUPPORTED" in results:
            final_result = 'Not supported'
            memory = insert2Memory({"from": "ai", "message": final_result}, memory)
            storeSession(uid, sid, memory)
            return final_result
        else:
            res = json.loads(results)
            if res["Score"] > 7:
                context = getIssuseContexFromDetails(uid, sid, query)
                
                return StreamingResponse(finalFormatedOutput(uid, sid, query, context), media_type="text/event-stream")
                # final_result = finalFormatedOutput(query, context)
                # print(final_result)
                # memory = insert2Memory({"from": "ai", "message": final_result}, memory)
                # print("Total Ticket = " + str(_global.tokenCount))
                # return {"text": final_result}
            else:
                return StreamingResponse(NotenoughContext(uid, sid, query), media_type="text/event-stream")
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
        context = getIssuseContexFromDetails(uid, sid, query)
        return StreamingResponse(finalFormatedOutput(uid, sid, query, context), media_type="text/event-stream")
        # final_result = finalFormatedOutput(query, context)
        # memory = insert2Memory({"from": "ai", "message": final_result}, memory)
        # print("Total Ticket = " + str(_global.tokenCount))
        # return {"text": final_result}


@app.get("/storeSession")
def store_memory(uid: str, sid: str):
    memory = loadSession(uid, sid)
    storeSession(uid, sid, memory)
    return {"Memory": "Stored"}


@app.get("/loadSession")
def load_memory(uid:str, sid: str):
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
        uid = request.query_params['uid']
        sid = request.query_params['sid']
        while True:
            if await request.is_disconnected():
                break
            if uid not in _global.prevStatus:
                _global.prevStatus[uid] = {sid: ""}
            if sid not in _global.prevStatus[uid]:
                 _global.prevStatus[uid] = {sid: ""}
            if _global.prevStatus[uid][sid]!= _global.currentStatus[uid][sid]:
                print( _global.prevStatus[uid][sid])
                _global.prevStatus[uid][sid] = _global.currentStatus[uid][sid]
                yield{
                    "data": _global.currentStatus[uid][sid]
                }
    return EventSourceResponse(status_generator())
