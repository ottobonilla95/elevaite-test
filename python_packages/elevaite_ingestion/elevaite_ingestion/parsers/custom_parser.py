# import sys
# import os
# import fitz
# import nltk
# from nltk.tokenize import sent_tokenize
# from typing import List
# from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
# from langchain_core.pydantic_v1 import BaseModel, Field
# from langchain_openai import ChatOpenAI

# nltk.download('punkt')
# from dotenv import load_dotenv
# load_dotenv()
# # ==============================
# # LLM Model for Proposition Generation
# # ==============================

# class GeneratePropositions(BaseModel):
#     """List of all the propositions in a given document"""
#     propositions: List[str] = Field(description="List of factual, self-contained, and concise propositions")

# llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
# structured_llm = llm.with_structured_output(GeneratePropositions)

# proposition_examples = [
#     {"document": "In 1969, Neil Armstrong became the first person to walk on the Moon during the Apollo 11 mission.",
#      "propositions":
#         ["Neil Armstrong was an astronaut.",
#          "Neil Armstrong walked on the Moon in 1969.",
#          "Neil Armstrong was the first person to walk on the Moon.",
#          "Neil Armstrong walked on the Moon during the Apollo 11 mission.",
#          "The Apollo 11 mission occurred in 1969."]},
# ]

# # Create a prompt for few-shot learning
# example_proposition_prompt = ChatPromptTemplate.from_messages([
#     ("human", "{document}"),
#     ("ai", "{propositions}"),
# ])

# few_shot_prompt = FewShotChatMessagePromptTemplate(
#     example_prompt=example_proposition_prompt,
#     examples=proposition_examples,
# )

# # System-level instructions for proposition generation
# system_prompt = """Please break down the following text into simple, self-contained propositions. Ensure that each proposition meets the following criteria:

# 1. **Express a Single Fact**: Each proposition should state one specific fact or claim.
# 2. **Be Understandable Without Context**: The proposition should be self-contained.
# 3. **Use Full Names, Not Pronouns**: Avoid ambiguous references.
# 4. **Include Relevant Dates/Qualifiers**: Ensure necessary details are included.
# 5. **Contain One Subject-Predicate Relationship**: Each should be a clear, standalone statement."""

# # Final LLM Prompt
# prompt = ChatPromptTemplate.from_messages([
#     ("system", system_prompt),
#     few_shot_prompt,
#     ("human", "{document}"),
# ])

# # Creating the proposition generator
# proposition_generator = prompt | structured_llm

# # ==============================
# # PDF Parsing & Sentence Extraction
# # ==============================

# class SentenceDocument:
#     """Represents a single sentence in a PDF along with metadata."""
#     def __init__(self, sentence_text, page_no, sentence_no, propositions=None):
#         self.sentence_text = sentence_text.strip()
#         self.page_no = page_no
#         self.sentence_no = sentence_no
#         self.propositions = propositions if propositions else []

#     def to_dict(self):
#         """Convert to dictionary format for JSON serialization."""
#         return {
#             "sentence_text": self.sentence_text,
#             "page_no": self.page_no,
#             "sentence_no": self.sentence_no,
#             "propositions": self.propositions
#         }

# class PdfParser:
#     """Parses a PDF file and extracts sentences with metadata."""
#     def __init__(self):
#         pass

#     def parse(self, file_path):
#         """
#         Parses a PDF file and extracts sentences with metadata.

#         Args:
#             file_path (str): Path to the PDF file.

#         Returns:
#             dict: Extracted content with sentence-level metadata.
#         """
#         try:
#             doc = fitz.open(file_path)
#             extracted_sentences = []

#             for page_num in range(len(doc)):
#                 page = doc[page_num]
#                 text = page.get_text("text").strip()

#                 if text:
#                     sentences = sent_tokenize(text)
#                     for sentence_no, sentence_text in enumerate(sentences, start=1):
#                         if sentence_text.strip():
#                             extracted_sentences.append(SentenceDocument(sentence_text, page_num + 1, sentence_no))

#             if not extracted_sentences:
#                 raise ValueError(f"No extractable content found in {file_path}")

#             return {
#                 "sentences": [sentence.to_dict() for sentence in extracted_sentences],
#                 "file_path": file_path
#             }

#         except Exception as e:
#             raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")

# # ==============================
# # Generating Propositions for Each Sentence
# # ==============================

# def generate_propositions_for_sentences(sentences):
#     """
#     Processes extracted sentences to generate factual propositions.

