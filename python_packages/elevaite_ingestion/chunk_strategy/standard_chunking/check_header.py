import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def generate_contextual_header(chunks):
    """
    Uses GPT-4o to generate a contextual header:
    - Summarizes the **core topic** of the chunk.
    - If related to `prev_chunk` or `next_chunk`, mentions it explicitly.
    """
    headers = []

    for i, chunk_text in enumerate(chunks):
        print(f"\n🔹 Sending chunk {i+1}/{len(chunks)} to GPT-4o...")

        prev_chunk = chunks[i - 1] if i > 0 else "None"
        next_chunk = chunks[i + 1] if i < len(chunks) - 1 else "None"

        prompt = f"""
        You are an AI assistant organizing structured documents for retrieval. 
        Generate a **one-line contextual header** summarizing this chunk:

        {chunk_text}

        If this chunk is **highly related** to the previous chunk:
        {prev_chunk}
        OR the next chunk:
        {next_chunk}, mention this in the summary.

        Response Format:
        **Core Summary**: <summary>
        **Related Chunks**: <mention previous or next if relevant>
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": prompt}],
                temperature=0.3,
                max_tokens=50,
            )

            header = response.choices[0].message.content.strip()
            print(f"✅ Header Generated: {header}\n")
        except Exception as e:
            print(f"⚠️ LLM request failed for chunk {i+1}: {e}")
            header = "⚠️ LLM Failed - Header Not Generated"
        
        headers.append(header)
        time.sleep(1)

    return headers

if __name__ == "__main__":
    sample_chunks = [
        "The Arlo camera system offers advanced security features including motion detection, cloud storage, and integration with smart home devices.",
        "To set up your Arlo camera, connect it to WiFi, sync with the mobile app, and position it for optimal coverage. Ensure firmware updates are applied.",
        "The Arlo subscription plans provide additional storage, AI-based motion detection, and priority customer support. Plans vary based on user needs.",
    ]

    print("🚀 Running LLM-based Contextual Header Generation Test...\n")
    contextual_headers = generate_contextual_header(sample_chunks)

    for i, header in enumerate(contextual_headers):
        print(f"🔹 Chunk {i+1} Header: {header}")
