from custom import DocumentLine
import openai
import json
import os
from dotenv import load_dotenv

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")


class LLMAgentChunker:
    def __init__(self, model_name="gpt-4o-mini", max_chunk_size=700):
        self.model_name = model_name
        self.max_chunk_size = max_chunk_size

    def is_semantically_related(self, prev_lines, next_lines):
        """
        Use OpenAI's LLM to determine if the next lines are semantically related to the previous lines.
        """
        prompt = f"""
        You are an intelligent agent tasked with grouping lines of text into semantically coherent chunks.
        Below are two sets of lines:

        Previous Lines:
        {" ".join(prev_lines)}

        Next Lines:
        {" ".join(next_lines)}

        Are the next lines semantically related to the previous lines? Answer with "Yes" or "No".
        """

        response = openai.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=10,
        )

        # Extract the LLM's response
        if response.choices[0].message.content is None:
            return False
        llm_response = response.choices[0].message.content.strip()
        return "Yes" in llm_response

    def create_chunks(self, document_lines):
        """
        Create chunks using the LLM-based agentic approach.
        """
        chunks = []
        current_chunk = ""
        current_metadata = []

        prev_lines = []

        for line in document_lines:
            # Check if adding this line exceeds the max chunk size
            if (
                len(current_chunk) + len(line.text) > self.max_chunk_size
                and current_chunk
            ):
                chunks.append(
                    {"text": current_chunk.strip(), "metadata": current_metadata}
                )
                current_chunk = ""
                current_metadata = []
                prev_lines = []

            # Check semantic relation if there are previous lines
            if prev_lines:
                next_lines = [line.text]
                if not self.is_semantically_related(prev_lines, next_lines):
                    # Start a new chunk
                    chunks.append(
                        {"text": current_chunk.strip(), "metadata": current_metadata}
                    )
                    current_chunk = ""
                    current_metadata = []
                    prev_lines = []

            # Add the current line to the chunk
            current_chunk += line.text + " "
            current_metadata.append(
                {
                    "page_no": line.page_no,
                    "line_start_no": line.line_start_no,
                    "line_end_no": line.line_end_no,
                    "source": line.source,
                    "cropped_table_path": line.cropped_table_path,
                    "cropped_image_path": line.cropped_image_path,
                }
            )

            # Update previous lines for semantic evaluation
            prev_lines = (
                [line.text] if not prev_lines else prev_lines[-2:] + [line.text]
            )

        # Add the last chunk if it exists
        if current_chunk:
            chunks.append({"text": current_chunk.strip(), "metadata": current_metadata})

        return chunks


if __name__ == "__main__":
    # Load parsed document lines from JSON
    with open("output/parsed_data.json", "r") as f:
        parsed_data = json.load(f)

    # Convert JSON back to DocumentLine objects
    document_lines = [
        DocumentLine(
            text=item["text"],
            page_no=item["page_no"],
            line_start_no=item["line_start_no"],
            line_end_no=item["line_end_no"],
            source=item["source"],
            cropped_table_path=item["cropped_table_path"],
            cropped_image_path=item["cropped_image_path"],
        )
        for item in parsed_data
    ]

    # Initialize the chunker
    chunker = LLMAgentChunker(model_name="gpt-4o-mini", max_chunk_size=700)

    # Create chunks
    chunks = chunker.create_chunks(document_lines)

    # Save chunks to JSON
    with open("output/chunks.json", "w") as f:
        json.dump(chunks, f, indent=4)

    # Print the first few chunks for verification
    for chunk in chunks[:10]:
        print(chunk)
