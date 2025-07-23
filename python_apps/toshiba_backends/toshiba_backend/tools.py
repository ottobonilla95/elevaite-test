from utils import function_schema
import dotenv
import os
import requests
import re
from typing import List, Optional
from abbreviation_dict import MACHINE_ABBREVIATIONS
SEGMENT_NUM = 5
TOP_GUN_SEGMENT_NUM = 2

if not os.getenv("KUBERNETES_SERVICE_HOST"):
    dotenv.load_dotenv(".env.local")

def customer_resolver(collection_id: str) -> str:
    customer_mapping = {
            "toshiba_demo_4": "All Customers", #
            "toshiba_alex_lee": "Alex Lee",
            "toshiba_at_home": "At Home", #
            "toshiba_badger": "Badger", #
            "toshiba_bass_pro": "Bass Pro",
            "toshiba_bjs": "BJS", #
            "toshiba_best_buy": "Best Buy", #
            "toshiba_camers_al": "CAM",
            "toshiba_coach": "Coach",
            "toshiba_costco": "Costco", #
            "toshiba_cost_plus_world_market": "Cost Plus World Market",
            "toshiba_cvs": "CVS",
            "toshiba_dollar_general": "Dollar General", #
            "toshiba_enterprise": "Enterprise",
            "toshiba_event_network": "Event network",
            "toshiba_foodland": "Foodland",
            "toshiba_GNC": "GNC",
            "toshiba_harbor_freight": "Harbor Freight",
            "toshiba_hudson_news": "Hudson News",
            "toshiba_idkids": "IDKIDS",
            "toshiba_kroger": "Kroger", #
            "toshiba_quickchek": "QuickChek",
            "toshiba_ross": "Ross", #
            "toshiba_saks": "Saks",
            "toshiba_sams_club": "Sams Club", #
            "toshiba_spartan_nash": "Spartan Nash",
            "toshiba_tca": "Travel Centers of America TCA", #
            "toshiba_tractor_supply": "TSC Tractor Supply", #
            "toshiba_walgreens": "Walgreens", #
            "toshiba_wegmans": "Wegmans",
            "toshiba_whole_foods": "Whole Foods" #
    }
    return customer_mapping.get(collection_id, "All Customers")


def top_gun_query_retriever(query: str, collection_id: Optional[str] = None, machine_types: Optional[List[str]] = None) -> list:
    def get_response(url, params):
        try:
            response = requests.post(url, params=params)
            res = ""
            sources = []
            segments = response.json()["selected_segments"][:TOP_GUN_SEGMENT_NUM]
            for i,segment in enumerate(segments):
                res += "*"*5+f"\n\nSegment Begins: "+"\n" #+"Contextual Header: "
                references = ""
                for j,chunk in enumerate(segment["chunks"]):
                    res += f"\nChunk {j}: "+chunk["chunk_text"]+"\n"+"Datetime: "+chunk.get("email_sent_datetime", "")
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
    url = os.getenv("TOP_GUN_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60,
        # "machine_types": machine_types,
        "customer_name": customer_resolver(collection_id)

    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]
    return [first_response, sources]


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

    url = os.getenv("TGCS_RETRIEVER_URL") + "/query-chunks"
    params = {
        "query": query,
        "top_k": 60,
        "machine_types": machine_types,
        "collection_id": "toshiba_demo_4"

    }
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        first_response, sources = ["",[]]

    try:
        # second_response, second_sources = get_response(url, params)
        # second_response, second_sources = top_gun_query_retriever(query, collection_id="toshiba_demo_4")
        second_response, second_sources = ["",[]]

    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    # print(first_response+second_response)
    # print(sources+second_sources)
    res = "CONTEXT FROM RETRIEVER: \n\n"
    # top_gun_header = "\n\nCONTEXT FROM TOSHIBA TOP GUN EMAILS: \n\n"
    # return [res+first_response+top_gun_header+second_response, sources+second_sources]
    return [res+first_response, sources]


