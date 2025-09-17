import re
import os
from typing import List, Dict
import json
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv()
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def parse_markdown_structure(markdown_text: str) -> List[Dict]:
    elements = []
    lines = markdown_text.split("\n")

    buffer = []
    element_type = None

    for line in lines:
        stripped = line.strip()

        # Detect Headers (H1 to H6)
        if re.match(r"^#{1,6} ", stripped):
            if buffer:
                elements.append({"type": element_type, "content": "\n".join(buffer)})
                buffer = []
            element_type = "heading"

        # Detect Tables
        elif "|" in stripped and "---" in stripped:
            if buffer:
                elements.append({"type": element_type, "content": "\n".join(buffer)})
                buffer = []
            element_type = "table"

        # Detect Lists (Ordered & Unordered)
        elif re.match(r"^(\*|-|\d+\.) ", stripped):
            if element_type != "list":
                if buffer:
                    elements.append({"type": element_type, "content": "\n".join(buffer)})
                    buffer = []
                element_type = "list"

        # Detect Code Blocks
        elif stripped.startswith("```"):
            if element_type != "code":
                if buffer:
                    elements.append({"type": element_type, "content": "\n".join(buffer)})
                    buffer = []
                element_type = "code"

        # Normal Text (Paragraphs)
        elif stripped:
            if element_type not in ["paragraph", "list", "code"]:
                if buffer:
                    elements.append({"type": element_type, "content": "\n".join(buffer)})
                    buffer = []
                element_type = "paragraph"

        # Append to buffer
        buffer.append(line)

    if buffer:
        elements.append({"type": element_type, "content": "\n".join(buffer)})

    return elements


def chunk_text_from_markdown(markdown_text: str) -> List[Dict]:
    """
    Parses Markdown structure and applies LLM-based chunking.
    """
    elements = parse_markdown_structure(markdown_text)
    print(f"🔍 Parsed {len(elements)} structured elements from Markdown.")
    return elements


async def chunk_text(elements: List[Dict]) -> List[str]:
    system_prompt = """
    You are an AI that refines document chunking for efficient retrieval.
    - Merge small sections to maintain context.
    - Avoid breaking tables, lists, and code blocks.
    - Ensure logical sections remain together.
    - Return output **only** as a valid JSON list of strings, with no additional text.
    """

    max_tokens_per_request = 2000
    batched_chunks = []

    for i in range(0, len(elements), 5):
        batch = elements[i : i + 5]

        if not all(isinstance(e, dict) for e in batch):
            print(f"⚠️ Warning: Batch {i // 5 + 1} contains non-dict elements! Skipping...")
            continue

        user_prompt = json.dumps(batch, indent=2)

        try:
            response = await openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Optimize the following chunks:\n\n{user_prompt}"},
                ],
            )

            raw_response = response.choices[0].message.content
            if raw_response is None:
                raise Exception("No response from LLM")
            print(f"🔍 Raw LLM Response (Batch {i // 5 + 1}): {raw_response[:500]}")

            refined_chunks = json.loads(raw_response)
            batched_chunks.extend(refined_chunks)

        except json.JSONDecodeError:
            print(f"⚠️ Error: Failed to parse LLM response for batch {i // 5 + 1}")
            if all(isinstance(e, dict) and "content" in e for e in batch):
                batched_chunks.extend([e["content"] for e in batch])
            else:
                print(f"❌ Skipping fallback for batch {i // 5 + 1}, invalid format detected.")

    return batched_chunks


if __name__ == "__main__":
    markdown_file_path = (
        "/Users/dheeraj/Desktop/eleviate_ingestion copy/output_data/Ethics of Autonomous Vehicles - Spring 2023_markitdown.md"
    )
    with open(markdown_file_path, "r", encoding="utf-8") as file:
        markdown_content = file.read()
    chunks = chunk_text_from_markdown(markdown_content)
    print(" ✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅")
    print(chunks)
    print(" ✅ ✅ ✅ ✅ ✅ ✅ ✅ ✅")
    print(type(chunks))
