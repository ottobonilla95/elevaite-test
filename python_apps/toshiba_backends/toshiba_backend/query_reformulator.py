import os
import string
import time
from openai import OpenAI
from trie_suggester import AbbreviationTrie
from abbreviation_dict import abbreviations, MACHINE_ABBREVIATIONS
from dotenv import load_dotenv
from abbreviation_dict import ABBREVIATION_TABLE

if not os.getenv("KUBERNETES_SERVICE_HOST"):
    load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)

trie = AbbreviationTrie()
for abbr, full in abbreviations.items():
    trie.insert(abbr, full)
    trie.insert(full, abbr)

def extract_abbreviation_expansions(query: str) -> dict:
    words = query.split()
    matches = {}

    print("\n check phrases in user query using Trie:")
    for i in range(len(words)):
        if words[i] in MACHINE_ABBREVIATIONS:
            matches[words[i]] = str(MACHINE_ABBREVIATIONS[words[i]])
        for j in range(i + 1, min(i + 5, len(words) + 1)):
            phrase = " ".join(words[i:j]).strip(string.punctuation)
            suggestions = trie.get_all_with_prefix(phrase)
            if suggestions:
                print(f"==> Phrase: '{phrase}' ::==> Suggestions: {suggestions}")
            for key, mapped_value in suggestions:
                if key == phrase:
                    matches[phrase] = mapped_value


    return matches

def reformulate_query_with_llm(original_query: str, abbreviation_expansions: dict, openai_model="gpt-4.1", chat_history: list = []) -> str:
    # if not abbreviation_expansions:
    #     return original_query

    if abbreviation_expansions.items():
        expansion_context = ", ".join(f"{k} = {v}" for k, v in abbreviation_expansions.items())
    else:
        expansion_context = "No abbreviations found."
    machine_types = "\n".join(f"{i}. {k}" for i, (k, v) in enumerate(MACHINE_ABBREVIATIONS.items()))

    system_prompt = f"""
    You are a helpful AI assistant for query rewriting. Your output will be sent to another system that needs clear, expanded queries.

    Your job is to:
    1. Expand machine codes or abbreviations inline using known names.
    2. Reformulate vague or incomplete queries using context from chat history.
    3. If the query is complete and not affected by abbreviations or history, return it as-is.
    4. Ensure the result is meaningful, well-formed, and clearly expresses user intent.

    ### MACHINE EXPANSION RULES:
    - Machine entries follow this format: Machine Type (4 digits), Model (3 alphanumeric), and Name.
    - Expand to this format: "<Full Name> (Machine Type: XXXX Model: XXX)"
    - Use partial rules if applicable:
        - {{'4835': {{'All': 'NetVista Kiosk'}}}} → All models
        - {{'4836': {{'1xx': 'Anyplace Kiosk'}}}} → Models starting with 1
    - If only the machine type is provided, use the most common or relevant model/name.

    Expand **only** if the machine type is in this list:
    {machine_types}

    ### CUSTOMER NAMES:
    Walgreens, Kroger (note that Harris Teeter is the same as Kroger, so refer to it as Kroger), Sam's Club, Tractor Supply, 
    Dollar General, Wegmans, Ross, Costco, Whole Foods, BJs or BJ's, Alex Lee, Badger, Best Buy, CAM, Hudson News, IDKIDS, 
    Saks, CVS, At Home, Harbor Freight, Spartan Nash, Event network, Foodland, Cost Plus World Market, Enterprise, 
    Red Apple, Bealls, Disney, Ovation Foods, 
    Yum Brands (note that KFC is the same as Yum Brands, so refer to it as Yum Brands), Nike, ABC Stores, 
    Tommy Bahama, Gordon Food Service, Michaels, Dunn Edwards, BP, Northern Tool, Winn Dixie, PVH, 
    Tommy Hilfiger, Calvin Klein, Ahold, Stop & Shop, Giant Martin's, Bfresh, Fresh Market, Times Supermarkets, 
    and MLSE (Maple Leaf Sports & Entertainment).

    ### DO NOT EXPAND:
    - Invalid machine types (not in the list)
    - MTM codes without valid types
    - "TCx Sky" (OS)
    - Toshiba part numbers (e.g. 80Y1564, 3AC01587100)

    ### IF NO REWRITE IS NEEDED:
    - If the input is a greeting or unrelated small talk (e.g. "hello", "thanks", "okay"), pass it through exactly.
    - If the query is already clear and not affected by known abbreviations or context, return it as-is.

    ### EXAMPLES:

    Original: "hello"
    → Rewritten: "hello"

    Original: "foyer part number"
    Chat history: "search in 7610"
    → Rewritten: "Foyer part number in System 42 (Machine Type: 7610)"
    NOTICE HOW NO MODEL NUMBER IS PROVIDED, SO IT IS NOT INCLUDED IN THE QUERY.

    Original: "4694 244 motor part"
    → Rewritten: "4694 (Machine Type: 4694 Model: 244) motor part"
    NOTICE HOW THE MODEL NUMBER IS PROVIDED, SO IT IS INCLUDED IN THE QUERY.

    Original: "MTM 036-W04"
    → Rewritten: "MTM 036-W04" (invalid machine type, no expansion)
    
    Original: "conveyor belt part number in 6200"
    → Rewritten: "Foyer part number in System 42 (Machine Type: 7610)"
    NOTICE HOW NO MODEL NUMBER IS PROVIDED, SO IT IS NOT INCLUDED IN THE QUERY.

    Rewritten queries must be natural and complete, as if a human rephrased them for clarity — but only when needed.

    ###
    """

    user_prompt = f"""
    Known Abbreviations: {expansion_context}
    Original Query: "{original_query}"

    Chat History: {chat_history}
    
    IMPORTANT:
    - If the query begins with "KG:", "CAM: " or "SQL:", do not rewrite it. These are special queries that should be passed through exactly.
    - For example, if the query is "KG: What are the SR tickets closed on 2024-11-06 and who resolved them?", do not rewrite it.

    Rewrite the query as follows:
    - Expand abbreviations and machine codes inline, using this format: "<Full Name> (<Abbreviation>)"
    - If the query is vague (e.g. "search in 7610"), combine it with previous relevant messages to form a natural, clear query.
    - If the chat history or known abbreviations do not help clarify the query, return the query exactly as written.
    - If the input is casual conversation (e.g. "hello", "thanks"), pass it through without rewriting.

    Rewritten Query:
    """

    response = client.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": system_prompt.strip()}]
        + chat_history +
            [{"role": "user", "content": user_prompt.strip()}
        ],
        temperature=0.6
    )
    # print(system_prompt)

    return response.choices[0].message.content.strip()

def reformulate_query_final(query: str, chat_history: list) -> str:
    print("\nOriginal Query:", query)
    filtered_query = query.replace("?", " ")
    filtered_query = filtered_query.replace("-", " ")
    expansions = extract_abbreviation_expansions(filtered_query)

    print("\nFinal Expansions:", expansions)

    rewritten = reformulate_query_with_llm(original_query=query,
                                           abbreviation_expansions=expansions,
                                           chat_history=chat_history)

    return rewritten

# print(reformulate_query_final("0365-244 SLO motor part sams"))
