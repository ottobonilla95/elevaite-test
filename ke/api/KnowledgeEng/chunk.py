from langchain.text_splitter import RecursiveCharacterTextSplitter
import tiktoken
import chunkbysize as chunksize
import json
import logging
from time import time
import config as cfg


logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__file__)


def chunkdata(data:str):
    time_start = gettime()
    logger.info(f'Chunking Process Begins :: -  {int(time() * 1e+3) - time_start}ms')
    j_data = data 
    chunk_texts, totaltokens = chunksize.chunk(j_data["Text"])
    output_fields = write_common_fields(j_data)
    output_fields[cfg.totaltok_key] = totaltokens
    output_fields[cfg.chunks_key] = chunk_texts    
    json_data = json.dumps(output_fields, ensure_ascii=False).encode('utf-8').decode()
    logger.info(f'Chunking Process Completed :: -  {int(time() * 1e+3) - time_start}ms')         
    return json_data

def write_common_fields(data):
    dat_output = {}
    dat_output[cfg.summary_key] = data[cfg.summary_key]
    dat_output[cfg.doctype_key] =  data[cfg.doctype_key]
    dat_output[cfg.docid_key] = data[cfg.docid_key]
    dat_output[cfg.product_key] = data[cfg.product_key]
    dat_output[cfg.version_key] = data[cfg.version_key]
    dat_output[cfg.topic_key] = data[cfg.topic_key]
    dat_output[cfg.subtopic_key] =  data[cfg.subtopic_key]
    dat_output[cfg.url_key] = data[cfg.url_key]
    dat_output[cfg.source_key] = data[cfg.source_key]            
    return dat_output
    
def gettime():
    time_start = int(time() * 1e+3)
    return time_start