from langchain.embeddings.openai import OpenAIEmbeddings
import os
import json
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
from langchain.callbacks.base import CallbackManager, BaseCallbackHandler
from callback import MyCustomCallbackHandler
from langchain.llms import OpenAI
from langchain.schema import messages_from_dict, messages_to_dict
from langchain.memory import ChatMessageHistory
from langchain.embeddings.openai import OpenAIEmbeddings
import datetime
from _global import updateStatus
import uuid

from langchain.chains import RetrievalQA


def UnsupportedProduct(query: str): #, filter: dict):
     updateStatus("UnsupportedProduct") 
     return ("The product seems to be something I cannot support. Please verify the incident text provided ")


def NotenoughContext(query: str): #, filter: dict):
     updateStatus("NotenoughContext")
     prompt = "Communicate to user that 'Not enough information to support, provide more context'. And Provide top 4 information (ordered in html ol tags) that need to be collected from User based on the below query \n " \
      + query 
     llm.temperature=0
     returnVal=llm(prompt)
     return (returnVal)


def finalFormatedOutput(inputString: str, context: Optional[str] = None): #, filter: dict):
     updateStatus("finalfinalFormatedOutput")
     prompt =   "For the given Incident text and Knowledge Articles, " \
               +"Use only relevant knowledge articles."\
               +"Dont repate Input Text and just provide output as troubleshooting steps or additional questions to be collected. "\
               +"If URLs available provide at the end after all steps one after other as Hyperlinks under Heading 'References'" \
               +"Dont repeate the URLs, remove duplicates\n" \
               +"Provide the answer in HTML format with ol tags.\n"  \
               +"If Incident is unspported, just respond 'Unsupported Query/Product\n" \
               +"Incident Text = '" +inputString+"'\n" \
               +"Knowledge Articles = '" + context + "'"
     #returnVal=(prompt)
     #+"Dont repeate the URLs and provide them one after another. "\
     llm.temperature=0
     returnVal=llm(prompt)
     return (returnVal)


def processQdrantOutput(results: list, query: str):
    updateStatus("processQdrantOutput")
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

def getIssuseContexFromSummary(query: str): #, filter: dict):
    updateStatus("getIssuseContexFromSummary")
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
                    , embedding_function=embeddings.embed_query \
                    #, content_payload_key="Text" \
                    #, metadata_payload_key="metadata"
    )
    results=qdrant.similarity_search_with_score(query, filter=filter, k=4)
    return(processQdrantOutput(results, query))

def getIssuseContexFromDetails(query: str): #, filter: dict):
    updateStatus("getIssuseContexFromDetails")
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
                    , embedding_function=embeddings.embed_query \
                    #, content_payload_key="Text" \
                    #, metadata_payload_key="metadata"
    )
    results=qdrant.similarity_search_with_score(query, k=3)  # filter=filter
    return(processQdrantOutput(results, query))

def getReleatedChatText(input: str): 
     chatHistory = _global.chatHistory
     updateStatus("getReleatedChatText")
     manager = CallbackManager([MyCustomCallbackHandler()])
     template=""" Give all the relevant past messages from the history
Input :  
{input_text}

History Messages
-----------------
{past_messages}
"""
    
     prompt = PromptTemplate(
           input_variables=["input_text", "past_messages"],
           template=template,
       )
     llm.callback_manager=manager
     llmgpt=ChatOpenAI(model_name="gpt-3.5-turbo", verbose=True,  temperature=0, callback_manager=manager)
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

def storeSession(sessionID, chatHistory: list):
   updateStatus("storeSession")
   folderPath="./sessionMemory"
   fileName=str(sessionID)+".json"
   with open(os.path.join(folderPath, fileName), 'w') as outfile:
      json.dump(chatHistory, outfile, indent=4)
   return(True)


def loadSession(sessionID: str):
   updateStatus("loadSession")
   ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
   folderPath="./sessionMemory"
   fileName=str(sessionID)+".json"
   if not (os.path.isfile(os.path.join(folderPath, fileName))):
      with open(os.path.join(folderPath, fileName), 'w') as outfile:
         json.dump([], outfile, indent=4)
   with open(os.path.join(folderPath, fileName), 'r') as infile:
      _global.currentStatus=json.load(infile)
   return(_global.currentStatus)

def deleteSession(sessionID: str):
   updateStatus("deleteSession")
   ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
   folderPath="./sessionMemory"
   fileName=str(sessionID)+".json"
   if os.path.isfile(os.path.join(folderPath, fileName)):
      os.remove(os.path.join(folderPath, fileName))
   return(_global.currentStatus)


def deletAllSessions():
   updateStatus("deleteAllSessions")
   ## Logically when loadSession is called, expectation is UI would have called the storeSession first and then call loadSession.
   folderPath="./sessionMemory"
   for f in os.listdir(folderPath):
      os.remove(os.path.join(folderPath, f))
   return(_global.currentStatus)

def insert2Memory(memoryValue: dict, chatHistory: list):
    messageType=memoryValue['from']
    message=memoryValue['message']
    currentTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    uuid_value=str(uuid.uuid4())
    chatHistory.append({'id': uuid_value, 'from': messageType, 'message': message, 'timestamp':currentTime})
    return(chatHistory)
