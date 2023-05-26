from fastapi import FastAPI, Request
import web_extract as WEBExtract
from fastapi.middleware.cors import CORSMiddleware
import contents as datacontent
import chunk as chunking
import qdrant_insert_data as qinsert
import chunkbysize as chunksize
import logging
from time import time
import run, json

app = FastAPI() 

origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)

@app.get('/')
async def knowledgedb():
   return {"content":"This is knowledge engineering service"}

@app.post('/webscrap')
async def webextract(request:Request):
    data = await request.json()    
    time_start = gettime()
    logger.info(f'Recieved Request for URL to parse :: - {data} {int(time() * 1e+3) - time_start}ms')
    url = data['url']  
    content, url, title, documentId = WEBExtract.urlextract(url)
    if (content == ""):
        return {"content" : "Error occured, unable to process the input URL"}
    json_data = datacontent.create_data(content, url, title, documentId)    
    json_output = chunking.chunkdata(json_data)
    logger.info(f'Request for URL to parse completed :: - {data} {int(time() * 1e+3) - time_start}ms')
    return {"content":json_output}

#only for testing purpose not for KnowledgeEng UI
@app.post('/webscrapjson')
async def webextractjson(request:Request):
    data = await request.json()    
    time_start = gettime()
    logger.info(f'Recieved Request for URL to parse :: - {data} {int(time() * 1e+3) - time_start}ms')
    url = data['url']  
    content, url, title, documentId = WEBExtract.urlextract(url)
    if (content == ""):
        return {"content" : "Error occured, unable to process the input URL"}
    json_data = datacontent.create_data(content, url, title, documentId)
    json_output = json.dumps(json_data).encode("utf-8").decode()     
    logger.info(f'Request for URL to parse completed :: - {data} {int(time() * 1e+3) - time_start}ms')
    return {"content":json_output, "documentId":documentId}


@app.post('/savecontent')
async def savedata(request:Request):  
    data = await request.json()
    time_start = gettime()
    logger.info(f'Recieved Request for saving data to Qdrant :: - {int(time() * 1e+3) - time_start}ms')
    content = data["content"]
    if (content == ""):
        return {"content" : "Unable to Save content, error occured for the input data"}
    qinsert.process_data(content)
    logger.info(f'Request for saving data to Qdrant is Completed :: - {int(time() * 1e+3) - time_start}ms')
    return {"response":"Content Successfully Insered into Qdrant DB"}

@app.post('/chunksize')
async def calculatesize(request:Request):  
    data = await request.json()
    time_start = gettime()
    logger.info(f'Recieved Request for calculating chunk size :: - {data} {int(time() * 1e+3) - time_start}ms')
    content = data["content"]
    size = chunksize.tiktoken_len(content)
    logger.info(f'Request for calculating chunk size completed:: -  {int(time() * 1e+3) - time_start}ms')
    return {"chunksize":size}

def gettime():
    time_start = int(time() * 1e+3)
    return time_start