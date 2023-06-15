from langchain.embeddings.openai import OpenAIEmbeddings
from fastapi.responses import StreamingResponse
import os
import json
import openai
from qdrant_client import QdrantClient
from langchain.vectorstores import Qdrant 
from typing import Union, Optional 
from langchain.memory import ConversationBufferMemory, ConversationSummaryBufferMemory
from langchain import PromptTemplate
from langchain.chains import LLMChain
from langchain.chat_models import ChatOpenAI
MAX_KB_TOKENSIZE=2500
scoreDiff=5
from _global import llm
import _global
from langchain.callbacks.base import BaseCallbackHandler
from langchain.callbacks.manager import AsyncCallbackManager
from callback import MyCustomCallbackHandler
from langchain.llms import OpenAI
from langchain.schema import messages_from_dict, messages_to_dict
from langchain.memory import ChatMessageHistory
from langchain.embeddings.openai import OpenAIEmbeddings
import datetime
from _global import updateStatus
import uuid

from langchain.chains import RetrievalQA


memory = _global.chatHistory


def UnsupportedProduct(uid: str, sid: str, query: str): #, filter: dict):
     updateStatus(uid, sid, "UnsupportedProduct") 
     return ("The product seems to be something I cannot support. Please verify the incident text provided ")


def NotenoughContext(uid: str, sid: str, query: str): #, filter: dict):
     updateStatus(uid, sid, "NotenoughContext")
     prompt = "Respond as a support engineer by following the two steps below." \
      "\n 1. Communicate to user that enough information is not provided." \
      "\n 2. Provide top 4 information (ordered in html ol tags) that need to be collected from User based on the below query \n " \
      + query
     llm.temperature=0
     returnVal=llm(prompt)
     return streaming_request(uid, sid, prompt)

   #   return (returnVal)


def finalFormatedOutput(uid: str, sid:str, inputString: str, context: Optional[str] = None): #, filter: dict):
     updateStatus(uid, sid, "finalfinalFormatedOutput")
     prompt =   "For the given Incident text and Knowledge Articles, " \
               +"Use only relevant knowledge articles."\
               +"Dont repate Input Text and just provide output as troubleshooting steps or additional questions to be collected. "\
               +"If URLs available provide at the end after all steps one after other as Hyperlinks under Heading 'References'" \
               +"Dont repeate the URLs, remove duplicates\n" \
               +"Provide the answer in HTML format with ol tags.\n"  \
               +"Incident Text = '" +inputString+"'\n" \
               +"Knowledge Articles = '" + context + "'"
     #returnVal=(prompt)
     #+"Dont repeate the URLs and provide them one after another. "\

     llm.temperature=0
     llm.max_tokens=2000
     returnVal=llm(prompt)
     return streaming_request(uid, sid, prompt)


   #   return (returnVal)


def processQdrantOutput(uid: str, sid: str, results: list, query: str):
    updateStatus(uid, sid,"processQdrantOutput")
    finalResults=["Knowledge Articles:\n"]
    tokenSize=0
    prevScore=0
    kbCnt=1
    prevContent=""
    prevURL=""
    for i in range(len(results)):
      currentScore=results[i][1]
      currentURL=results[i][0].metadata['source']
      print(str(currentScore) + " : " + currentURL) 
      if currentScore > 0.7:
         tokenSize=tokenSize+results[i][0].metadata["tokenSize"]
         if (tokenSize < MAX_KB_TOKENSIZE and (prevScore==0  or  (prevScore-currentScore)/prevScore*100 <= scoreDiff )):
            #finalResults.append(str(i+1) +". "+results[i][0].metadata['title']  \
            
            if prevURL=="":
               prevURL=currentURL
               knowledgeText="\n" +str(kbCnt) + ". '"
               kbCnt=kbCnt+1
            if currentURL != prevURL : 
               knowledgeText =  knowledgeText  \
                                + "Relevance Score = " + str(prevScore) +"'"\
                                + "\nURL : " + prevURL
               finalResults.append(knowledgeText)                 
               knowledgeText="\n" +str(kbCnt) + ". '"\
                                + results[i][0].page_content                 
               prevURL=currentURL
               kbCnt=kbCnt+1
            else :
               knowledgeText=knowledgeText + results[i][0].page_content + "\n"
            prevScore=currentScore
         else:
            break 
    knowledgeText =  knowledgeText  \
                  + "Relevance Score = " + str(prevScore) +"'"\
                  + "\nURL : " + prevURL

                            
    finalResults.append(knowledgeText)
    output=(' '.join(finalResults) )
    return(output)

def getIssuseContexFromSummary(uid: str, sid: str, query: str): #, filter: dict):
    updateStatus(uid, sid, "getIssuseContexFromSummary")
    embeddings = OpenAIEmbeddings()
    qa_collection_name=os.environ.get("QDRANT_COLLECTION")
    #if not filter:
    filter={"Summary" : "Y"}
    #else:
       #filter.update({"DocumentType" : "Summary"})

    qdrant_client = QdrantClient(
         url    =os.environ.get("QDRANT_URL")
        ,api_key=os.environ.get("QDRANT_API_KEY")
    )

    qdrant = Qdrant(
                      client=qdrant_client\
                    , collection_name=qa_collection_name\
                    , embeddings=embeddings \
                    #, content_payload_key="Text" \
                    #, metadata_payload_key="metadata"
    )
    results=qdrant.similarity_search_with_score(query, filter=filter, k=4)
    return(processQdrantOutput(uid, sid, results, query))

