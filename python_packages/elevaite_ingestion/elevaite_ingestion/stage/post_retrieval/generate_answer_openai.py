import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=api_key)


def generate_answer(query: str, segments: list) -> str:
    # for i, s in enumerate(segments):
    #     print(f"\n--- Segment {i+1} ---\n{s[:1000]}")

    # Segments is a flat list of combined header + chunk_text strings
    context_text = "\n".join(segments)
    print("############contet_text..")
    print(context_text)

    example = (
        "Example:\n"
        "Question: What happens during the End of Life (EOL) of a product?\n"
        "Answer:\n"
        "A. First consequence\n"
        "B. Second consequence\n"
        "C. Third consequence\n"
    )

    prompt = (
        "You are a helpful assistant. Carefully read and understand the **entire context**, even if parts of the answer appear across different chunks."
        " Do not stop at the first relevant part — ensure your answer is **complete and holistic**, covering all steps mentioned in the context."
        " Use only the information provided.\n\n"
        f"{example}"
        "\n\n--- CONTEXT (with headers) ---\n"
        f"{context_text}"
        "\n\n--- USER QUESTION ---\n"
        f"{query}"
        "\n\n--- INSTRUCTIONS ---\n"
        "If the answer includes a list of steps, instructions, or outcomes using A, B, C... formatting, return each item on a **new line**, starting with the correct letter."
        " Do not merge multiple items onto a single line. Preserve the structure and ordering exactly as it appears in the context."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You answer based only on the provided context."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"❌ Error generating answer: {str(e)}"
