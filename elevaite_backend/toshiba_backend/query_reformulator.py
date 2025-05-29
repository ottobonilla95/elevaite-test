import os
import string
import time
from openai import OpenAI
from trie_suggester import AbbreviationTrie
from abbreviation_dict import abbreviations
from dotenv import load_dotenv
from abbreviation_dict import ABBREVIATION_TABLE

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
        for j in range(i + 1, min(i + 5, len(words) + 1)):
            phrase = " ".join(words[i:j]).strip(string.punctuation)
            suggestions = trie.get_all_with_prefix(phrase)
            if suggestions:
                print(f"==> Phrase: '{phrase}' ::==> Suggestions: {suggestions}")
            for key, mapped_value in suggestions:
                if key.lower() == phrase.lower():
                    matches[phrase] = mapped_value
    return matches

def reformulate_query_with_llm(original_query: str, abbreviation_expansions: str, openai_model="gpt-4o-mini") -> str:
    if not abbreviation_expansions:
        return original_query

    expansion_context = ", ".join(f"{k} = {v}" for k, v in abbreviation_expansions.items())

    system_prompt = f"""
You are a helpful AI assistant for query rewriting.
When users include abbreviations in their queries, expand them inline to clarify the meaning.
When users enter machine type, expand it to the full machine name.
Make the reformulated query clear and complete, but keep it short.

### Machine Abbreviations
Use the following table to expand machine type abbreviations:
Machine Abbreviations: {ABBREVIATION_TABLE}

EXAMPLE:
"6145 ink setting"
"TCx Printer (6145) ink setting"
###

Rewrite the query by expanding each abbreviation using its full form.
Keep both the full form and the abbreviation together, like this format:
"self-checkout (SCO)"
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
        temperature=0.2
    )

    return response.choices[0].message.content.strip()

def reformulate_query_final(query: str) -> str:
    expansions = extract_abbreviation_expansions(query)

    print("\nFinal Expansions:", expansions)

    rewritten = reformulate_query_with_llm(query, expansions)

    return rewritten

# print(reformulate_query_final("MTM 4614 Motor control pn"))