def getIssuseContexFromDetails(uid: str, sid: str, query: str): #, filter: dict):
    updateStatus(uid, sid, "getIssuseContexFromDetails")
    embeddings = OpenAIEmbeddings()
    qa_collection_name=os.environ.get("QDRANT_COLLECTION")
    print("Collection Name = " + qa_collection_name)
    #if not filter:
    filter={"Summary" : "N"}
    #else:
       #filter.update({"DocumentType" : "Details"})
   
    qdrant_client = QdrantClient(
         url    =os.environ.get("QDRANT_URL")
        ,api_key=os.environ.get("QDRANT_API_KEY")
    )

    qdrant = Qdrant(
                      client=qdrant_client\
                    , collection_name=qa_collection_name\
                    , embeddings=embeddings \
                    #, content_payload_key="Text" \
                    #, metadata_payload_key="metadata"
    )
    results=qdrant.similarity_search_with_score(query, k=3)  # filter=filter
    return(processQdrantOutput(uid, sid, results, query))

def getReleatedChatText(uid: str, sid: str, input: str): 
     chatHistory = loadSession(uid, sid)
     updateStatus(uid, sid, "getReleatedChatText")
     manager = AsyncCallbackManager([MyCustomCallbackHandler()])
     template=""" Find and return messages within <past_messages> </past_messages> that are relevant to the input within <input> </input> 
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
     llm.callback_manager=manager
     llmgpt=ChatOpenAI(model_name="gpt-3.5-turbo", verbose=True,  max_tokens=MAX_KB_TOKENSIZE,  temperature=0, callback_manager=manager)
     llmChain=LLMChain(llm=llmgpt, prompt=prompt, verbose=True, callback_manager=manager)
     past_messages=[]
     results="NONE"
     if(chatHistory):
         for items in chatHistory:
            past_messages.append(items["from"] +  " : " + items["message"])
         results=llmChain.predict(input_text=input, past_messages=past_messages)
         results=results.replace("\n","") 
     if 'NONE' in results.upper():
         return('')
     else:
         return(results)
     

# def retrieve_from_kb(query:str):
#    llm = OpenAI(temperature=0)
#    MODEL = "text-embedding-ada-002"
#    client = QdrantClient(
#     url = os.environ["QDRANT_URL"],
#     prefer_grpc=True,
#     api_key = os.environ["QDRANT_API_KEY"]
#     )
#    embeddings = OpenAIEmbeddings(model=MODEL)
#    qdrant = Qdrant(
#     client=client, collection_name=os.environ.get("QDRANT_COLLECTION"), 
#     embedding_function=embeddings.embed_query
# )
#    retriever = qdrant.as_retriever()
#    memory = ConversationSummaryBufferMemory(llm=llm, memory_key="chat_history", max_token_limit=2000)
#    knowledgeBase = RetrievalQA.from_chain_type(llm=llm, chain_type="map_reduce", memory=memory, retriever=retriever)
#    return (knowledgeBase.run(query))

def streaming_request(uid: str, sid: str, input: str):
    memory = loadSession(uid, sid)
    openai.api_key = os.getenv("OPENAI_API_KEY")
    completion = openai.ChatCompletion.create(
            model='gpt-3.5-turbo', 
            messages=[{"role": "user", "content": input}],
            stream=True)
    final_result = ""
    for line in completion:
            chunk = line['choices'][0].get('delta', {}).get('content', '')
            if chunk:
                final_result += chunk
                yield chunk
    if len(final_result) > 0:
      memory = insert2Memory({"from": "ai", "message": final_result}, memory)
      storeSession(uid, sid, memory)
    return True


def storeSession(uid: str, sid:str, chatHistory: list):
   updateStatus(uid, sid, "storeSession")
   folderPath="./sessionMemory/"+uid
   if not (os.path.isdir(folderPath)):
      os.mkdir(folderPath)
   fileName=str(sid)+".json"
   with open(os.path.join(folderPath, fileName), 'w') as outfile:
      json.dump(chatHistory, outfile, indent=4)
   return(True)


def loadSession(uid: str, sid: str):
   updateStatus(uid, sid, "loadSession")
   ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
   folderPath="./sessionMemory/"+uid
   fileName=str(sid)+".json"
   if not (os.path.isdir(folderPath)):
       os.mkdir(folderPath)
   if not (os.path.isfile(os.path.join(folderPath, fileName))):
      with open(os.path.join(folderPath, fileName), 'w') as outfile:
         json.dump([], outfile, indent=4)
   with open(os.path.join(folderPath, fileName), 'r') as infile:
      _global.currentStatus[uid][sid]=json.load(infile)
   return(_global.currentStatus[uid][sid])

def deleteSession(uid: str, sid: str):
   updateStatus(uid, sid, "deleteSession")
   ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
   folderPath="./sessionMemory/" + uid
   fileName=str(sid)+".json"
   if os.path.isfile(os.path.join(folderPath, fileName)):
      os.remove(os.path.join(folderPath, fileName))
   return(_global.currentStatus[uid][sid])


def deletAllSessions(uid:str):
   ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
   folderPath="./sessionMemory/" + uid
   for f in os.listdir(folderPath):
      os.remove(os.path.join(folderPath, f))
   return "Done"

def insert2Memory(memoryValue: dict, chatHistory: list):
    messageType=memoryValue['from']
    message=memoryValue['message']
    currentTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uuid_value=str(uuid.uuid4())
    chatHistory.append({'id': uuid_value, 'from': messageType, 'message': message, 'timestamp':currentTime})
    return(chatHistory)



