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

def reformulate_query_with_llm(original_query: str, abbreviation_expansions: str, openai_model="gpt-4.1") -> str:
    # if not abbreviation_expansions:
    #     return original_query

    if abbreviation_expansions.items():
        expansion_context = ", ".join(f"{k} = {v}" for k, v in abbreviation_expansions.items())
    else:
        expansion_context = "No abbreviations found."
    machine_types = "\n".join(f"{i}. {k}" for i, (k, v) in enumerate(MACHINE_ABBREVIATIONS.items()))

    system_prompt = f"""
You are a helpful AI assistant for query rewriting.
When users include abbreviations in their queries, expand them inline to clarify the meaning.
When users enter machine type, expand it to the full machine name.
Make the reformulated query clear and complete, but keep it short.

### Machine Abbreviations
Machines are identified by a machine type, model, and name.
The machine type is the first number, and the model is the second number.
For example, in "4612 C01", "6145" is the machine type, "100" is the model, and SurePoint Mobile is the name.
The machine type is always 4 digits, and the model is always 3 digits.
In the data, {{'4612': "{{'C01': 'SurePoint Mobile'}}"}} means that the machine type is 4612, the model is C01, and the name is SurePoint Mobile.
{{'4835': "{{'All': 'NetVista Kiosk'}}"}} here All means all models of the machine type 4835 are NetVista Kiosk.
{{'4836': "{{'1xx': 'Anyplace Kiosk'}}"}} here 1xx means all models that start with 1 are Anyplace Kiosk.

The only machine types that exist are:
{machine_types}

LIST OF Primary CUSTOMERS:
1. Walgreens
2. Kroger
3. Sam's Club aka Sams
4. Tractor Supply
5. Dollar General
6. Wegmans
7. Ross
8. Costco
9. Whole Foods
10. BJs or BJ's
11. Alex Lee
12. Badger
###

EXAMPLES:
Original Query: "4610 1NR ink setting"
Known Abbreviations: 4610 = {{'1NR': 'SureMark Printer'}}
Rewritten Query: "SureMark Printer (Machine Type: 4610 Model: 1NR) ink setting"

Original Query: "4694 244 motor part"
Known Abbreviations: 4694 = {{'All': '4694'}}
Rewritten Query: "4694 (Machine Type: 4694 Model: 244) motor part"

Original Query: "4800-0xx SSD motor part"
Known Abbreviations: 4800 = {{'011': 'SureBase', '010': 'SureBase', '110': 'SurePoint Display'}}
Rewritten Query: "SureBase (Machine Type: 4800 Model: 0xx) Solid State Drive (SSD) part"

Original Query: "0365-K6A Kroger motor part"
Known Abbreviations: {{None}}
Rewritten Query: "0365-K6A Kroger motor part"

Original Query: "MTM 08R3-PU8 Walgreens printer part"
Known Abbreviations: {{None}}
Rewritten Query: "MTM 08R3-PU8 Walgreens printer part"

Notice how 0365 is not in the list of machine types, so it is not expanded.
###

Rewrite the query by expanding each abbreviation using its full form.
Keep both the full form and the abbreviation together, like this format:
"<Full Form> (<Abbreviation>)"

IF THE USER ENTERS AN INVALID MACHINE TYPE, MODEL OR NAME, IGNORE IT.
For example, if the user enters "036-100" which is not a valid machine type in the list above, ignore it and don't expand it.
For example, if the user enters "MTM 036-W04" then the user is referring to some other Machine type code, so ignore it and don't expand it.

TCx Sky is the operating system. Don't expand it.
Toshiba Part numbers are always 7 digits like 80Y1564 or 11-digit like 3AC01587100. Don't expand them.
"""

    user_prompt = f"""
Known Abbreviations: {expansion_context}
Original Query: "{original_query}"
Rewritten Query:
"""

    response = client.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()}
        ],
        temperature=0.1
    )
    # print(system_prompt)

    return response.choices[0].message.content.strip()

def reformulate_query_final(query: str) -> str:
    print("\nOriginal Query:", query)
    filtered_query = query.replace("?", " ")
    filtered_query = filtered_query.replace("-", " ")
    expansions = extract_abbreviation_expansions(filtered_query)

    print("\nFinal Expansions:", expansions)

    rewritten = reformulate_query_with_llm(query, expansions)

    return rewritten

# print(reformulate_query_final("0365-244 SLO motor part sams"))
