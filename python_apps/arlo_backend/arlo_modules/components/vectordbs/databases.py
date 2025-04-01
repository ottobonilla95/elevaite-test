import faiss

class FaissDB:
    @staticmethod
    def build_index(embeddings):
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        return index

    @staticmethod
    def search(query, index, texts, embedding_model, k=3):
        query_embedding = embedding_model.encode([query])
        distances, indices = index.search(query_embedding, k)
        return [(texts[idx], idx) for idx in indices[0]]

# class Chroma:
