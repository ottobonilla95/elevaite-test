from typing import List, Dict
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    PromptTemplate,
)
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
import asyncio

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
Please give a short succinct context to situate this chunk within the overall document for the purposes of improving search retrieval of the chunk. Answer only with the succinct context and nothing else.""",
)

human_prompt = HumanMessagePromptTemplate(prompt=context_prompt)
anthropic_prompt_template = ChatPromptTemplate.from_messages([human_prompt])
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


def generate_contextual_header(
    chunk: Dict, full_paragraphs: List[Dict], total_pages: int
) -> str:
    try:
        # Validate document structure first
        if not full_paragraphs:
            return "Header Generation Failed: Empty document"
        if any(p["page_no"] < 1 for p in full_paragraphs):
            return "Header Generation Failed: Invalid page numbers"

        chunk_pages = set(chunk["page_range"])
        buffer_pages = set()

        # Clamp pages to valid range using total_pages
        for pg in chunk_pages:
            buffer_pages.update({max(1, pg - 1), pg, min(total_pages, pg + 1)})

        surrounding_paragraphs = [
            p["paragraph_text"] for p in full_paragraphs if p["page_no"] in buffer_pages
        ]

        first_page_paragraphs = [
            p["paragraph_text"] for p in full_paragraphs if p["page_no"] == 1
        ]

        whole_context = " ".join(first_page_paragraphs + surrounding_paragraphs)
        chunk_text = chunk["chunk_text"]

        prompt_input = anthropic_prompt_template.format_messages(
            WHOLE_DOCUMENT=whole_context, CHUNK_CONTENT=chunk_text
        )

        response = llm(prompt_input)
        return response.content.strip()
    except Exception as e:
        return f"Header Generation Failed: {e}"


async def generate_contextual_header_async(
    chunk: Dict, full_paragraphs: List[Dict], total_pages: int
) -> str:
    try:
        if not full_paragraphs:
            return "Header Generation Failed: Empty document"
        if any(p["page_no"] < 1 for p in full_paragraphs):
            return "Header Generation Failed: Invalid page numbers"

        chunk_pages = set(chunk["page_range"])
        buffer_pages = set()

        for pg in chunk_pages:
            buffer_pages.update({max(1, pg - 1), pg, min(total_pages, pg + 1)})

        surrounding_paragraphs = [
            p["paragraph_text"] for p in full_paragraphs if p["page_no"] in buffer_pages
        ]

        first_page_paragraphs = [
            p["paragraph_text"] for p in full_paragraphs if p["page_no"] == 1
        ]

        whole_context = " ".join(first_page_paragraphs + surrounding_paragraphs)
        chunk_text = chunk["chunk_text"]

        prompt_input = anthropic_prompt_template.format_messages(
            WHOLE_DOCUMENT=whole_context, CHUNK_CONTENT=chunk_text
        )

        response = await asyncio.wait_for(llm.ainvoke(prompt_input), timeout=30)
        return response.content.strip()
    except asyncio.TimeoutError:
        return "Header Generation Failed: Timeout"
    except Exception as e:
        return f"Header Generation Failed: {e}"
