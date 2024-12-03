from dsrag.knowledge_base import KnowledgeBase

class dsRAGKnowledgeBaseHandler:
    def __init__(self, kb_id: str, storage_directory: str):
        """
        Initialize the KnowledgeBaseHandler to load an existing knowledge base.
        
        Args:
            kb_id (str): Unique identifier for the knowledge base.
            storage_directory (str): Directory where the knowledge base is stored.
        
        Raises:
            ValueError: If the storage directory is not provided.
        """
        if not storage_directory:
            raise ValueError("A valid storage directory must be provided.")
        
        # Load the existing knowledge base from the provided storage directory
        self.kb = KnowledgeBase(kb_id=kb_id, storage_directory=storage_directory, exists_ok=True)
        print(f"Knowledge base '{kb_id}' loaded from {storage_directory}")

    def retrieve_information(self, query: str) -> str:
        """
        Retrieve relevant information from the knowledge base for a given query.
        
        Args:
            query (str): The user's query to search in the knowledge base.
        
        Returns:
            str: The retrieved information or a message if no relevant information is found.
        """
        search_queries = [query]
        results = self.kb.query(search_queries)

        if not results:
            return f"No relevant information found in the knowledge base for the query: {query}"

        retrieved_info = "\n".join([segment["text"] for segment in results])
        return retrieved_info