import os
from dsrag.knowledge_base import KnowledgeBase
from dsrag.document_parsing import extract_text_from_pdf
from dotenv import load_dotenv
import trafilatura

# Load environment variables
# env_file_path = ".env"
env_file_path = os.path.abspath(os.path.join(__file__, '../../../../.env'))
load_dotenv(dotenv_path=env_file_path)


links = ["https://www.arlo.com/en-us/security-system/arlo-security-system.html",
"https://www.arlo.com/en-us/cameras/essential/arlo-essential-xl-v2.html",
"https://www.arlo.com/en-us/cameras/go/arlo-go-2-cameras.html",
"https://www.arlo.com/en-us/cameras/essential/arlo-essential-v2.html",
"https://www.arlo.com/en-us/cameras/essential/arlo-essential-indoor-v2.html",
"https://www.arlo.com/en-us/doorbell/AVD4001-100NAS.html",
"https://www.arlo.com/en-us/doorbell/AVD3001-100NAS.html",
"https://www.arlo.com/en-us/cameras/ultra/arlo-ultra-2.html",
"https://www.arlo.com/en-us/cameras/pro/arlo-pro-5.html",
"https://www.arlo.com/en-us/light/arlo-wired-floodlight.html",
"https://www.arlo.com/en-us/light/arlo-pro-3-floodlight-camera.html",
]

# Function to create a kb from a document file -------> (supports both text and PDF)
def create_kb(kb_id: str, file_path: str, storage_directory: str):
    """
    Create a knowledge base (KB) from a given file and save it in the specified storage directory.
    
    Args:
        kb_id (str): Unique identifier for the knowledge base.
        file_path (str): Path to the file from which to create the knowledge base.
        storage_directory (str): Directory where the knowledge base will be stored.
    
    Returns:
        KnowledgeBase: The created knowledge base object.
    """
    doc_id = os.path.basename(file_path).split(".")[0]

    # Determine file type and extract text accordingly
    if file_path.endswith(".pdf"):
        document_text = extract_text_from_pdf(file_path)
    else:
        with open(file_path, "r") as f:
            document_text = f.read()

    # Ensure the text is a string (it might return a tuple by mistake in some cases)
    if isinstance(document_text, tuple):
        document_text = document_text[0]

    # print(f"Document text preview:\n{document_text[:1000]}")

    # # Create a new knowledge base or load an existing one
    kb = KnowledgeBase(kb_id=kb_id, exists_ok=True, storage_directory=storage_directory)
    
    # # Add the document to the knowledge base
    kb.add_document(doc_id=doc_id, text=document_text)
    # print(f"Document '{doc_id}' added to the knowledge base '{kb_id}'.")
    return kb

#################################retriever with preicsion ##########################
RSE_PARAMS_PRESET = {
    "balanced": {
        'max_length': 15,
        'overall_max_length': 30,
        'minimum_value': 0.5,
        'irrelevant_chunk_penalty': 0.18,
        'overall_max_length_extension': 5,
        'decay_rate': 30,
        'top_k_for_document_selection': 10,
        'chunk_length_adjustment': True,
    },
    "precision": {
        'max_length': 15,
        'overall_max_length': 30,
        'minimum_value': 1.1,
        'irrelevant_chunk_penalty': 0.17,
        'overall_max_length_extension': 5,
        'decay_rate': 30,
        'top_k_for_document_selection': 10,
        'chunk_length_adjustment': True,
    },
    "find_all": {
        'max_length': 40,
        'overall_max_length': 200,
        'minimum_value': 1.2,
        'irrelevant_chunk_penalty': 0.18,
        'overall_max_length_extension': 0,
        'decay_rate': 200,
        'top_k_for_document_selection': 200,
        'chunk_length_adjustment': True,
    },
}

class KnowledgeBaseHandler:
    def __init__(self, kb):
        self.kb = kb

    def retrieve_information(self, query: str, rse_param_key: str = "precision") -> tuple:
        rse_params = RSE_PARAMS_PRESET.get(rse_param_key, RSE_PARAMS_PRESET["precision"])
        search_queries = [query]
        results = self.kb.query(search_queries, rse_params=rse_params, latency_profiling=False)
        
        if not results:
            return f"No relevant information found in the knowledge base for the query: {query}", 0.0, []

        # Filter results based on relevancy score
        # filtered_results = [
        #     segment for segment in results if segment["score"] > 0.9
        # ]
        # print("##############################################")
        # print("filtered_results::::::::", filtered_results)
        # print("##############################################")


        # if not filtered_results:
        #     return "No relevant information with a score greater than 0.8 found.", 0.0, []

        if len(results) > 3:
            results = results[:3]

        chunks = []

        # Iterate through all filtered results and retrieve chunks for each one
        for result in results:
            # print("#############################")
            # print(result)
            # print("#############################")
            doc_id = result['doc_id']
            chunk_start = result['chunk_start']
            chunk_end = result['chunk_end']

            # Collect chunks within the specified range
            for i in range(chunk_start, chunk_end):
                chunk = {
                    "section_title": self.kb.chunk_db.get_section_title(doc_id, i),
                    "chunk_text": self.kb.chunk_db.get_chunk_text(doc_id, i),
                }
                chunks.append(chunk)

        # Combine all chunk texts into the output
        chunk_output = "\n".join([f"{chunk['section_title']}:::::<=============Section _title============|{chunk['chunk_text']}" for chunk in chunks])
        # Compile retrieved information and relevancy scores
        retrieved_info = "\n\n-------\n\n".join([segment["text"] for segment in results])
        retrieved_info_relevancy_score = "\n".join([str(segment["score"]) for segment in results])

        return retrieved_info, retrieved_info_relevancy_score, chunks

