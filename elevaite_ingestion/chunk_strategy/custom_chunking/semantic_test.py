from langchain_openai import OpenAIEmbeddings
from semantic_chunk_v1 import semantic_chunking

sample_paragraphs = [
    {"paragraph_text": "Arlo devices are used for home security.", "paragraph_no": 1, "page_no": 1},
    {"paragraph_text": "You can manage Arlo subscriptions through the app.", "paragraph_no": 2, "page_no": 1},
    {"paragraph_text": "Arlo Pro models support two-way audio.", "paragraph_no": 3, "page_no": 1},
    {"paragraph_text": "Bluetooth allows device pairing over short distances.", "paragraph_no": 4, "page_no": 2},
    {"paragraph_text": "WiFi routers are used to connect multiple devices wirelessly.", "paragraph_no": 5, "page_no": 2},
]

embedding_model = OpenAIEmbeddings(model="text-embedding-3-small")

# Call the chunker
chunks = semantic_chunking(
    paragraphs=sample_paragraphs,
    embeddings=embedding_model,
    buffer_size=1,
    threshold_type="percentile",
    threshold_value=90,
    min_chunk_size=50
)

# Print results
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i + 1}")
    print("Content:", chunk["chunk_content"])
    print("Metadata:", chunk["metadata"])
