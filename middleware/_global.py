import datetime
from langchain.llms import OpenAI
from langchain.memory import ConversationBufferMemory

llm = OpenAI( verbose=True\
             ,temperature=0\
            )
tokenCount=0
currentStatus=""
#chatHistory: ConversationBufferMemory
chatHistory=[]


def updateStatus(currentState: str):
  global currentStatus
  currentTime=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
  currentStatus=currentTime + "  " + currentState 
