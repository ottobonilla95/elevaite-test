from langchain import PromptTemplate
from arlo_modules.components.websearch.cleaned_url_content import perform_web_search
from arlo_modules.agents.llm_service import LLMService
from arlo_modules.config.settings import Config, Prompts
from arlo_modules.components.preprocessors.url_processor import QueryBasedURLTextExtractor
from arlo_modules.components.websearch.websearch import BingWebSearcher
from arlo_modules.components.retrievers.dsRAG_f import KnowledgeBaseHandler
from dsrag.knowledge_base import KnowledgeBase
import os
import concurrent.futures

Config.OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
Config.BING_API_KEY = os.getenv("BING_API_KEY")
SCRAPER = os.getenv("SCRAPER")

kb_id = "arlo_v3"
storage_directory = "dsRAG_v3"
ARLO_KB = KnowledgeBase(kb_id=kb_id, storage_directory=storage_directory, exists_ok=True)


def arlo_web_search(query):
    relevant_text, search_results = perform_web_search(query, sites=None)

    urls_fetched = search_results
    return urls_fetched, relevant_text

def arlo_bing_web_search(query):
    bing = BingWebSearcher(Config.BING_API_KEY)
    print("Query: ", query)
    search_results = bing.search(str(query))
    if SCRAPER == "GPT":
        return [ i["url"] for i in search_results["webPages"]["value"]], " "

    filtered_articles = bing.filter_articles(search_results,filter_domains=["community.arlo", "kb.arlo"])
    urls_fetched = bing.urls_fetched(filtered_articles)
    return urls_fetched, " "

def arlo_web_search_processing(urls_fetched):
    url_processor = QueryBasedURLTextExtractor()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        web_articles = list(executor.map(url_processor.get_text_from_url, urls_fetched))

    fetched_articles = ''

    for idx,article in enumerate(web_articles):
        fetched_articles += f"Web Result {idx} " + article + '\n\n'
    return fetched_articles

def craft_query(query, chats, llm = LLMService("openai",api_key=Config.OPENAI_API_KEY), prompt=Prompts.CRAFT_QUERY_PROMPT):
    chat_history = []

    for i in range(len(chats)):
        chat_history.append((chats[i]['role'], chats[i]['content']))

    chat_history.append(("User", query))

    query_prompt = (prompt
                   + "\n\nHere is the chat history: \n" + "\n".join([i[0]+": "+i[1] for i in chat_history])
                    )

    for response in llm.generate_query(query_prompt,[]):
        yield response

def web_search_service(query):
    if os.environ.get("SEARCH_ENGINE") == "BING":
        urls_fetched, relevant_text = arlo_bing_web_search(query)
    else:
        urls_fetched, relevant_text = arlo_web_search(query)
        relevant_text = "\n\nInfo from Arlo.com " + relevant_text
    # print("URLs fetched: ", urls_fetched)
    urls_fetched = urls_fetched[:3]
    if SCRAPER == "GPT":
        return gpt_scraping(query, urls_fetched), urls_fetched
    else:
        fetched_articles = arlo_web_search_processing(urls_fetched)
        fetched_articles = fetched_articles + relevant_text
    # print(chats)
    return fetched_articles, urls_fetched

def web_summarize_service(query, fetched_articles, chats=[]):
    processed_articles = ""
    for response in chat_service(query, fetched_articles, chat_history=chats, streaming=False,
                                 system_prompt=Prompts.WEB_SEARCH_SYSTEM_PROMPT, qa=False):
        processed_articles += response
    return processed_articles

def chat_service(query, fetched_articles, chat_history=[], system_prompt="",
                 streaming=False, qa=False,qa_system_prompt="",
                 llm = LLMService("openai",api_key=Config.OPENAI_API_KEY)):
    streaming = False
    if system_prompt == "":
        system_prompt = Prompts.DEFAULT_SYSTEM_PROMPT

    prompt = PromptTemplate(
        template=system_prompt,
        input_variables=["fetched_knowledge", "history"],
    )

    try:
        system_prompt = prompt.partial(fetched_knowledge=fetched_articles).format()
    except KeyError:
        system_prompt = prompt.partial().format()


    if qa==True:
        first_response = ''
        for response in llm.generate_response(system_prompt, query, chat_history, streaming=streaming):
            first_response+= response
        print("First response: ", first_response)
        if qa_system_prompt == "":
            qa_chat_history = "\n".join([i[0]+": "+i[1] for i in chat_history])
            print("Reformulating response")
            for response in llm.generate_response(Prompts.QA_SYSTEM_PROMPT,
                                                  "\n\nHere is previous llm response : "+first_response+
                                                  "\n\nHere is user's query: "+query+
                                                    "\n\nHere is the past chat history: "+qa_chat_history,

                                                  [], streaming=streaming):
                yield response
        else:
            qa_chat_history = "\n".join([i[0] + ": " + i[1] for i in chat_history])
            print("Reformulating response")
            for response in llm.generate_response(qa_system_prompt,
                                                  "\n\nHere is previous llm response : "+first_response+
                                                  "\n\nHere is the past chat history: " + qa_chat_history+
                                                  "\n\nHere is user's query: "+query,
                                                  [], streaming=streaming):
                yield response
    else:
        for response in llm.generate_response(system_prompt, query, chat_history, streaming=streaming):
            yield response


def ds_rag_service(query):
    # Remove after testing
    # return "No relevant results found", []
    if ARLO_KB is None:
        return "No relevant results found",[]

    KB_handler = KnowledgeBaseHandler(ARLO_KB)
    res, retrieved_info_relevancy_score, chunks= KB_handler.retrieve_information(query)
    # print("Retrieved Info: ", retrieved_info)
    refs = [f"KB-{idx}-"+i["section_title"] for idx, i in enumerate(chunks)]
    return res, refs

def kb_summarize_service(query, fetched_articles, chats=[]):
    processed_articles = ""
    for response in chat_service(query, fetched_articles, chat_history=chats, streaming=False,
                                 system_prompt=Prompts.KB_SEARCH_SYSTEM_PROMPT, qa=False):
        processed_articles += response
    return processed_articles


def scraping_service(query, fetched_articles, chat_history=[], system_prompt="",
                 streaming=False, qa=False,qa_system_prompt="",
                 llm = LLMService("openai",api_key=Config.OPENAI_API_KEY, max_tokens=1000)):
    streaming = False
    if system_prompt == "":
        system_prompt = Prompts.DEFAULT_SYSTEM_PROMPT+fetched_articles
    else:
        system_prompt = system_prompt+fetched_articles

    for response in llm.generate_response(system_prompt, query, chat_history, streaming=streaming):
        yield response

def gpt_scraping(query, urls):
    urls ="-"*20+"Urls:"+"\n".join(urls)+"-"*20
    response = next(scraping_service(query, urls,
                       chat_history=[],
                       streaming=False,
                       system_prompt="""Go through the urls thoroughly, and read the relevant information to create a specific and precise response that answers the user's query.
                                    Extract as much relevant information as possible.
                                    DO NOT include suggestions to contact customer support.
                                    And only include the relevant information for the specific product or issue.
                                    If you can't find any information for the right product in the urls, just say "No relevant information found".""",
                       qa=False))
    return response