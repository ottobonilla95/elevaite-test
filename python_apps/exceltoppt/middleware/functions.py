import os
import openai
from openai import OpenAI

from dotenv import load_dotenv




load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
current_woring_dir = os.path.dirname(os.path.realpath(__file__))



def api_openai(content: str):
    client = OpenAI()
    chat_completion = client.chat.completions.create(
        messages=[
            {"role":"system", "content":"You are a helpful assistant."},
            {"role":"user","content":content}

        ],
        model="gpt-4",
    )
    return(chat_completion.choices[0].message.content)



