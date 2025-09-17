import os
from typing import List
from dotenv import load_dotenv
import openai

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    raise ValueError("OPENAI_API_KEY not found. Please set it in the environment variables.")

client = openai.OpenAI(api_key=api_key) 

def get_embedding(text: str) -> List[float]:
    try:
        response = client.embeddings.create(
            model="text-embedding-ada-002",
            input=[text] 
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error generating embedding: {e}")
        return [0] * 1536 


# if __name__ == "__main__":
#     sample_text = "OpenAI embeddings test."
#     embedding = get_embedding(sample_text)
#     print(f"Generated Embedding: {embedding[:5]}...")
