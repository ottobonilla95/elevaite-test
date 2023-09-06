from langchain.embeddings.openai import OpenAIEmbeddings
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi import Response
import os
import json
import openai
from qdrant_client import QdrantClient
from langchain.vectorstores import Qdrant
from typing import Union, Optional
from langchain.memory import ConversationSummaryBufferMemory
from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.chains.summarize import load_summarize_chain
from langchain.chat_models import ChatOpenAI
import re
from dotenv import load_dotenv

MAX_KB_TOKENSIZE = 2500
scoreDiff = 5
from ._global import llm
import app.utils._global as _global
from langchain.callbacks.manager import AsyncCallbackManager
from .callback import MyCustomCallbackHandler
from langchain.embeddings.openai import OpenAIEmbeddings
import datetime
from ._global import updateStatus
import uuid
import pickle
from collections import defaultdict
from .email_util.email_parser import EmailConversationParser
import app.configs.collections_config as collections_config
import app.configs.prompts_config as prompts_config
memory = _global.chatHistory


################################## FAQ Short-circuit ###############################
# Get an answer directly from the vector db without going to an LLM
def faq_answer(uid: str, sid: str, query: str, collection: str):
    memory = loadSession(uid, sid)
    embeddings = OpenAIEmbeddings()
    qa_collection_name = collections_config.collections_config[collection]
    # print("Collection Name = " + qa_collection_name)

    qdrant_client = QdrantClient(
        url=os.environ.get("QDRANT_URL"), api_key=os.environ.get("QDRANT_API_KEY")
    )

    qdrant = Qdrant(
        client=qdrant_client,
        collection_name=qa_collection_name,
        embeddings=embeddings  # , content_payload_key="Text" \
        # , metadata_payload_key="metadata"
    )
    results = qdrant.similarity_search_with_score(query, k=1)
    if results[0][1] > 0.75 and "answer" in results[0][0].metadata:
        memory = insert2Memory(
            {"from": "ai", "message": results[0][0].metadata["answer"]}, memory
        )
        storeSession(uid, sid, memory)
        return results[0][0].metadata["answer"]
    else:
        return None

def streaming_request(uid: str, sid: str, input: str):
    memory = loadSession(uid, sid)
    openai.api_key = os.getenv("OPENAI_API_KEY")
    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0613",
        messages=[{"role": "user", "content": input}],
        stream=True,
    )
    final_result = ""
    for line in completion:
        chunk = line["choices"][0].get("delta", {}).get("content", "")
        if chunk:
            final_result += chunk
            yield chunk
    if len(final_result) > 0:
        memory = insert2Memory({"from": "ai", "message": final_result}, memory)
        storeSession(uid, sid, memory)
    return True

def NotenoughContext(uid: str, sid: str, query: str):  # , filter: dict):
    updateStatus(uid, sid, "NotenoughContext")
    prompt = (
        "Respond as a support engineer by following the two steps below."
        "\n 1. Communicate to user that enough information is not provided."
        "\n 2. Provide top 4 information (ordered in html ol tags) that need to be collected from User based on the below query \n "
        + query
    )
    llm.temperature = 0
    returnVal = llm(prompt)
    return streaming_request(uid, sid, prompt)


#   return (returnVal)

def finalFormatedOutput(
    uid: str, sid: str, inputString: str, context: Optional[str] = None
):  # , filter: dict):
    updateStatus(uid, sid, "finalfinalFormatedOutput")
    prompt = (
        "For the given Incident text and Knowledge Articles, "
        + "Use only relevant knowledge articles."
        + "Dont repate Input Text and just provide output as troubleshooting steps or additional questions to be collected. "
        + "If URLs available provide at the end after all steps one after other as Hyperlinks under Heading 'References'"
        + "Dont repeate the URLs, remove duplicates\n"
        + "Provide the answer in HTML format with ol tags.\n"
        + "Incident Text = '"
        + str(inputString)
        + "'\n"
        + "Knowledge Articles = '"
        + str(context)
        + "'"
    )
    # returnVal=(prompt)
    # +"Dont repeate the URLs and provide them one after another. "\

    llm.temperature = 0
    llm.max_tokens = 2000
    returnVal = llm(prompt)
    return streaming_request(uid, sid, prompt)
