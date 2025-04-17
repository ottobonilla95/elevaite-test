import os
import uuid
from typing import Dict, List, Optional
from langchain.prompts import ChatPromptTemplate, PromptTemplate, HumanMessagePromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains import create_extraction_chain_pydantic
from dotenv import load_dotenv
from langchain_core.pydantic_v1 import BaseModel

load_dotenv()

class AgenticChunker:
    def __init__(self, openai_api_key=None):
        self.chunks = {}
        self.id_truncate_limit = 5

        if openai_api_key is None:
            openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key is None:
            raise ValueError("API key is not provided and not found in environment variables")

        self.llm = ChatOpenAI(model='gpt-4o-mini', openai_api_key=openai_api_key, temperature=0)

    def _get_new_chunk_summary(self, paragraph_text, whole_document):
        """
        Generates a succinct context for the given chunk based on Anthropic's retrieval methodology.
        """
        anthropic_prompt = """<document>
        {WHOLE_DOCUMENT}
        </document>
        Here is the chunk we want to situate within the whole document
        <chunk>
        {CHUNK_CONTENT}
        </chunk>
        Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""

        prompt_template = PromptTemplate(
            input_variables=['WHOLE_DOCUMENT', 'CHUNK_CONTENT'],
            template=anthropic_prompt
        )

        human_message_prompt = HumanMessagePromptTemplate(prompt=prompt_template)

        final_prompt = ChatPromptTemplate(
            input_variables=['WHOLE_DOCUMENT', 'CHUNK_CONTENT'],
            messages=[human_message_prompt]
        )

        runnable = final_prompt | self.llm

        chunk_context = runnable.invoke({
            "WHOLE_DOCUMENT": whole_document,
            "CHUNK_CONTENT": paragraph_text
        }).content

        return chunk_context

    def _get_new_chunk_title(self, summary):
        """
        Generates a short, generalizable chunk title.
        """
        title_prompt = """You are the steward of document chunks. Generate a short title for the following chunk summary:

        Summary:
        {SUMMARY}

        Output only the title, nothing else."""

        prompt_template = PromptTemplate(
            input_variables=['SUMMARY'],
            template=title_prompt
        )

        runnable = prompt_template | self.llm

        new_chunk_title = runnable.invoke({
            "SUMMARY": summary
        }).content

        return new_chunk_title

    def _create_new_chunk(self, paragraph_text, page_no, filename, whole_document):
        """
        Creates a new chunk with Anthropic-style retrieval summary.
        """
        new_chunk_id = str(uuid.uuid4())[:self.id_truncate_limit]
        new_chunk_summary = self._get_new_chunk_summary(paragraph_text, whole_document)
        new_chunk_title = self._get_new_chunk_title(new_chunk_summary)

        self.chunks[new_chunk_id] = {
            'chunk_id': new_chunk_id,
            'paragraphs': [paragraph_text],
            'page_nos': [page_no],
            'filename': filename,
            'title': new_chunk_title,
            'summary': new_chunk_summary 
        }

    def get_chunks(self):
        """Returns the chunk dictionary."""
        return self.chunks
