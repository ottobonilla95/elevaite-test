from elevaite_ingestion.vectorstore.db import PineconeClient, ChromaClient, QdrantClientWrapper


class VectorDBFactory:
    @staticmethod
    def get_client(db_type: str, **kwargs):
        if db_type == "pinecone":
            return PineconeClient(
                api_key=kwargs["api_key"],
                cloud=kwargs["cloud"],
                region=kwargs["region"],
                index_name=kwargs["index_name"],
                dimension=kwargs["dimension"],
            )
        elif db_type == "chroma":
            return ChromaClient(db_path=kwargs["db_path"])
        elif db_type == "qdrant":
            return QdrantClientWrapper(host=kwargs["host"], port=int(kwargs["port"]))
        else:
            raise ValueError(f"Unsupported vector database type: {db_type}")