#   return (returnVal)

def getIssuseContexFromSummary(uid: str, sid: str, query: str):  # , filter: dict):
    updateStatus(uid, sid, "getIssuseContexFromSummary")
    embeddings = OpenAIEmbeddings()
    qa_collection_name = os.environ.get("QDRANT_COLLECTION")
    # if not filter:
    filter = {"Summary": "Y"}
    # else:
    # filter.update({"DocumentType" : "Summary"})

    qdrant_client = QdrantClient(
        url=os.environ.get("QDRANT_URL"), api_key=os.environ.get("QDRANT_API_KEY")
    )

    qdrant = Qdrant(
        client=qdrant_client,
        collection_name=qa_collection_name,
        embeddings=embeddings  # , content_payload_key="Text" \
        # , metadata_payload_key="metadata"
    )
    results = qdrant.similarity_search_with_score(query, filter=filter, k=4)
    return processQdrantOutput(uid, sid, results)

def getReleatedChatText(uid: str, sid: str, input: str):
    chatHistory = loadSession(uid, sid)
    updateStatus(uid, sid, "getReleatedChatText")
    manager = AsyncCallbackManager([MyCustomCallbackHandler()])
    template = """ Find and return messages within <past_messages> </past_messages> that are relevant to the input within <input> </input> 
<input>\n  
{input_text}
\n</input>
\n
<past_messages> \n
{past_messages}
\n
</past_messages>
"""

    prompt = PromptTemplate(
        input_variables=["input_text", "past_messages"],
        template=template,
    )
    llm.callback_manager = manager
    llmgpt = ChatOpenAI(
        model_name="gpt-3.5-turbo",
        verbose=True,
        max_tokens=MAX_KB_TOKENSIZE,
        temperature=0,
        callback_manager=manager,
    )
    llmChain = LLMChain(
        llm=llmgpt, prompt=prompt, verbose=True, callback_manager=manager
    )
    past_messages = []
    results = "NONE"
    if chatHistory:
        for items in chatHistory:
            past_messages.append(items["from"] + " : " + items["message"])
        results = llmChain.predict(input_text=input, past_messages=past_messages)
        results = results.replace("\n", "")
    if "NONE" in results.upper():
        return ""
    else:
        return results
    
# Stream the response from vector db (short circuited response) to maintain the same user experience
def faq_streaming_request(input: str):
    for chunk in input:
        yield chunk
    return True
################################## END ###############################

################################## RAG powered QnA using Langchain Memory ###############################
# Process the output recieved from vector db to create the context for the LLM
def processQdrantOutput(uid: str, sid: str, results: list):
    updateStatus(uid, sid, "processQdrantOutput")
    finalResults = ["Knowledge Articles:\n"]
    tokenSize = 0
    prevScore = 0
    kbCnt = 1
    prevContent = ""
    knowledgeText = ""
    prevURL = ""
    for i in range(len(results)):
        currentScore = results[i][1]
        currentURL = results[i][0].metadata["source"]
        print(str(currentScore) + " : " + currentURL)
        if currentScore > 0.7:
            tokenSize = tokenSize + results[i][0].metadata["tokenSize"] #tokenSize
            if tokenSize < MAX_KB_TOKENSIZE and (
                prevScore == 0
                or (prevScore - currentScore) / prevScore * 100 <= scoreDiff
            ):
                # finalResults.append(str(i+1) +". "+results[i][0].metadata['title']  \

                if prevURL == "":
                    prevURL = currentURL
                    knowledgeText = "\n" + str(kbCnt) + ". '"
                    kbCnt = kbCnt + 1
                if currentURL != prevURL:
                    knowledgeText = (
                        knowledgeText
                        + "Relevance Score = "
                        + str(prevScore)
                        + "'"
                        + "\nURL : "
                        + prevURL
                    )
                    finalResults.append(knowledgeText)
                    knowledgeText = (
                        "\n" + str(kbCnt) + ". '" + results[i][0].page_content
                    )
                    prevURL = currentURL
                    kbCnt = kbCnt + 1
                else:
                    knowledgeText = knowledgeText + results[i][0].page_content + "\n"
                prevScore = currentScore
            else:
                break
    finalResults.append(knowledgeText)
    output = " ".join(finalResults)
    return output