@function_schema
def customer_query_retriever(query: str, collection_id: str) -> list:
    """"
    TOSHIBA CUSTOMER DATA RETRIEVER TOOL

    Use this tool to query the Toshiba's Customer knowledge base.
    This tool is only used for customer-specific information.
    List of customers and their collection_ids:
    1. Walgreens: toshiba_walgreens
    2. Kroger: toshiba_kroger (Note that Harris Teeter is also included in this collection)
    3. Sam's Club: toshiba_sams_club
    4. Tractor Supply: toshiba_tractor_supply
    5. Dollar General: toshiba_dollar_general
    6. Wegmans: toshiba_wegmans
    7. Ross: toshiba_ross
    8. Costco: toshiba_costco
    9. Whole Foods: toshiba_whole_foods
    10. BJs: toshiba_bjs
    11. Alex Lee: toshiba_alex_lee
    12. Badger: toshiba_badger
    13. Best Buy: toshiba_best_buy
    14. GNC: toshiba_GNC
    15. Coach: toshiba_coach
    16. QuickChek: toshiba_quickchek
    16. CAM: toshiba_cameras_al
    17. Hudson News: toshiba_hudson_news
    18. IDKIDS: toshiba_idkids
    19. Saks: toshiba_saks * For Saks, if the user asks for client advocates, use query "Client Advocate" instead of "Client Advocates list"
    20. CVS: toshiba_cvs
    21. At Home: toshiba_at_home
    22. Harbor Freight: toshiba_harbor_freight
    23. TCA: toshiba_tca * TCA is also known as Travel Centers of America
    24. Spartan Nash: toshiba_spartan_nash
    25. Event network: toshiba_event_network
    26. Bass Pro: toshiba_bass_pro * For Bass Pro, if the user asks for client advocates, use query "Client Advocate" instead of "Client Advocates list"
    27. Foodland: toshiba_foodland
    28. Cost Plus World Market: toshiba_cost_plus_world_market
    29. Enterprise: toshiba_enterprise
    30. Red Apple: toshiba_red_apple
    31. Yum Brands: toshiba_yum_brands * Note that KFC is also included in this collection
    32. Bealls: toshiba_bealls
    33. Disney: toshiba_disney
    34. Ovation Foods: toshiba_ovation_foods
    35. Nike: toshiba_nike
    36. ABC Stores: toshiba_abc_stores
    37. Tommy Bahama: toshiba_tommy_bahama
    38. Gordon Food Service: toshiba_gordon_food_service
    39. Michaels: toshiba_michaels

    Use toshiba_demo_4 if the customer retriever fails to return any relevant results

    Questions can include part numbers, assembly names, abbreviations, descriptions and general queries.

    EXAMPLES:
    Example: query="part number AC01548000"
    Example: query="What is 2110"
    Example: query="stock room camera part number"
    Example: query="assembly name for part number 3AC01548000"
    Example: query="TAL parts list"
    Example: query="Client Advocates list"

    Essentially, if the user asks "Walgreens <question>" then the query should be "<question>" and the collection_id should be "toshiba_walgreens"

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
                        # print(chunk["filename"]+f" page {page}")
                        print(chunk["filename"])
                        filename = chunk["filename"].removesuffix(".pdf")
                        print(filename)
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

    url = os.getenv("CUSTOMER_RETRIEVER_URL") + "/query-chunks"
    if collection_id == "toshiba_walgreens":
        collection_id = "toshiba_walgreen"
    if collection_id == "toshiba_harbor_freight":
        collection_id = "toshiba_harbour_frieght"
    params = {
        "query": query,
        "top_k": 60,
        "collection_id": collection_id
    }
    first_response, sources = ["", []]
    try:
        first_response, sources = get_response(url, params)
    except Exception as e:
        print(f"Failed to call retriever: {e}")

    try:
        # second_response, second_sources = top_gun_query_retriever(query, collection_id=collection_id)
        second_response, second_sources = ["",[]]
    except Exception as e:
        print(f"Failed to call retriever: {e}")
        second_response, second_sources = ["",[]]
    res = "CONTEXT FROM RETRIEVER: \n\n"
    # top_gun_header = "\n\nCONTEXT FROM TOSHIBA TOP GUN EMAILS: \n\n"
    # return [res+first_response+top_gun_header+second_response, sources+second_sources]
    return [res+first_response, sources]


@function_schema
def sql_database(query: str) -> list:
    """"
    SQL DATABASE TOOL
    Any query that has "SQL: <question>" MUST use this tool.

    Use this tool to query the Toshiba Service Request database.
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
    "sql_database": sql_database,
    "customer_query_retriever": customer_query_retriever,
}


tool_schemas = {
    "query_retriever": query_retriever.openai_schema,
    "sql_database": sql_database.openai_schema,
    "customer_query_retriever": customer_query_retriever.openai_schema,
}


print(customer_query_retriever("Client advocates list", collection_id="toshiba_event_network")[0])