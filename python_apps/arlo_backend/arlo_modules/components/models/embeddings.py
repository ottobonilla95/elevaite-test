from sentence_transformers import SentenceTransformer

class TextEmbedder:
    def __init__(self, model_name="all-mpnet-base-v2"):
        self.model = SentenceTransformer(model_name)

    def create_embeddings(self, texts):
        embeddings = self.model.encode(texts)
        return embeddings, self.model

    def get_model(self):
        return self.model