# Get the chunks relevant to a query
def getIssuseContexFromDetails(
    uid: str, sid: str, query: str, collection: str, isUpsell: bool = False
):  # , filter: dict):
    updateStatus(uid, sid, "getIssuseContexFromDetails")
    embeddings = OpenAIEmbeddings()
    qa_collection_name = collections_config.collections_config[collection]
    print("Collection Name = " + qa_collection_name)
    # if not filter:
    # else:
    # filter.update({"DocumentType" : "Details"})

    qdrant_client = QdrantClient(
        url=os.environ.get("QDRANT_URL"), api_key=os.environ.get("QDRANT_API_KEY")
    )

    qdrant = Qdrant(
        client=qdrant_client,
        collection_name=qa_collection_name,
        embeddings=embeddings  # , content_payload_key="Text" \
        # , metadata_payload_key="metadata"
    )
    if isUpsell:
        filter = {"DocumentType": "Upsell"}
        results = qdrant.similarity_search_with_score(query, filter=filter, k=1)
        print('Here are upsell results', results)
        return processQdrantOutput(uid, sid, results)
    else:
        results = qdrant.similarity_search_with_score(query, k=3)  # filter=filter
        print("This is the score here",results[0][1])
        if results[0][1] < 0.70:
            return None
        return processQdrantOutput(uid, sid, results)

# Stream the response being generated based on RAG
def streaming_request_upgraded(uid: str, sid: str, human_input: str, collection: str, isUpsell: bool = False, withRefs: bool = False):
    template = ''
    print('This is upsell', isUpsell)
    if isUpsell:
        template = prompts_config.prompts_config['netgear_upsell']
    else:
        template = prompts_config.prompts_config[collection]
    chat = ChatOpenAI(temperature=0)
    chat_session_memory = loadSession(uid, sid)
    if os.path.getsize('./db/all_chat_memory.pkl') > 0:
        with open('./db/all_chat_memory.pkl', 'rb') as f:
                memory = pickle.load(f)
        f.close()
    else:
        memory = defaultdict()
    if uid not in memory:
        memory[uid] = {
            sid: ConversationSummaryBufferMemory(
                llm=chat, max_token_limit=1500, memory_key="chat_history", 
            )
        }
    if sid not in memory[uid]:
        memory[uid] = {
            sid: ConversationSummaryBufferMemory(
                llm=chat, max_token_limit=1500, memory_key="chat_history"
            )
        }
    with open('./db/all_chat_memory.pkl', 'wb') as f:
        pickle.dump(memory, f, pickle.HIGHEST_PROTOCOL)
        
    input = str(memory[uid][sid]) + human_input
    recent_history = loadSession(uid, sid)
    if len(recent_history) > 3:
        input = '\n'.join(str(msg['from']+ ":" + msg['message']) for msg in recent_history[-3:])
    else:
        input = '\n'.join(str(msg['from']+ ":" + msg['message']) for msg in recent_history)
    print("This is the whole input", input)
    if isUpsell:
        context = getIssuseContexFromDetails(uid, sid, input, collection, True)
    else:
        context = getIssuseContexFromDetails(uid, sid, input, collection)
    
    refs = set()
    if withRefs:
        data = get_context_for_query(input, collection)
        chunks = data['chunks']
        for chunk in chunks:
            refs.add(chunk['reference'])

    if context is not None:
        input = (
            human_input
            + "\n Here is the context below: \n <context> \n"
            + context
            + "\n </context>"
        )
    else:
        input = human_input + "<context> No relevant context found. </context>"
    print(input)
    prompt = PromptTemplate(
        input_variables=["chat_history", "human_input"], template=template
    )
    llm_chain = LLMChain(llm=chat, prompt=prompt, memory=memory[uid][sid])
    result = llm_chain.predict(human_input=input)
    with open('./db/all_chat_memory.pkl', 'wb') as f:
        pickle.dump(memory, f, pickle.HIGHEST_PROTOCOL)
    # print(memory[uid][sid])

    # print(result)
    chat_session_memory = insert2Memory({"from": "ai", "message": result}, chat_session_memory)
    storeSession(uid, sid, chat_session_memory)
    final_result = ""
    if withRefs:
        list_refs = list(refs)
        return result, list_refs
    else:
        return faq_streaming_request(result)