############################################################################

########################################################### retriever without precision ##############
# class KnowledgeBaseHandler:
#     def __init__(self, kb):
#         self.kb = kb

#     def retrieve_information(self, query: str) -> tuple:
#         search_queries = [query]
#         results = self.kb.query(search_queries)

#         if not results:
#             return f"No relevant information found in the knowledge base for the query: {query}", 0.0, []

#         # Filter results based on relevancy score
#         filtered_results = [
#             segment for segment in results if segment["score"] > 1.2
#         ]
#         # print("##############################################")
#         # print("filtered_results::::::::", filtered_results)
#         # print("##############################################")

#         if not filtered_results:
#             return "No relevant information with a score greater than 0.8 found.", 0.0, []

#         # Retrieve chunks based on filtered results
#         doc_id = filtered_results[0]['doc_id']
#         chunk_start = filtered_results[0]['chunk_start']
#         chunk_end = filtered_results[0]['chunk_end']

#         chunks = []
#         for i in range(chunk_start, chunk_end + 1):
#             chunk = {
#                 "section_title": self.kb.chunk_db.get_section_title(doc_id, i),
#                 "chunk_text": self.kb.chunk_db.get_chunk_text(doc_id, i),
#             }
#             chunks.append(chunk)

#         # Format the chunks for output
#         chunk_output = "\n".join([f"{chunk['section_title']}: {chunk['chunk_text']}" for chunk in chunks])

#         # Compile retrieved information and relevancy scores
#         retrieved_info = "\n".join([segment["text"] for segment in filtered_results])
#         retrieved_info_relevancy_score = "\n".join([str(segment["score"]) for segment in filtered_results])

#         return retrieved_info, retrieved_info_relevancy_score, chunks
###############################################################################################
# Class for handling the knowledge base operations
# class KnowledgeBaseHandler:
#     def __init__(self, kb):
#         """
#         Initialize the KnowledgeBaseHandler to load an existing knowledge base.
#
#         Args:
#             kb_id (str): Unique identifier for the knowledge base.
#             storage_directory (str): Directory where the knowledge base is stored.
#
#         Raises:
#             ValueError: If the storage directory is not provided.
#         """
#         # if not storage_directory:
#         #     raise ValueError("A valid storage directory must be provided.")
#
#         # Load the existing knowledge base from the provided storage directory
#         self.kb = KnowledgeBase(kb_id=kb_id, storage_directory=storage_directory, exists_ok=True)
#         print(f"Knowledge base '{kb_id}' loaded from {storage_directory}")
#
#     def retrieve_information(self, query: str) -> str:
#         """
#         Retrieve relevant information from the knowledge base for a given query.
#
#         Args:
#             query (str): The user's query to search in the knowledge base.
#
#         Returns:
#             str: The retrieved information or a message if no relevant information is found.
#         """
#         search_queries = [query]
#         results = self.kb.query(search_queries)
#
#         if not results:
#             return f"No relevant information found in the knowledge base for the query: {query}"
#
#         retrieved_info = "\n".join([segment["text"] for segment in results])
#         return retrieved_info


#Define followings to create kb and add documents
# file_path = "documents/kb_arlo.pdf"


# # Create the knowledge base and add the document
# kb = create_kb(kb_id, file_path, storage_directory)
# print("kb::::::::::::", type(kb))
# print("Created kb")

def add_url_content_to_existing_kb(kb_id: str, storage_directory: str, links):
    """
    Adds content from specified URLs to an existing knowledge base.
    
    Args:
        kb_id (str): Unique identifier for the knowledge base.
        storage_directory (str): Directory where the knowledge base is stored.
        links (list): List of URLs to fetch additional content from.
    """
    # Initialize the existing KnowledgeBase
    kb = KnowledgeBase(kb_id=kb_id, exists_ok=True, storage_directory=storage_directory)

    # Fetch content from each URL and combine into a single document text
    documents = []
    for url in links:
        downloaded = trafilatura.fetch_url(url)
        if downloaded:
            page_content = trafilatura.extract(downloaded)
            if page_content:
                documents.append(page_content)
    
    # Combine all URL contents into a single string
    url_content = "\n".join(documents)

    # Define a unique doc_id for this new document
    url_doc_id = f"{kb_id}_url_content"

    # Add the URL content as a new document to the KnowledgeBase
    kb.add_document(
        doc_id=url_doc_id,
        text=url_content,
    )
    # print(f"URL content added to KnowledgeBase with ID: {kb_id}")

# kb_id = "arlo_ds"
# storage_directory = "dsRAG_db"
# kb = KnowledgeBase(kb_id=kb_id, exists_ok=True, storage_directory=storage_directory)
#
# # # kb_add_url = add_url_content_to_existing_kb(kb_id, storage_directory, links)
# #
# #
# # # # Load the knowledge base and retrieve information
# kb_handler = KnowledgeBaseHandler(kb)
# # #
# # # # Check retrieved info based on query
# query = "Specs for Home security system"
# retrieved_info,_,_ = kb_handler.retrieve_information(query)
# # #
# # # # Display retrieved information
# print(f"Retrieved Information:\n{retrieved_info}")