#     Args:
#         sentences (list): List of SentenceDocument objects.

#     Returns:
#         list: List of SentenceDocument objects with populated propositions.
#     """
#     for sentence_obj in sentences:
#         response = proposition_generator.invoke({"document": sentence_obj.sentence_text})
#         sentence_obj.propositions = response.propositions  # Store generated propositions
#     return sentences

# # ==============================
# # Chunk Formation Using Propositions
# # ==============================

# def create_chunks_with_propositions(sentences, max_tokens=512):
#     """
#     Forms chunks using both sentences and their extracted propositions.

#     Args:
#         sentences (list): List of SentenceDocument objects with propositions.
#         max_tokens (int): Maximum chunk size in tokens.

#     Returns:
#         list: List of formed chunks.
#     """
#     chunks = []
#     current_chunk = []

#     for sentence_obj in sentences:
#         sentence_with_props = sentence_obj.sentence_text + " " + " ".join(sentence_obj.propositions)

#         # Check if adding this sentence exceeds the chunk size
#         if len(" ".join(current_chunk)) + len(sentence_with_props) > max_tokens:
#             chunks.append(" ".join(current_chunk))
#             current_chunk = []

#         current_chunk.append(sentence_with_props)

#     # Add the last chunk
#     if current_chunk:
#         chunks.append(" ".join(current_chunk))

#     return chunks

# # ==============================
# # Running the Full Pipeline
# # ==============================

# if __name__ == "__main__":
#     file_path = "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/INPUT/kb_arlo_check.pdf"

#     # Step 1: Parse PDF and extract sentences
#     parser = PdfParser()
#     parsed_data = parser.parse(file_path)

#     # Convert extracted sentence dicts to SentenceDocument objects
#     sentence_objects = [SentenceDocument(**sent) for sent in parsed_data["sentences"]]
#     # ✅ Print the first 10 sentences with details
#     print("\n### First 10 Extracted Sentences ###\n")
#     for idx, sentence in enumerate(sentence_objects[:10]):
#         print(f"Sentence {idx+1}:")
#         print(f"  Text      : {sentence.sentence_text}")
#         print(f"  Page No   : {sentence.page_no}")
#         print(f"  Sentence No: {sentence.sentence_no}")
#         print(f"  Propositions: {sentence.propositions}")
#         print("-" * 60)

#     # # Step 2: Generate Propositions for Each Sentence
#     # enriched_sentences = generate_propositions_for_sentences(sentence_objects)

#     # # Step 3: Create Chunks Using Both Sentences & Propositions
#     # final_chunks = create_chunks_with_propositions(enriched_sentences)

#     # # Output Chunks
#     # for idx, chunk in enumerate(final_chunks[:10]):
#     #     print(f"\nChunk {idx + 1}:\n{chunk}\n")

import fitz
import nltk
from nltk.tokenize import sent_tokenize
from typing import List
from langchain_core.prompts import ChatPromptTemplate, FewShotChatMessagePromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

from dotenv import load_dotenv

nltk.download("punkt")
load_dotenv()

# ==============================
# LLM Model for Proposition Generation
# ==============================


class GeneratePropositions(BaseModel):
    """List of all the propositions in a given document"""

    propositions: List[str] = Field(
        description="List of factual, self-contained, and concise propositions"
    )


# ✅ Use OpenAI model (e.g., GPT-4o)
llm = ChatOpenAI(model="gpt-4o", temperature=0)
structured_llm = llm.with_structured_output(GeneratePropositions)

proposition_examples = [
    {
        "document": "In 1969, Neil Armstrong became the first person to walk on the Moon during the Apollo 11 mission.",
        "propositions": [
            "Neil Armstrong was an astronaut.",
            "Neil Armstrong walked on the Moon in 1969.",
            "Neil Armstrong was the first person to walk on the Moon.",
            "Neil Armstrong walked on the Moon during the Apollo 11 mission.",
            "The Apollo 11 mission occurred in 1969.",
        ],
    },
]

# Create a prompt for few-shot learning
example_proposition_prompt = ChatPromptTemplate.from_messages(
    [
        ("human", "{document}"),
        ("ai", "{propositions}"),
    ]
)

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_proposition_prompt,
    examples=proposition_examples,
)

