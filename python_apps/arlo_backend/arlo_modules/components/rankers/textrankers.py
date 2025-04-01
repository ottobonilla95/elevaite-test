# from sentence_transformers import SentenceTransformer, CrossEncoder
#
# class TextRanker():
#
#     @staticmethod
#     def re_ranking(query, results, model_name="cross-encoder/ms-marco-MiniLM-L-6-v2"):
#         """Re-rank the search results using a cross-encoder model."""
#
#         # Load a cross-encoder model for re-ranking
#         reranker_model = CrossEncoder(model_name)
#         # Combine query and the top retrieved documents into pairs
#         query_doc_pairs = [[query, text] for text, idx in results]
#         # Re-rank the retrieved documents
#         rerank_scores = reranker_model.predict(query_doc_pairs)
#         # Sort the documents by their re-rank score
#         reranked_results = sorted(zip(results, rerank_scores), key=lambda x: x[1], reverse=True)
#         reranked_results = [res for res, score in reranked_results]
#
#         return reranked_results