################################## END ###############################



################################## e-mail generation ###############################
def generate_email_content(latest_message: str, past_messages: str, context: str):
    prompt = (
        "You are a Customer Support Agent. Respond to the Human using the details given in <context></context> tags and <email_history></email_history> tags, generate a response to the EMAIL you have received from a customer. Please provide your response in a well formatted html. Add ol tags if you have a stepwise answer. DO NOT add email signature and DO NOT add [YOUR NAME] in your response. DO NOT send the relevance score as part of your response."
        + "\nIf you do not have relevant information to answer the query, respond with a set of questions you have regarding the query.\n"
        +"Look into the <email_history></email_history> to see if the answer you are generating is not repeated."
        + "\nIf the user requests to connect to a customer support engineer, please say that you've assigned the ticket to Paul Jeyasingh and that he will respond to the email."
        + "Human:" + latest_message
        + "\nPast Messages:" + past_messages
        + "\nHere is your context \n <context>"
        + context
        + "\n </context>"
        + "Customer Support Agent:"
    )

    llm.temperature = 0
    llm.max_tokens = 2500
    # print(prompt)
    returnVal = ""


    try:
        returnVal = llm(prompt)
    except:
        llm.max_tokens = 1500
        summary_prompt = (
            "Summarize the below text in less than 1500 tokens\n" +
            "Input:" + past_messages +
            "\nSummary:"
        )
        summarized_past_messages = llm(summary_prompt)
        prompt = (
            "You are a Customer Support Agent. Respond to the Human using the details given in <context></context> tags and <email_history></email_history> tags, generate a response to the EMAIL you have received from a customer. Please provide your response in a well formatted html. Add ol tags if you have a stepwise answer. DO NOT add email signature and DO NOT add [YOUR NAME] in your response. DO NOT send the relevance score as part of your response."
            + "\nIf you do not have relevant information to answer the query, respond with a set of questions you have regarding the query.\n"
            +"Look into the <email_history></email_history> to see if the answer you are generating is not repeated."
            + "\nIf the user requests to connect to a customer support engineer, please say that you've assigned the ticket to Paul Jeyasingh and that he will respond to the email."
            + "Human:" + latest_message
            + "\nPast Messages:" + summarized_past_messages
            + "\nHere is your context \n <context>"
            + context
            + "\n </context>"
            + "Customer Support Agent:"
        )
        returnVal = llm(prompt)
        return returnVal
    
    return returnVal
################################## END ###############################

################################## Session house keeping ###############################
def storeSession(uid: str, sid: str, chatHistory: list):
    updateStatus(uid, sid, "storeSession")
    folderPath = "./db/sessionMemory/" + uid
    if not (os.path.isdir(folderPath)):
        os.mkdir(folderPath)
    fileName = str(sid) + ".json"
    with open(os.path.join(folderPath, fileName), "w") as outfile:
        json.dump(chatHistory, outfile, indent=4)
    return True

#storeSession with Tenant ID - 08/01/23
def storeSession_with_tenant(uid: str, tid: str, sid: str, chatHistory: list):
    updateStatus(uid, sid, "storeSession")
    folderPath = ".db/sessionMemory/" + uid + "/" + tid 

    #if Folder with uid/tid does not exist , create one
    if not (os.path.isdir(folderPath)):
        os.makedirs(folderPath)

    fileName = str(sid) + ".json"
    with open(os.path.join(folderPath, fileName), "w") as outfile:
        json.dump(chatHistory, outfile, indent=4)
    return True

