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

oem_mapping = {'FSCO': 'Kroger', 'Fujitsu': 'Kroger', 'Bosch': 'Walgreens', 'PVM': 'Walgreens', 'DVR': 'Walgreens', 'Zooter': 'Kroger', 'Lenovo': 'Kroger', 'Dell': "Sam's Club", 'Access Point': 'Kroger', 'AP': 'Kroger', 'Cherry POS': 'Tractor Supply', 'Honeywell': 'Tractor Supply', 'Epson': 'Tractor Supply', 'Veriphone': 'Tractor Supply', 'Elo': 'Tractor Supply', 'Aruba': 'Kroger', 'Cisco': 'Tractor Supply', 'Juniper': 'Tractor Supply', 'Inseego': 'Tractor Supply', 'KVM': 'Kroger', 'Stockyard': 'Tractor Supply', 'Lexmark': 'Tractor Supply', 'Barix': 'Tractor Supply', 'Cradlepoint': 'Tractor Supply', 'Garden Center': 'Tractor Supply', 'Palo Alto': 'Tractor Supply', 'ENS': 'Tractor Supply', 'Yealink': 'Tractor Supply', 'Grandstream': 'Tractor Supply', 'Ucaas': 'Tractor Supply', 'Phoenix America': 'Tractor Supply', 'T-mobile': 'Tractor Supply', 'Algo': 'Tractor Supply', 'Eaton': 'Tractor Supply', 'Theatro': 'Tractor Supply', 'Accu-Time Systems': "Sam's Club", 'Anixter': "Sam's Club", 'Apple': "Sam's Club", 'ATEB': "Sam's Club", 'BNSF': "Sam's Club", 'Cable Electronics Inc': "Sam's Club", 'CDW Direct': "Sam's Club", 'CTA': "Sam's Club", 'First Data': "Sam's Club", 'HP': "Sam's Club", 'Ingenico': "Sam's Club", 'Invue': "Sam's Club", 'Invue Security Products': "Sam's Club", 'KIOSK': "Sam's Club", 'Mist': "Sam's Club", 'NCR': "Sam's Club", 'Par Tech': "Sam's Club", 'Perc. Opt.': "Sam's Club", 'Prime': "Sam's Club", 'SCHNEIDER ELECTRIC IT USA INC': "Sam's Club", 'Star Tech': "Sam's Club", 'Tellermate Inc': "Sam's Club", 'Toshiba': "Sam's Club", 'Velcro': "Sam's Club", 'Verifone': "Sam's Club", 'Zebra': "Sam's Club", 'IBM': 'Kroger', 'Mettler Toledo': 'Kroger', 'Datalogic': 'Kroger', 'Corn Fiber': 'Kroger', 'T-flex': 'Kroger', 'Teleq': 'Kroger', 'Pay Station': 'Kroger', 'Gryphon': 'Kroger', 'RJ45 Patch Cable': 'Kroger', 'Compulink': 'Kroger', 'Tripp Lite': 'Kroger', 'Lock-In': 'Kroger', 'Lock In': 'Kroger', 'CTG': 'Kroger', 'Insignia': 'Kroger', 'Panduit': 'Kroger', 'IOGEAR': 'Kroger', 'Avant': 'Kroger', 'StarTech': 'Kroger', 'Powercart': 'Kroger', 'ONC': 'Kroger', 'Oneac': 'Kroger', 'Genesis': 'Kroger', 'NextGen': 'Kroger', 'Alarm': 'Kroger', 'Telequip': 'Kroger', 'FC###': 'Kroger', 'Edgeport': 'Kroger', 'Bill dispenser': 'Kroger', 'Cash Acceptor': 'Kroger', 'Interstate': 'Kroger', 'Well Shin': 'Kroger', 'PSC': 'Kroger', 'Load cell': 'Kroger', 'Magellan': 'Kroger', 'Scaletron': 'Kroger', 'PowerVar': 'Kroger', 'Shekel': 'Kroger', 'Pand': 'Kroger', 'Cybex': 'Kroger', 'Avalan': 'Kroger', 'Fuel Controller': 'Kroger', 'Controller Unit Controller': 'Toshiba', 'Payment Unit Controller': 'Toshiba', 'Scanning Unit Controller': 'Toshiba', 'SUC': 'Toshiba', 'CUC': 'Toshiba', 'PUC': 'Toshiba', 'curtain': 'Kroger', 'flat pack': 'Kroger', 'APC': 'BJs', 'UPS': 'Kroger', 'Tripp Lite KVM': 'BJs', 'Fujitsu Monitor': 'Ross', 'Fujitsu D75': 'Ross', 'VISTA': 'Walgreens', 'Ademco': 'Walgreens', 'Altronix': 'Walgreens', 'Sentrol': 'Walgreens', 'Teldat': 'Walgreens', 'Yuasa': 'Walgreens', 'Equinox': 'Walgreens', 'Aigis Mechtronics': 'Walgreens', 'Aten': 'Walgreens', 'Clinton Electronics (CE)': 'Walgreens', 'Grainger': 'Walgreens', 'Workstation': 'Walgreens', 'Meraki': 'Walgreens', 'analog box camera': 'Walgreens', 'Indyme': 'Walgreens', 'WYSE': 'Walgreens', 'Samsung': 'Walgreens', 'HP engage go': 'Walgreens', 'HP MP9': 'Walgreens', 'Avaya': 'Walgreens', 'TM-T88': 'Walgreens', 'T88': 'Walgreens', 'daktronics': 'Walgreens', 'Sensormatic': 'Zara', 'Nixdorf': 'Zara', 'Surepoint Display': 'Toshiba', 'Overhead Paging': 'Walgreens', 'Rally bar': 'Kroger', 'E & M': 'Walgreens', 'spectralink': 'Kroger', 'Catalina': 'Walgreens'}


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
    - Expand to this format: "<Full Name> (Machine Type: XXXX Model: XXX)" if the model number is provided.
    - Use partial rules if applicable:
        - {{'4835': {{'All': 'NetVista Kiosk'}}}} → All models
        - {{'4836': {{'1xx': 'Anyplace Kiosk'}}}} → Models starting with 1
    - If only the machine type is provided, only expand the machine type.

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
    MLSE (Maple Leaf Sports & Entertainment), Coach, TCA (Travel Centers of America), Bass Pro, Kirkland, 
    Simmons Bank, GNC, Zara, STCR, Boston Pizza, LCBO (Liquor Control Board of Ontario), NLLC (Newfoundland and Labrador Liquor Corporation)
    , Husky, Princess Auto, Albertson, Signature Aviation, New Brunswick Liquor Corporation (Alcool NB Liquor Corporation or ANBL).
    
    If the customer name is not in the query, but has one of the OEM names in the query, add the customer name to the query.
    Here is the mapping of OEM names to their respective customers:
    {oem_mapping}

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
    - If the query begins with "KG:", "CAM: " or "SR Data:", keep the prefix "KG:", "CAM: " or "SR Data:". 
    - For example, if the query is "SR Data: How many SR tickets were done for 4694 in march 2020", then expand it to,
    "SR Data: How many SR tickets were done for 4694 (Machine Type: 4694 Model: 244) in march 2020"

    Rewrite the query as follows:
    - Expand abbreviations and machine codes inline, using this format: "<Full Name> (<Abbreviation>)"
    - If the query is vague (e.g. "search in 7610"), combine it with previous relevant messages to form a natural, clear query.
    - If the chat history or known abbreviations do not help clarify the query, return the query exactly as written.
    - If the input is casual conversation (e.g. "hello", "thanks"), pass it through without rewriting.
    - DO NOT INCLUDE MODEL NUMBERS IF THE USER DID NOT SPECIFY THEM. 
    For example, if the user asks "what is the part number for the motorized controller in 6800?", do not rewrite it to "what is the part number for the motorized controller in System 7 (Machine Type:6800 model: 100)?" because the user did not specify the model number.
    You should re-write the query to "what is the part number for the motorized controller in System 7 (Machine Type:6800)?"

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
