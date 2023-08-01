import datetime
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory
from collections import defaultdict
from langchain.embeddings.openai import OpenAIEmbeddings

llm = OpenAI( verbose=True\
             ,temperature=0\
            )
tokenCount=defaultdict()
currentStatus=defaultdict()
prevStatus = defaultdict()
# memory = defaultdict()
#chatHistory: ConversationBufferMemory
chatHistory=[]

def updateStatus(uid: str, sid: str, currentState: str):
  global currentStatus
  currentStatus[uid] = {sid: ""}
  currentTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  currentStatus[uid][sid]=currentTime + "  " + currentState 
