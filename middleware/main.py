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
def get_Agent_incidentSolver(query: str, sid:str):
    global memory
    final_result = ""
    memory = insert2Memory({"from": "human", "message": query}, memory)
    storeSession(sid, memory)
    _global.currentStatus = ""
    _global.tokenCount = 0
    updateStatus("Main")
    results = ""
    print(len(memory))
    if len(memory) == 1:
        results = func_incidentScoringChain(query)
        if "NOT SUPPORTED" in results:
            final_result = 'Not supported'
            memory = insert2Memory({"from": "ai", "message": final_result}, memory)
            storeSession(sid, memory)
            return final_result
        else:
            res = json.loads(results)
            if res["Score"] > 7:
                context = getIssuseContexFromDetails(query)
                
                return StreamingResponse(finalFormatedOutput(sid, query, context), media_type="text/event-stream")
                # final_result = finalFormatedOutput(query, context)
                # print(final_result)
                # memory = insert2Memory({"from": "ai", "message": final_result}, memory)
                # print("Total Ticket = " + str(_global.tokenCount))
                # return {"text": final_result}
            else:
                return StreamingResponse(NotenoughContext(sid, query), media_type="text/event-stream")
                # print(final_result)
                # memory = insert2Memory({"from": "ai", "message": final_result}, memory)
                # print("Total Ticket = " + str(_global.tokenCount))
                # return {"text": final_result}

    else:
        output = getReleatedChatText(query)
        query_with_memory = f"Here is the past relevant messages for your reference delimited by three backticks: \
            \
        ```{output}``` \
        \n  \
        Here is the query for you to answer delimited by <>: \n \
        <{query}> \
        "
        query = query_with_memory
        context = getIssuseContexFromDetails(query)
        return StreamingResponse(finalFormatedOutput(sid, query, context), media_type="text/event-stream")
        # final_result = finalFormatedOutput(query, context)
        # memory = insert2Memory({"from": "ai", "message": final_result}, memory)
        # print("Total Ticket = " + str(_global.tokenCount))
        # return {"text": final_result}


@app.get("/storeSession")
def store_memory(sessionID: str):
    global memory
    storeSession(sessionID, memory)
    return {"Memory": "Stored"}


@app.get("/loadSession")
def load_memory(sessionID: str):
    global memory
    memory.clear()
    memory = loadSession(sessionID)
    _global.chatHistory = memory
    return memory


@app.get("/deleteSession")
def delete_session(sessionID: str):
    memory.clear()
    deleteSession(sessionID)
    return "Session cleared"


@app.get("/deleteAllSessions")
def delete_session():
    memory.clear()
    deletAllSessions()
    return "Deleted sessions"


@app.get("/currentStatus")
async def current_status(request: Request):
    async def status_generator():
        while True:
            if await request.is_disconnected():
                break
            print(_global.prevStatus)
            if _global.prevStatus!= _global.currentStatus:
                _global.prevStatus = _global.currentStatus
                yield{
                    "data": _global.currentStatus
                }
    return EventSourceResponse(status_generator())
