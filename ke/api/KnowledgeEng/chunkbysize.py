from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
import json
import logging
from time import time
import config as cfg

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)

model = cfg.embedding_model #"text-embedding-ada-002"
encoding = tiktoken.encoding_for_model(model)
chunk_size = cfg.chunksize#400


def chunk(data:str):
    time_start = gettime()
    logger.info(f'Chunking Process Using Model  text-embedding-ada-002 :: - {model} {int(time() * 1e+3) - time_start}ms') 
    chunk_texts = text_splitter.split_text(data)
    print(type(chunk_texts))
    chunklist = write_chunk_data(chunk_texts)
    return chunklist, tiktoken_len(data)

def tiktoken_len(text):
        tokens=encoding.encode(text)
        return len(tokens)    

def write_chunk_data (chunks):
        chunklist = []        
        i = 1
        for chunk in chunks:
            chunkdict = {}
            chunkdict[cfg.chunk_key] = i  
            chunkdict[cfg.size_key] = tiktoken_len(chunk)       
            chunkdict[cfg.text_key] = chunk
            i = i + 1
            chunklist.append(chunkdict)               
        return chunklist

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=chunk_size,
    chunk_overlap=cfg.chunk_overlap,
    length_function=tiktoken_len,
    separators=["\n\n", "\n", " ", ""]
)

def gettime():
    time_start = int(time() * 1e+3)
    return time_start