def loadSession(uid: str, sid: str):
    updateStatus(uid, sid, "loadSession")
    ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
    print(os.getcwd())
    folderPath = "./db/sessionMemory/" + uid
    fileName = str(sid) + ".json"
    if not (os.path.isdir(folderPath)):
        os.mkdir(folderPath)
    if not (os.path.isfile(os.path.join(folderPath, fileName))):
        with open(os.path.join(folderPath, fileName), "w") as outfile:
            json.dump([], outfile, indent=4)
    with open(os.path.join(folderPath, fileName), "r") as infile:
        _global.currentStatus[uid][sid] = json.load(infile)
    return _global.currentStatus[uid][sid]

#loadSession with Tenant ID - 08/01/23
def loadSession_with_tenant(uid: str, tid: str, sid: str):
    updateStatus(uid, sid, "loadSession")
    ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
    print(os.getcwd())
    folderPath = ".db/sessionMemory/" + uid + "/" + tid
    fileName = str(sid) + ".json"
    #if Folder with uid/tid does not exist, create one
    if not (os.path.isdir(folderPath)):
        os.makedirs(folderPath)

    if not (os.path.isfile(os.path.join(folderPath, fileName))):
        with open(os.path.join(folderPath, fileName), "w") as outfile:
            json.dump([], outfile, indent=4)
    with open(os.path.join(folderPath, fileName), "r") as infile:
        _global.currentStatus[uid][sid] = json.load(infile)
    return _global.currentStatus[uid][sid]

def deleteSession(uid: str, sid: str):
    updateStatus(uid, sid, "deleteSession")
    ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
    folderPath = "./db/sessionMemory/" + uid
    fileName = str(sid) + ".json"
    if os.path.isfile(os.path.join(folderPath, fileName)):
        os.remove(os.path.join(folderPath, fileName))
    return _global.currentStatus[uid][sid]


def deletAllSessions(uid: str):
    ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
    folderPath = "./db/sessionMemory/" + uid
    for f in os.listdir(folderPath):
        os.remove(os.path.join(folderPath, f))
    memory = defaultdict()
    if os.path.getsize('./db/all_chat_memory.pkl') > 0:
        with open('./db/all_chat_memory.pkl', 'rb') as f:
                memory = pickle.load(f)
    memory[uid] = {}
    with open('./db/all_chat_memory.pkl', 'wb') as f:
        pickle.dump(memory, f, pickle.HIGHEST_PROTOCOL)
    f.close()
    return "Done"

#Function to extract the session details for getAllSessions() & getAllSessionsbyTenant()
def processSessionDetails(tid,sid, file_path):

    with open(file_path, "r") as file:
        data = json.load(file)
    
        sessionDetails ={
            "tenant_id": tid,
            "session_id" : sid,
            "title": " ".join(data[0]["message"].split()[:5]),
            "timestamp": data[0]["timestamp"]
        }
    return sessionDetails

#Get list of sessions (title) of a user 
def getAllSession(uid: str):
    
    tid = ""
    sid = ""
    sessionDetails=[]
    folderPath ="./db/sessionMemory/" + uid 
    
    #New User - no existing sessions available - return an empty json
    if not(os.path.isdir(folderPath)):
        return json.dumps(sessionDetails)
    
    #User exists
    for dir in os.scandir(folderPath):
        tid = str(dir.name)
        for filename in os.listdir(dir):
            if filename.endswith(".json"):
                filePath = folderPath + "/" + tid + "/" + filename
                sid = filename.rsplit(".json", 1)[0]
                sessionDetails.append(processSessionDetails(tid,sid,filePath))
                
                
    return json.dumps(sessionDetails)

#Get list of sessions (title) of a user WRT tenant 
def getAllSessionbyTenant(uid: str,tid: str):
    
    sid=""
    sessionDetails=[]
    folderPath = "./db/sessionMemory/" + uid + "/" + tid

    if not(os.path.isdir(folderPath)):
        return json.dumps(sessionDetails)

    for filename in os.listdir(folderPath):
        if filename.endswith(".json"):
            filePath = folderPath + "/" + filename
            sid = filename.rsplit(".json",1)[0]
            sessionDetails.append(processSessionDetails(tid,sid,filePath))

    return json.dumps(sessionDetails)


