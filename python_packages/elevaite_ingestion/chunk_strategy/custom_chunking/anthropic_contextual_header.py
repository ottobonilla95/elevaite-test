from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

# Contectual-retrieval Anthropic-style prompt
context_prompt = PromptTemplate(
    input_variables=["WHOLE_DOCUMENT", "CHUNK_CONTENT"],
    template="""<document>
{WHOLE_DOCUMENT}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{CHUNK_CONTENT}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""
)

human_prompt = HumanMessagePromptTemplate(prompt=context_prompt)
anthropic_prompt_template = ChatPromptTemplate.from_messages([human_prompt])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

def generate_contextual_header(chunk: Dict, full_paragraphs: List[Dict]) -> str:
    chunk_pages = set(chunk["page_range"])
    buffer_pages = {p for pg in chunk_pages for p in (pg - 1, pg, pg + 1)}
    
    surrounding_paragraphs = [
        p["paragraph_text"] for p in full_paragraphs
        if p["page_no"] in buffer_pages
    ]
    
    whole_context = " ".join(surrounding_paragraphs)
    chunk_text = chunk["chunk_text"]

    prompt_input = anthropic_prompt_template.format_messages(
        WHOLE_DOCUMENT=whole_context,
        CHUNK_CONTENT=chunk_text
    )

    response = llm(prompt_input)
    return response.content.strip()



import os
from typing import List, Dict
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

# Anthropic-style context prompt
context_prompt = PromptTemplate(
    input_variables=["WHOLE_DOCUMENT", "CHUNK_CONTENT"],
    template="""<document>
{WHOLE_DOCUMENT}
</document>
Here is the chunk we want to situate within the whole document
<chunk>
{CHUNK_CONTENT}
</chunk>
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else."""
)

human_prompt = HumanMessagePromptTemplate(prompt=context_prompt)
anthropic_prompt_template = ChatPromptTemplate.from_messages([human_prompt])

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)



async def generate_contextual_header_async(chunk: Dict, full_paragraphs: List[Dict]) -> str:
    chunk_pages = set(chunk["page_range"])
    buffer_pages = {p for pg in chunk_pages for p in (pg - 1, pg, pg + 1)}

    surrounding_paragraphs = [
        p["paragraph_text"] for p in full_paragraphs
        if p["page_no"] in buffer_pages
    ]

    whole_context = " ".join(surrounding_paragraphs)
    chunk_text = chunk["chunk_text"]

    prompt_input = anthropic_prompt_template.format_messages(
        WHOLE_DOCUMENT=whole_context,
        CHUNK_CONTENT=chunk_text
    )

    # try:
    #     response = await llm.ainvoke(prompt_input)
    #     return response.content.strip()
    # except Exception as e:
    #     return f"Header Generation Failed: {e}"

    try:
        response = await asyncio.wait_for(llm.ainvoke(prompt_input), timeout=30)
        return response.content.strip()
    except asyncio.TimeoutError:
        return "Header Generation Failed: Timeout"
    except Exception as e:
        return f"Header Generation Failed: {e}"


