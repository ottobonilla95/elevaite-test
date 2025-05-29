from utils import function_schema
import dotenv
import os
import requests
import re

dotenv.load_dotenv(".env.local")

@function_schema
def query_retriever(query: str, alt_query: str) -> list:
    """"
    RETRIEVER TOOL

    Use this tool to query the Toshiba knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000", alt_query="what is AC01548000"
    Example: query="What is 2110", alt_query="description for code 2110"
    Example: query="What is 4348", alt_query="description for code 4348"
    Example: query="What is TAL", alt_query="Define TAL"
    Example: query="assembly name for part number 3AC01548000", alt_query="part number 3AC01548000 assembly name"
    Example: query="TAL parts list", alt_query="What are the parts in the TAL assembly"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    """


    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:2]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "

                references = ""
                for j,chunk in enumerate(segment["chunks"]):

                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    # print(pages)
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"] + f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
                    # references += f"File: {chunk['filename']}, Pages: {chunk['page_info']}\n"
                    #     if i==0:
                    if "page" in filename:
                        sources.append(f"{filename}" + f" [aws_id: {filename}] score: [{round(segment['score'], 2)}]")
                    else:
                        sources.append(
                            f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}] score: [{round(segment['score'], 2)}]")
            res += "Segment Ends\n"+"-"*5+"\n\n"

            return [res, sources]
        except Exception as e:
            print(f"Failed to call retriever: {e}")
            return ["",[]]

    url = os.getenv("RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    params = {
        "query": alt_query,
        "top_k": 60,
        "minimum_value": 0.1
    }
    try:
        second_response, second_sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    # print(first_response+second_response)
    # print(sources+second_sources)
    res = "CONTEXT FROM RETRIEVER: \n\n"
    print(res+first_response+second_response)
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def customer_query_retriever(query: str, alt_query: str) -> list:
    """"
    CUSTOMER DATA RETRIEVER TOOL

    Use this tool to query the Toshiba Customer knowledge base.
    Primary Customers include Walgreens, CVS, Kroger, etc.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000", alt_query="what is AC01548000"
    Example: query="What is 2110", alt_query="description for code 2110"
    Example: query="What is 4348", alt_query="description for code 4348"
    Example: query="stock room camera part number", alt_query="What's the stock room camera part number"
    Example: query="assembly name for part number 3AC01548000", alt_query="part number 3AC01548000 assembly name"
    Example: query="TAL parts list", alt_query="What are the parts in the TAL assembly"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    """


    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:2]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                # contextual_header = segment["chunks"][0].get("contextual_header","")
                # print("-"*100)
                # print(contextual_header)
                # print("-"*100)
                # skip_length = len(contextual_header) if contextual_header else 0
                # res += (contextual_header if contextual_header else ""+"\n")+"Context: "+"\n"
                # print(segment["score"])
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    # res += f"Contextual Header: {chunk['contextual_header']}\n"
                    # print("*"*100)
                    # print(chunk["chunk_text"])
                    # print("|"*100)
                    # print(chunk["chunk_text"].replace(contextual_header,""))
                    # print(chunk['page_info'])
                    # print("*"*100)
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    # if "-" in chunk['page_info']:
                    #     print("RANGE: ",chunk['page_info'])
                    #     pages = re.findall(r"\d+", str(chunk['page_info']))
                    #     pages = [int(page) for page in pages]
                    #     pages = list(range(pages[0], pages[1]+1))
                    #     print(f"RANGE: {pages}")
                    # else:
                    # print("Actual pages",chunk['page_info'])
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    # print(pages)
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
                    # references += f"File: {chunk['filename']}, Pages: {chunk['page_info']}\n"
                    #     if i==0:
                    if "page" in filename:
                        sources.append(f"{filename}" + f" [aws_id: {filename}] score: [{round(segment['score'], 2)}]")
                    else:
                        sources.append(
                            f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}] score: [{round(segment['score'], 2)}]")

                    # res += "\n"
                # res += f"Sources: {references}"
            res += "Segment Ends\n"+"-"*5+"\n\n"

            return [res, sources]
        except Exception as e:
            print(f"Failed to call retriever: {e}")
            return ["",[]]

    url = os.getenv("CUSTOMER_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    params = {
        "query": alt_query,
        "top_k": 60,
        "minimum_value": 0.1
    }
    try:
        second_response, second_sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    # print(first_response+second_response)
    # print(sources+second_sources)
    res = "CONTEXT FROM RETRIEVER: \n\n"
    # print(res+first_response+second_response)
    return [res+first_response+second_response, sources+second_sources]

tool_store = {
    "query_retriever": query_retriever,
    "customer_query_retriever": customer_query_retriever,
}

tool_schemas = {
    "query_retriever": query_retriever.openai_schema,
    "customer_query_retriever": customer_query_retriever.openai_schema,
}

# print(tool_schemas)
# res = query_retriever("What is TAL light", "define BCR")
# print(res[0])
# print(res[1])
#
# print("-"*100)
# res = customer_query_retriever("For Walgreens, what is the part number (pn) for a 4900-767 register base?", "what is the part number (pn) for a 4900-767 register base?")
# print(res[0])
# print(res[1])
