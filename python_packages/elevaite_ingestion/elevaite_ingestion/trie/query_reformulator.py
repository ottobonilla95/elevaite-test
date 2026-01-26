import os
import string
import time
from openai import OpenAI
from trie_suggester import AbbreviationTrie
from abbreviation_dict import abbreviations
from dotenv import load_dotenv

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


def reformulate_query_with_llm(
    original_query: str, abbreviation_expansions: dict, openai_model="gpt-4o"
) -> str:
    if not abbreviation_expansions:
        return original_query

    expansion_context = ", ".join(
        f"{k} = {v}" for k, v in abbreviation_expansions.items()
    )

    system_prompt = """
You are a helpful AI assistant for query rewriting.
When users include abbreviations in their queries, expand them inline to clarify the meaning.
Make the reformulated query clear and complete, but keep it short.
"""

    user_prompt = f"""
Original Query: "{original_query}"
Known Abbreviations: {expansion_context}

Rewrite the query by expanding each abbreviation using its full form.
Keep both the full form and the abbreviation together, like this format:
"self-checkout (SCO)"

Rewritten Query:
"""

    response = client.chat.completions.create(
        model=openai_model,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": user_prompt.strip()},
        ],
        temperature=0.2,
    )

    return response.choices[0].message.content.strip()


if __name__ == "__main__":
    query = "for sco, provide assembly list"

    start_time_1 = time.time()
    expansions = extract_abbreviation_expansions(query)
    end_time_1 = time.time()

    print("\nFinal Expansions:", expansions)

    start_time_2 = time.time()
    rewritten = reformulate_query_with_llm(query, expansions)
    end_time_2 = time.time()

    print("\n==> Reformulated Query:", rewritten)
    print(f"==> Matching time: {(end_time_1 - start_time_1) * 1000:.3f} ms")
    print(f"==> Reformulation time: {(end_time_2 - start_time_2) * 1000:.3f} ms")
