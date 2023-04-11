from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import qdrant_client
from qdrant_client import QdrantClient
import openai
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
embedding_model = "text-embedding-ada-002"
collection_name = "kbDocs_openAI"
MODEL = "text-embedding-ada-002"
OPEN_AI_KEY = "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"
DEFAULT_RESPONSE = "Sorry, I don't have the relevant knowledge base to answer this query at this time. I will keep learning as relevant documents \
                    related to this query is added."
INVALID_REQUEST = "Sorry, the token limit has been breached for this query. Please try splitting the input into smaller chunks."
DEFAULT_THRESHOLD = 0.77

qdrant_client = QdrantClient(
    url="https://a29a4a5f-b731-4ffa-befd-5c3f702c66f3.us-east-1-0.aws.cloud.qdrant.io:6333", 
    api_key="bD7Kx0EQ3hPe2FJjzjNpXr7E4mZatk9MAhqwNHi4EBOPdNqKcRW7HA"
)

logging.basicConfig(level=logging.INFO,format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(__file__)

@app.get("/")
def read_root():
    return {"Hello": "World"}

@app.get("/query")
def get_query_completion(query: str):
    # convert to vector
    openai.api_key = OPEN_AI_KEY
    time_start = int(time() * 1e+3)
    try:
        vectorized_ask = openai.Embedding.create( input= query, engine=MODEL)
    except:
        return get_default_response()
    logger.info(f'Vectorized Query - {query} {int(time() * 1e+3) - time_start}ms')
    # get similar results
    time_start = int(time() * 1e+3)
    semantic_text_results = get_semantic_search_results(vectorized_ask)
    top_similar_results_count = len(semantic_text_results) if semantic_text_results else 0
    logger.info(f'Semantic results fetched - {top_similar_results_count} chunks in {int(time() * 1e+3) - time_start}ms')
    
    for idx, result in enumerate(semantic_text_results):
        logger.info(f'Result {idx} - Text: {result.payload["Text"]}, Score: {result.score}')
    
    if is_above_threshold(semantic_text_results) == True:
        query_completion = get_query_completion_result(query, semantic_text_results)
        if query_completion == get_invalid_request():
            return get_invalid_request()
        return get_response(query_completion, semantic_text_results)
    else:
        context = "What additional details need to be gathererd from customer to solve the below incident\n"+ query \
        + "\n Provide your response embedded in ol tags HTML format."
        completion = openai.Completion.create(model="text-davinci-003", prompt=context, temperature=0, max_tokens=3000)
        return {"text":"Please gather these additional details from the customer: \n" + completion.choices[0].text}

def get_semantic_search_results(vectorized_ask):
    return qdrant_client.search(
        collection_name=collection_name,
        query_vector=vectorized_ask["data"][0]["embedding"],
        limit=3,
        with_vectors=True,
        with_payload=True,
    )

def get_query_completion_result(query: str, semantic_text_results):
    time_start = int(time() * 1e+3)
    context = "Provide recommendation for the following text"+ query + "Use only the context below to answer \n" \
        + get_context(semantic_text_results) \
        + "\n Provide the answer in HTML format. \nGive the answer in sequence of steps whenever necessary."
    try:
        completion = openai.Completion.create(model="text-davinci-003", prompt=context, temperature=0, max_tokens=3000)
    except openai.error.InvalidRequestError:
        return get_invalid_request()
    except:
        return get_default_response()
    logger.info(f'Query Completion Elapsed Time - {int(time() * 1e+3) - time_start}ms')
    return completion

def get_context(semantic_results: list):
    list_of_similar_results = [result.payload['Text'] for result in semantic_results if result.payload]
    return ' '.join(list_of_similar_results)

def get_response(query_completion, semantic_results: list):
    openai.api_key = OPEN_AI_KEY
    response_dict = {}
    response_dict["text"] = query_completion.choices[0].text if query_completion and query_completion.choices else ''
    for idx, result in enumerate(semantic_results):
        response_key = (f'url_{idx}', f'topic_{idx}')
        response_val = (result.payload['url'], result.payload['Sub-Topic']) if result.payload else ''
        response_dict[response_key[0]] = response_val[0]
        response_dict[response_key[1]] = response_val[1]
    return response_dict

def get_default_response():
    return {"text" : DEFAULT_RESPONSE}
def get_invalid_request():
    return {"text" : INVALID_REQUEST}


def is_above_threshold(sementic_text_results):
    is_above_threshold = False if len(sementic_text_results) <= 0 or sementic_text_results[0].score <= DEFAULT_THRESHOLD else True
    logger.info(f'Results above threshold - {is_above_threshold}')
    return is_above_threshold