# System-level instructions for proposition generation
system_prompt = """Please break down the following text into simple, self-contained propositions. Ensure that each proposition meets the following criteria:

1. **Express a Single Fact**: Each proposition should state one specific fact or claim.
2. **Be Understandable Without Context**: The proposition should be self-contained.
3. **Use Full Names, Not Pronouns**: Avoid ambiguous references.
4. **Include Relevant Dates/Qualifiers**: Ensure necessary details are included.
5. **Contain One Subject-Predicate Relationship**: Each should be a clear, standalone statement."""

# Final LLM Prompt
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        few_shot_prompt,
        ("human", "{document}"),
    ]
)

# Creating the proposition generator
proposition_generator = prompt | structured_llm

# ==============================
# PDF Parsing & Sentence Extraction
# ==============================


class SentenceDocument:
    """Represents a single sentence in a PDF along with metadata."""

    def __init__(self, sentence_text, page_no, sentence_no, propositions=None):
        self.sentence_text = sentence_text.strip()
        self.page_no = page_no
        self.sentence_no = sentence_no
        self.propositions = propositions if propositions else []

    def to_dict(self):
        """Convert to dictionary format for JSON serialization."""
        return {
            "sentence_text": self.sentence_text,
            "page_no": self.page_no,
            "sentence_no": self.sentence_no,
            "propositions": self.propositions,
        }


class PdfParser:
    """Parses a PDF file and extracts sentences with metadata."""

    def __init__(self):
        pass

    def parse(self, file_path):
        """
        Parses a PDF file and extracts sentences with metadata.

        Args:
            file_path (str): Path to the PDF file.

        Returns:
            list: List of SentenceDocument objects.
        """
        try:
            doc = fitz.open(file_path)
            extracted_sentences = []

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text").strip()

                if text:
                    sentences = sent_tokenize(text)
                    for sentence_no, sentence_text in enumerate(sentences, start=1):
                        if sentence_text.strip():
                            extracted_sentences.append(
                                SentenceDocument(
                                    sentence_text, page_num + 1, sentence_no
                                )
                            )

            if not extracted_sentences:
                raise ValueError(f"No extractable content found in {file_path}")

            return extracted_sentences  # ✅ Returns list of SentenceDocument objects

        except Exception as e:
            raise Exception(f"Failed to parse PDF file: {file_path}. Error: {e}")


# ==============================
# Enrich Sentences with Context Before Proposition Generation
# ==============================


def enrich_sentence_with_context(sentences):
    """
    Enrich each sentence by resolving references using the previous sentence when needed.

    Args:
        sentences (list): List of SentenceDocument objects.

    Returns:
        list: List of enriched SentenceDocument objects.
    """
    enriched_sentences = []
    prev_sentence = ""

    for sentence_obj in sentences:
        sentence_text = sentence_obj.sentence_text.strip()

        keywords_indicating_reference = ["this article", "this program", "it refers to"]
        needs_context = any(
            kw in sentence_text.lower() for kw in keywords_indicating_reference
        )

        if needs_context and prev_sentence:
            input_text = f"""
            Task: Enrich the current sentence by resolving references while keeping all factual details.
            
            - If the sentence contains 'this article', 'this program', or similar ambiguous references, replace it with the actual subject from the previous sentence.
            - DO NOT remove or modify lists, numbers, or structured data.
            - Ensure that the enriched sentence remains clear, structured, and self-contained.

            **Example Input:**
            Previous Sentence: "What do I need to know about the Arlo Theft Replacement program?"
            Current Sentence: "This article applies to: AVD4001, AVD3001, AVD2001, AVD1001."

            **Expected Output:**
            "The article about the Arlo Theft Replacement program applies to: AVD4001, AVD3001, AVD2001, AVD1001."

            **Example Input:**
            Previous Sentence: "Arlo offers a theft replacement service for stolen devices."
            Current Sentence: "This program requires a police report."

            **Expected Output:**
            "The Arlo theft replacement service requires a police report."
            
            Now, process the following:
            Previous Sentence: "{prev_sentence}"
            Current Sentence: "{sentence_text}"
            """

            response = proposition_generator.invoke({"document": input_text})
            resolved_sentence = response.propositions[0]
        else:
            resolved_sentence = sentence_text

        if ":" in resolved_sentence and "," not in resolved_sentence and prev_sentence:
            resolved_sentence += " " + prev_sentence

        enriched_sentence_obj = SentenceDocument(
            sentence_text=resolved_sentence,
            page_no=sentence_obj.page_no,
            sentence_no=sentence_obj.sentence_no,
            propositions=[],
        )

        enriched_sentences.append(enriched_sentence_obj)

        if len(sentence_text.split()) > 3:
            prev_sentence = sentence_text

    return enriched_sentences