def insert2Memory(memoryValue: dict, chatHistory: list):
    messageType = memoryValue["from"]
    message = memoryValue["message"]
    currentTime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uuid_value = str(uuid.uuid4())
    chatHistory.append(
        {
            "id": uuid_value,
            "from": messageType,
            "message": message,
            "timestamp": currentTime,
        }
    )
    return chatHistory

async def extract_chat_session_summary(uid: str, sid: str):
    messages = loadSession(uid, sid)
    prompts = ['netgear_extract_title_prompt', 'netgear_extract_problem_prompt', 'netgear_extract_solution_prompt']
    title = await llm_generate_response(prompts[0], messages)
    problem = await llm_generate_response(prompts[1], messages)
    solution = await llm_generate_response(prompts[2], messages, token_size=250)
    res = {
        "title":title,
        "problem": problem,
        "solution": solution
    }
    print(res)
    return res

async def llm_generate_response(prompt_tenant: str, messages, token_size = 1000):
    template = prompts_config.prompts_config[prompt_tenant]
    prompt = PromptTemplate(input_variables=["messages"], template=template)
    llm = ChatOpenAI(temperature=0, model_name="gpt-3.5-turbo-16k" )
    llm.max_tokens = token_size
    llm_chain = LLMChain(llm=llm, prompt=prompt)
    res = await llm_chain.apredict(messages=messages)
    return res 
    
################################## END ###############################

############################################# Cisco endpoint #############################################


def get_context_for_query(query: str, collection: str):
    MODEL = "text-embedding-ada-002"
    qa_collection_name = collections_config.collections_config[collection]
    print(qa_collection_name)
    qdrant_client = QdrantClient(
        url=os.environ.get("QDRANT_URL"), api_key=os.environ.get("QDRANT_API_KEY")
    )
    vectorized_query = openai.Embedding.create( input= query, engine=MODEL)

    results = qdrant_client.search(
    collection_name=qa_collection_name,
    query_vector=vectorized_query["data"][0]["embedding"],
    limit=3,
    score_threshold=0.75,
    with_vectors=False,
    with_payload=True,
)
    # results = qdrant.similarity_search_with_score(query, k=3)  # filter=filter
    chunks = []
    context = ""
    for result in results:
        chunk = {}
        res = re.sub("  ", " ", result.payload['page_content'])
        chunk["text"] = res
        print(result)
        chunk["score"] = result.score
        chunk["id"] = result.id
        chunk["reference"] = result.payload['metadata']['source']
        chunks.append(chunk)
        context += str(res)
    return {"context": context, "chunks": chunks}


async def generate_one_shot_response(query: str, prompt:str = None, collection: str = "cisco", prompt_tenant: str = "cisco_poc_1"):
    response = {}
    template = ""
    try:
        query_check = query.replace(" ", "")
        if len(query_check) == 0:
            raise ValueError("Invalid input query!")
        res = get_context_for_query(query, collection)
        print(res)
        context = res["context"]
        if prompt is None:
            template = prompts_config.prompts_config[prompt_tenant]
        else:
            template = prompt
        if context is not None:
            input = (
                query
                + "\n Here is the context below: \n <context> \n"
                + context
                + "\n </context>"
            )
        else:
            input = query + "<context> No relevant context found. </context>"
        prompt = PromptTemplate(input_variables=["human_input"], template=template)
        chat = ChatOpenAI(temperature=0)
        llm_chain = LLMChain(llm=chat, prompt=prompt)
        result = await llm_chain.apredict(human_input=input)

        # Create the response object
        response = {"answer": result, "chunks": res["chunks"], "success": True}
        response = json.dumps(response)
    except Exception as error:
        print(error)
        res = {"error": str(error), "success": False}
        response = JSONResponse(
            status_code=422, content=res, media_type="application/json"
        )
        return response

    return Response(response, status_code=200, media_type="application/json")