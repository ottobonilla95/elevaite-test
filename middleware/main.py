from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from _global import llm
from _global import tokenCount
import tiktoken
import os
import json
import re
from typing import Any, Dict, List, Optional, Union
from langchain.agents import initialize_agent, load_tools
from langchain.agents import AgentType
from langchain.schema import AgentAction, AgentFinish, LLMResult
from langchain.callbacks.base import CallbackManager, BaseCallbackHandler
from langchain.agents import Tool
import openai
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory

from get_tokens_count import get_tokens_count
from callback import MyCustomCallbackHandler
from incidentScoringChain import func_incidentScoringChain 
from functions  import getIssuseContexFromSummary, deletAllSessions, \
    getIssuseContexFromDetails, UnsupportedProduct, NotenoughContext, finalFormatedOutput \
, getReleatedChatText, storeSession, loadSession, deleteSession, insert2Memory

import _global
from _global import currentStatus
from _global import updateStatus

import logging
from time import time


app = FastAPI()
origins = ["https://elevaite.iopex.ai", "http://localhost", "http://localhost:3000", "https://api.iopex.ai",
           "https://elevaite-cb.iopex.ai", "http://elevaite-cb.iopex.ai"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

## Global variables
totalTokens=0
scoreDiff=5
qa_collection_name=os.environ.get("QDRANT_COLLECTION")
openai.api_key = os.environ["OPENAI_API_KEY"]
manager = CallbackManager([MyCustomCallbackHandler()])
MAX_KB_TOKENSIZE=1000


llm.callback_manager=manager
## Tool to get the incident scoring
tool_incidentScoring = Tool(
    name="tool_incidentScoring",
    func=func_incidentScoringChain,
    description="First Step to find supported product and enough content of incident is there, Useful to Score the incident text for completeness and identify which knowledge arcticel group to use. This tool can never give final answer. Do not take more than 5 seconds here.",
    verbose=True,
    callback_manager=manager,
)

## Tool to get the data from summary knowledge base

tool_incidentSummarySearch = Tool(
      name="tool_incidentSummarySearch",
      func=getIssuseContexFromSummary,
      description="If Score is between 6, Useful to get the Knowledge Articles relevant to the incident. Do not take more than 5 seconds here.",
      verbose=True,
      callback_manager=manager,
      return_direct=True,
  ) 

tool_incidentDetailsSearch = Tool(
    name="tool_incidentDetailsSearch",
    func=getIssuseContexFromDetails,
    #description="If Score greater than 7,Useful to get the Knowledge Articles relevant to the incident",
    description="Useful to get the Knowledge Articles relevant to the incident if the incident text has good content to guide to solve. Do not take more than 5 seconds here.",
    verbose=True,
    callback_manager=manager,
    return_direct=True,
) 

tool_UnsupportedProduct = Tool(
    name="tool_UnsupportedProduct",
    func=UnsupportedProduct,
    description="Useful to answer Not Supported Product questions, or if it not Incident text. Do not take more than 5 seconds here.",
    verbose=True,
    callback_manager=manager,
    return_direct=True,
)

tool_NotenoughContext = Tool(
    name="tool_NotenoughContext",
    func=NotenoughContext,
    description="Useful to answer when the incident context for Supported Product score is less than 6. Do not take more than 5 seconds here.",
    verbose=True,
    callback_manager=manager,
    return_direct=True,
) 

tool_finalFormatedOutput = Tool(
    name="tool_finalFormatedOutput",
    func=finalFormatedOutput,
    description="Call this to format the final output of the Agent. Do not take more than 5 seconds here.",
    verbose=True,
    callback_manager=manager,
    return_direct=True,
) 

tool_checkRelatedHistory = Tool(
    name="tool_checkRelatedHistory",
    func=getReleatedChatText,
    description="Need to use this tool if the current input is referring to past convesation / chat history OR  when some Additional Context are provided, some possible examples will be usage of words like above, previous, additional etc", 
    verbose=True,
    callback_manager=manager,
    return_direct=False,
)

llm.callback_manager=manager

toolList =[  tool_checkRelatedHistory \
           , tool_incidentScoring \
#          , tool_incidentSummarySearch\
           , tool_incidentDetailsSearch\
           , tool_UnsupportedProduct\
           , tool_NotenoughContext ]
          #, tool_finalFormatedOutput]



Agent_incidentSolver =""
#memory = ConversationSummaryBufferMemory(llm=llm, memory_key="chat_history", return_messages=True)
#memory = ConversationBufferMemory( memory_key="chat_history", return_messages=True)
memory= _global.chatHistory

Agent_incidentSolver = initialize_agent(
            tools=toolList,
            llm=llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            verbose=True,
            callback_manager=manager,
        )
            #memory=memory,
Agent_incidentSolver.return_intermediate_steps = False

replaceText="Answer the following questions as best you can. You will always use Tools to generate the Answer and not answer yourself."
tobeReplaced="Answer the following questions as best you can."

orgPrompt=Agent_incidentSolver.agent.llm_chain.prompt.template

Agent_incidentSolver.agent.llm_chain.prompt.template=orgPrompt.replace(tobeReplaced,replaceText ) 


@app.get("/")
def read_root():
    return {"Hello": "World"}

# @app.get("/query")
# def get_Agent_incidentSolver(query: str):
#     global memory 
#     memory=insert2Memory({"from":"human", "message" : query}, memory)
#     _global.currentStatus=""
#     _global.tokenCount=0
#     updateStatus("Main")
#     response=Agent_incidentSolver(query)
#     results=finalFormatedOutput(query, response['output'])    
#     print("Total Ticket = " + str(_global.tokenCount))
#     memory=insert2Memory({"from":"ai", "message" : results}, memory)
#     return({"text":results})


# non agent version 
@app.get("/query")
def get_Agent_incidentSolver(query: str):
    global memory 
    final_result = ""
    memory=insert2Memory({"from":"human", "message" : query}, memory)
    _global.currentStatus=""
    _global.tokenCount=0
    updateStatus("Main")
    results = ""
    print(len(memory))
    if len(memory) == 1:
        results = func_incidentScoringChain(query)
        if "NOT SUPPORTED" in results:
            final_result="Not supported"
            memory=insert2Memory({"from":"ai", "message" : final_result}, memory)
            return({"text":final_result})
        else:
            res = json.loads(results)
            if res["Score"] > 7:
                context = getIssuseContexFromDetails(query) 
                final_result = finalFormatedOutput(query, context)
                memory=insert2Memory({"from":"ai", "message" : final_result}, memory)
                print("Total Ticket = " + str(_global.tokenCount))
                return({"text":final_result})
            else:
                final_result = NotenoughContext(query)
                print(final_result)
                memory=insert2Memory({"from":"ai", "message" : final_result}, memory)
                print("Total Ticket = " + str(_global.tokenCount))
                return({"text":final_result})


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
        final_result = finalFormatedOutput(query, context)
        memory=insert2Memory({"from":"ai", "message" : final_result}, memory)
        print("Total Ticket = " + str(_global.tokenCount))
        return({"text":final_result})
    



@app.get("/storeSession")
def store_memory(sessionID: str):
    global memory 
    storeSession(sessionID, memory)
    return {"Memory": "Stored"}

@app.get("/loadSession")
def load_memory(sessionID: str):
    global memory 
    memory.clear()
    memory=loadSession(sessionID)
    _global.chatHistory=memory
    return (memory)

@app.get("/deleteSession")
def delete_session(sessionID: str):
    memory.clear()
    deleteSession(sessionID)
    return ("Session cleared")

@app.get("/deleteAllSessions")
def delete_session():
    memory.clear()
    deletAllSessions()
    return ("Deleted sessions")

@app.get("/currentStatus")
def current_status():
    return ({"Status" : _global.currentStatus})