# ==============================
# Running the Full Pipeline
# ==============================

if __name__ == "__main__":
    file_path = (
        "/Users/dheeraj/Desktop/elevaite/elevaite_ingestion/INPUT/kb_arlo_check.pdf"
    )

    parser = PdfParser()
    sentence_objects = parser.parse(file_path)

    print("\n########## 1️⃣ Extracted Sentences ##########")
    for idx, sentence in enumerate(sentence_objects[:15]):
        print(f"Sentence {idx + 1}: {sentence.sentence_text} (Page {sentence.page_no})")
    print("###########################################\n")

    # # ✅ Enrich sentences by resolving context
    # enriched_sentences = enrich_sentence_with_context(sentence_objects)

    # print("\n########## 2️⃣ Enriched Sentences (Resolved Context) ##########")
    # for idx, sentence in enumerate(enriched_sentences[:5]):  # Print first 5 for clarity
    #     print(f"Sentence {idx+1}: {sentence.sentence_text} (Page {sentence.page_no})")
    # print("###########################################\n")

    # # ✅ Generate Propositions for Enriched Sentences
    # enriched_sentences = generate_propositions_for_sentences(enriched_sentences)

    # print("\n########## 3️⃣ Enriched Sentences with Propositions ##########")
    # for idx, sentence in enumerate(enriched_sentences[:5]):  # Print first 5 for clarity
    #     print(f"Sentence {idx+1}: {sentence.sentence_text} (Page {sentence.page_no})")
    #     print(f"  Propositions: {sentence.propositions}")
    # print("###########################################\n")

    # # ✅ Create Chunks Using Sentences & Propositions
    # final_chunks = create_chunks_with_propositions(enriched_sentences)

    # print("\n########## 4️⃣ Final Chunked Output ##########")
    # for idx, chunk in enumerate(final_chunks[:3]):  # Print first 3 chunks for clarity
    #     print(f"Chunk {idx+1} (Pages: {chunk['pages']}):\n{chunk['text']}\n")
    # print("###########################################\n")

    # # ✅ Print first 10 enriched sentences
    # print("\n########## 5️⃣ First 10 Enriched Sentences ##########")
    # for idx, sentence in enumerate(enriched_sentences[:10]):
    #     print(f"Sentence {idx+1}: {sentence.sentence_text} (Page {sentence.page_no})")
    # print("###########################################\n")


# # ==============================
# # Generating Propositions for Each Sentence
# # ==============================

# def generate_propositions_for_sentences(sentences):
#     """
#     Generates factual propositions while preserving metadata.

#     Args:
#         sentences (list): List of enriched SentenceDocument objects.

#     Returns:
#         list: List of SentenceDocument objects with populated propositions.
#     """
#     for sentence_obj in sentences:
#         response = proposition_generator.invoke({"document": sentence_obj.sentence_text})

#         # Ensure list-style facts are maintained in separate propositions
#         propositions = []
#         for prop in response.propositions:
#             if "," in prop:  # If the proposition contains a list, keep it as a single statement
#                 propositions.append(prop)
#             else:
#                 propositions.append(prop)

#         sentence_obj.propositions = list(set(propositions))  # Remove duplicates
#     return sentences


# # ==============================
# # Chunk Formation Using Propositions
# # ==============================

# def create_chunks_with_propositions(sentences, max_tokens=512):
#     """
#     Forms chunks using both sentences and their extracted propositions while keeping metadata.

#     Args:
#         sentences (list): List of SentenceDocument objects with propositions.
#         max_tokens (int): Maximum chunk size in tokens.

#     Returns:
#         list: List of formed chunks with metadata.
#     """
#     chunks = []
#     current_chunk = []
#     current_metadata = []

#     for sentence_obj in sentences:
#         sentence_with_props = sentence_obj.sentence_text + " " + " ".join(sentence_obj.propositions)

#         if sentence_with_props not in current_chunk:
#             if len(" ".join(current_chunk)) + len(sentence_with_props) > max_tokens:
#                 chunks.append({
#                     "text": " ".join(current_chunk),
#                     "pages": list(set(current_metadata))
#                 })
#                 current_chunk = []
#                 current_metadata = []

#             current_chunk.append(sentence_with_props)
#             current_metadata.append(sentence_obj.page_no)

#     if current_chunk:
#         chunks.append({
#             "text": " ".join(current_chunk),
#             "pages": list(set(current_metadata))
#         })

#     return chunks
