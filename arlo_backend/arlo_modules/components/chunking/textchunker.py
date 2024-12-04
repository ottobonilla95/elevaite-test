from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from nltk import sent_tokenize

class TextChunker:
    """
    A class that provides various methods for chunking text into smaller segments
    using different strategies like semantic clustering, fixed size, sliding window,
    and natural breaks (sentences/paragraphs).
    """

    def __init__(self, semantic_model='paraphrase-MiniLM-L6-v2'):
        """
        Initialize the TextChunker with a specified semantic model.

        Parameters:
        semantic_model (str): Name of the sentence transformer model to use for semantic chunking.
        """
        self.semantic_model = SentenceTransformer(semantic_model)

    def semantic_chunk(self, text, n_clusters=5):
        """
        Splits text into semantic chunks by clustering similar sentences.

        Parameters:
        text (str): The input text to chunk.
        n_clusters (int): The number of semantic clusters/chunks to create.

        Returns:
        List[str]: A list of semantically chunked text.
        """
        # Split the text into sentences
        sentences = sent_tokenize(text)

        # Generate embeddings for each sentence
        sentence_embeddings = self.semantic_model.encode(sentences)

        # Perform KMeans clustering to group sentences into semantic chunks
        kmeans = KMeans(n_clusters=n_clusters, random_state=0)
        kmeans.fit(sentence_embeddings)

        # Assign each sentence to a cluster
        clustered_sentences = [[] for _ in range(n_clusters)]
        for idx, label in enumerate(kmeans.labels_):
            clustered_sentences[label].append(sentences[idx])

        # Combine sentences within the same cluster to form chunks
        semantic_chunks = [' '.join(cluster) for cluster in clustered_sentences]

        return semantic_chunks

    def sentence_chunk(self, text):
        """
        Splits text into chunks based on sentence boundaries.

        Parameters:
        text (str): The input text to chunk.

        Returns:
        List[str]: A list of sentences.
        """
        return sent_tokenize(text)

    def fixed_size_chunk(self, text, chunk_size=100):
        """
        Splits text into chunks of fixed size.

        Parameters:
        text (str): The input text to chunk.
        chunk_size (int): The size of each chunk in characters.

        Returns:
        List[str]: A list of fixed-size text chunks.
        """
        chunks = []
        for i in range(0, len(text), chunk_size):
            chunks.append(text[i:i + chunk_size])
        return chunks

    def sliding_window_chunk(self, text, window_size=100, overlap=0.5):
        """
        Splits text using a sliding window approach with overlap.

        Parameters:
        text (str): The input text to chunk.
        window_size (int): The size of the sliding window in characters.
        overlap (float): The fraction of overlap between consecutive windows (0 to 1).

        Returns:
        List[str]: A list of overlapping text chunks.
        """
        chunks = []
        step = int(window_size * (1 - overlap))
        for i in range(0, len(text) - window_size + 1, step):
            chunks.append(text[i:i + window_size])
        return chunks

    def paragraph_chunk(self, text):
        """
        Splits text into chunks based on paragraph breaks.

        Parameters:
        text (str): The input text to chunk.

        Returns:
        List[str]: A list of paragraphs.
        """
        return [p for p in text.split('\n\n') if p.strip()]

