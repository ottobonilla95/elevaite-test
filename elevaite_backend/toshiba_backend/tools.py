from utils import function_schema
import dotenv
import os
import requests
import re
from typing import List, Optional
from abbreviation_dict import MACHINE_ABBREVIATIONS
SEGMENT_NUM = 5

if not os.getenv("KUBERNETES_SERVICE_HOST"):
    dotenv.load_dotenv(".env.local")

@function_schema
def query_retriever(query: str, machine_types: Optional[List[str]] = None) -> list:
    """
    RETRIEVER TOOL

    Use this tool to query the Toshiba knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    If the user enters a machine type, add it to the machine_types list. For example, if the user asks "What is the part number for the Motorized Controller on the 6800?", add "6800" to the machine_types list.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="What is TAL"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"

    Example: query="diagnostic code X is 0 Y is 2"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".

    DO NOT ADD MACHINE TYPES TO THE QUERY. ONLY USE THE MACHINE TYPES LIST.
    FOR EXAMPLE, IF THE USER ASKS "What is the part number for the Motorized Controller on the 6800 System 7?",
    ADD "6800" TO THE MACHINE TYPES LIST.
    AND THEN QUERY WITH "part number for the Motorized Controller System 7"
    NOTICE HOW THE MACHINE NAME "SYSTEM 7" IS INCLUDED IN THE QUERY.

    INCLUDE THE MODEL NUMBER AND NAME IN THE QUERY IF AVAILABLE.
    FOR EXAMPLE, IF THE USER ASKS "SureBase (Machine Type: 4800 Model: 0xx) SLO motor part"
    ADD "4800" TO THE MACHINE TYPES LIST.
    AND THEN QUERY WITH "part number for the Motorized Controller for SureBase model 100".
    NOTICE HOW THE MACHINE NAME "SureBase" IS INCLUDED IN THE QUERY.
    
    VALID MACHINE TYPES:

    1. 2001
    2. 2011
    3. 4612
    4. 4613
    5. 4614
    6. 4615
    7. 4674
    8. 4683
    9. 4693
    10. 4694
    11. 4695
    12. 4750
    13. 4800
    14. 4810
    15. 4818
    16. 4825
    17. 4828
    18. 4835
    19. 4836
    20. 4838
    21. 4840
    22. 4845
    23. 4846
    24. 4851
    25. 4852
    26. 4855
    27. 4888
    28. 4900
    29. 4901
    30. 4910
    31. 6140
    32. 6183
    33. 6200
    34. 6201
    35. 6225
    36. 6700
    37. 6800
    38. 6900
    39. 7054
    40. 8368
    41. 4610
    42. 4679
    43. 4685
    44. 4698
    45. 4689
    46. 4820
    47. 6145
    48. 6149
    49. 6150
    50. 6160
    51. 6180
    52. 6260
    53. 9338

    If no machine types are provided, query without the machine type.
    """


    def get_response(url, params):
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"] + f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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
        "top_k": 60,
        "machine_types": machine_types

    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "machine_types": machine_types
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    # print(first_response+second_response)
    # print(sources+second_sources)
    res = "CONTEXT FROM RETRIEVER: \n\n"
    print(res+first_response+second_response)
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def walgreens_query_retriever(query: str) -> list:
    """"
    WALGREENS DATA RETRIEVER TOOL

    Use this tool to query the Toshiba Kroger knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Walgreens <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """


    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("WALGREENS_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def kroger_query_retriever(query: str) -> list:
    """"
    KROGER DATA RETRIEVER TOOL

    Use this tool to query the Toshiba Kroger knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Kroger <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """


    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("KROGER_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def tractor_query_retriever(query: str) -> list:
    """"
    TRACTOR SUPPLY DATA RETRIEVER TOOL

    Use this tool to query the Toshiba TRACTOR SUPPLY knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Tractor Supply <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """


    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("TRACTOR_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def sams_club_query_retriever(query: str) -> list:
    """"
    SAM'S CLUB DATA RETRIEVER TOOL

    Use this tool to query the Toshiba SAM'S CLUB knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Sam's Club <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("SAMS_CLUB_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def dollar_general_query_retriever(query: str) -> list:
    """"
    DOLLAR GENERAL DATA RETRIEVER TOOL

    Use this tool to query the Toshiba Dollar General knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Dollar General <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("DOLLAR_GENERAL_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def wegmans_query_retriever(query: str) -> list:
    """"
    WEGMANS DATA RETRIEVER TOOL

    Use this tool to query the Toshiba Wegmans knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Wegmans <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("WEGMANS_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def ross_query_retriever(query: str) -> list:
    """"
    DOLLAR GENERAL DATA RETRIEVER TOOL

    Use this tool to query the Toshiba Ross knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Ross <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("ROSS_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def costco_query_retriever(query: str) -> list:
    """"
    COSTCO DATA RETRIEVER TOOL

    Use this tool to query the Toshiba Costco base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Costco <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("COSTCO_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def whole_foods_query_retriever(query: str) -> list:
    """"
    WHOLE FOODS DATA RETRIEVER TOOL

    Use this tool to query the Toshiba Whole Foods knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Whole Foods <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("WHOLE_FOODS_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def bjs_query_retriever(query: str) -> list:
    """"
    BJ's DATA RETRIEVER TOOL

    Use this tool to query the Toshiba BJ's knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "BJs <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("BJS_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def alex_lee_query_retriever(query: str) -> list:
    """"
    ALEX LEE DATA RETRIEVER TOOL

    Use this tool to query the Toshiba ALEX LEE knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Alex Lee <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("ALEX_LEE_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def badger_query_retriever(query: str) -> list:
    """"
    BADGER DATA RETRIEVER TOOL

    Use this tool to query the Toshiba BADGER knowledge base.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"
    Example: query="What is the password for Bosch pin pad"

    Essentially, if the user asks "Badger <question>" then the query should be "<question>"

    Never query just the part number. Add a description. For example, if the user asks for "3AC01548000", query with "part number 3AC01548000".
    If the user asks a query with "MTM <model>" then query with "MTM <model>". For example, if the user asks "What is the part number for the MTM 036-W21 camera?", query with "MTM 036-W21 camera part number".
    """

    def get_response(url, params):
    # Make the POST request
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"Chunk {j}: "+chunk["chunk_text"]
                    pages = re.findall(r"\d+", str(chunk['page_info']))
                    res += f"\nSource for Chunk {j}: "
                    for page in pages:
                        print(chunk["filename"]+f" page {page}")
                        filename = chunk["filename"].strip(".pdf")
                        if "page" in filename:
                            res+=f"{filename}" + f" [aws_id: {filename}]\n"
                        else:
                            res += f"{filename} page {page}" + f" [aws_id: {filename}_page_{page}]\n"
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

    url = os.getenv("BADGER_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60
    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    # params = {
    #     "query": alt_query,
    #     "top_k": 60,
    #     "minimum_value": 0.1
    # }
    try:
        # second_response, second_sources = get_response(url, params)
        second_response, second_sources = ["", []]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    return [res+first_response+second_response, sources+second_sources]

@function_schema
def kg_database(query: str) -> list:
    """"
    KG Knowledge Graph DATABASE TOOL
    Any query that has "KG: <question>" should use this tool.

    Use this tool to query the Toshiba Service Request database.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    query = "What are the SR tickets closed on 2024-11-06 and who resolved them?"
    query = "Which SRs were resolved between 2024-11-05 and 2024-11-07?"
    query = "Which SRs closed in Florida and who handled them?"
    query = "What tickets were handled by Jason Hechler?"
    """
    st_url = os.getenv("KG_RETRIEVER_URL")+"/query-sr"
    params = {
        "query": query
    }
    try:
        print(st_url)
        print(params)
        response = requests.post(st_url, params=params)
        print(response.json())
        res = response.json()["answer"]
        return [res, []]
    except Exception as e:
        print(f"Failed to call SR database: {e}")
        return []

@function_schema
def sql_database(query: str) -> list:
    """"
    SQL DATABASE TOOL
    Any query that has "SQL: <question>" should use this tool.

    Use this tool to query the Toshiba SQL database.
    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    query = "What are the SR tickets closed on 2024-11-06 and who resolved them?"
    query = "Which SRs were resolved between 2024-11-05 and 2024-11-07?"
    query = "Which SRs closed in Florida and who handled them?"
    query = "What tickets were handled by Jason Hechler?"
    """
    st_url = os.getenv("SQL_RETRIEVER_URL")+"/query"
    params = {
        "query": query
    }
    try:
        print(st_url)
        print(params)
        response = requests.post(st_url, params=params)
        print(response.json())
        res = response.json()["response"]
        return [res, []]
    except Exception as e:
        print(f"Failed to call SR database: {e}")
        return []

tool_store = {
    "query_retriever": query_retriever,
    "walgreens_query_retriever": walgreens_query_retriever,
    "kroger_query_retriever": kroger_query_retriever,
    "dollar_general_query_retriever": dollar_general_query_retriever,
    "sams_club_query_retriever": sams_club_query_retriever,
    "tractor_query_retriever": tractor_query_retriever,
    "ross_query_retriever": ross_query_retriever,
    "wegmans_query_retriever": wegmans_query_retriever,
    "costco_query_retriever": costco_query_retriever,
    "whole_foods_query_retriever": whole_foods_query_retriever,
    "bjs_query_retriever": bjs_query_retriever,
    "alex_lee_query_retriever": alex_lee_query_retriever,
    "badger_query_retriever": badger_query_retriever,
    "kg_database": kg_database,
    "sql_database": sql_database,
}


tool_schemas = {
    "query_retriever": query_retriever.openai_schema,
    "walgreens_query_retriever": walgreens_query_retriever.openai_schema,
    "kroger_query_retriever": kroger_query_retriever.openai_schema,
    "dollar_general_query_retriever": dollar_general_query_retriever.openai_schema,
    "sams_club_query_retriever": sams_club_query_retriever.openai_schema,
    "tractor_query_retriever": tractor_query_retriever.openai_schema,
    "ross_query_retriever": ross_query_retriever.openai_schema,
    "wegmans_query_retriever": wegmans_query_retriever.openai_schema,
    "costco_query_retriever": costco_query_retriever.openai_schema,
    "whole_foods_query_retriever": whole_foods_query_retriever.openai_schema,
    "bjs_query_retriever": bjs_query_retriever.openai_schema,
    "alex_lee_query_retriever": alex_lee_query_retriever.openai_schema,
    "badger_query_retriever": badger_query_retriever.openai_schema,
    "kg_database": kg_database.openai_schema,
    "sql_database": sql_database.openai_schema,
}

# for key in query_retriever.openai_schema["function"]:
#     print(key)
#     print(query_retriever.openai_schema["function"][key])
# print(query_retriever("What is loader", "what is loader", ["6800"]))
# print(query_retriever.openai_schema)
# print("\n".join(f"{i+1}. {k}" for i, (k, v) in enumerate(MACHINE_ABBREVIATIONS.items())))
# print(tool_schemas["kroger_query_retriever"])
