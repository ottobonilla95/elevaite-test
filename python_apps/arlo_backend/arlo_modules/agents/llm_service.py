# from langchain_community.chat_models import ChatOpenAI
import os

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
# from arlo_modules.components.postprocessors.processor import Post
import dotenv

class LLMService:
    def __init__(self, model='openai',api_key=None,max_tokens=500):
        if model == 'openai':
            self.llm = ChatOpenAI(
                model=os.environ.get("GPT_MODEL","gpt-4o"),
                temperature=0.2,
                max_tokens=max_tokens,
                timeout=60,
                max_retries=2,
                api_key=api_key
            )
        else:
            raise ValueError("Invalid model")

    def generate_response(self, system_prompt, query, history, streaming=False):
        prompt_chat = [("system", system_prompt)]+history + [("user", "{input}")]
        prompt_gen = ChatPromptTemplate.from_messages(prompt_chat)
        chain = prompt_gen | self.llm

        if streaming:
            for response_chunk in chain.stream({"input": query}, streaming=True):
                yield response_chunk.content
        else:
            response = chain.invoke({"input": query})
            yield response if isinstance(response, str) else response.content

    # def generate_qa_response(self, system_prompt, query, history, streaming=False):
    #     prompt_chat = history + [("system", "You are a helpful assistant"), ("user", "{input}")]
    #     prompt_gen = ChatPromptTemplate.from_messages(prompt_chat)
    #     chain = prompt_gen | self.llm
    #
    #     if streaming:
    #         for response_chunk in chain.stream({"input": system_prompt+query}, streaming=True):
    #             yield response_chunk.content
    #     else:
    #         response = chain.invoke({"input": system_prompt+query})
    #         yield response if isinstance(response, str) else response.content

    def generate_query(self, query, history, streaming=False):
        prompt_chat = history + [("user", "{input}")]
        prompt_gen = ChatPromptTemplate.from_messages(prompt_chat)
        chain = prompt_gen | self.llm

        if streaming:
            for response_chunk in chain.stream({"input": query}, streaming=True):
                yield response_chunk.content
        else:
            response = chain.invoke({"input": query})
            yield response if isinstance(response, str) else response.content



    # def controller_llm(self, system_prompt, query, history):
    #     """
    #     Temporarty solution to setting easy, medium, hard difficulty levels
    #     for system prompt
    #     """
    #     prompt_chat = history + [("system", f"{system_prompt}"),("user", "{input}")]
    #     prompt_gen = ChatPromptTemplate.from_messages(prompt_chat)
    #     chain = prompt_gen | self.llm
    #     response = chain.invoke({"input": query})
    #     output = response if isinstance(response, str) else response.content
    #     return PostProcessor.find_numbers(output)
