import json
import logging
import numpy as np
import re
from typing import List, Dict, Any
from hippo_config import HippoRAGConfig
from build_kg import KnowledgeGraphBuilder
from index_qdrant import HippoRAGIndexer

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class PPRPassageRetriever:
    def __init__(self, config: HippoRAGConfig):
        self.config = config
        self.graph_builder = KnowledgeGraphBuilder(config)
        self.indexer = HippoRAGIndexer(config)
        self.graph_builder.load_graph()
        self.index = self.indexer.load_index()


    def extract_entities(self, query: str) -> List[str]:
        query_lower = query.lower()
        entities = set()

        # 1. Match standard formats: date and SR ----- TODO
        date_patterns = [
            r'\d{4}-\d{2}-\d{2}',  # 2024-11-06
            r'\d{2}/\d{2}/\d{4}',  # 11/06/2024
            r'\d{2}-\d{2}-\d{4}',  # 11-06-2024
        ]
        for pat in date_patterns:
            entities.update(re.findall(pat, query))

        sr_pattern = r'\b\d{8}\b'  # 8-digit SR numbers ------TODO
        entities.update(re.findall(sr_pattern, query))

        # 2. Quoted terms
        quoted = re.findall(r'"([^"]+)"', query)
        entities.update(quoted)

        # 3. Substring match against all known entities in KG
        for candidate in self.graph_builder.entity_to_id.keys():
            if candidate.lower() in query_lower:
                entities.add(candidate)

        # 4. Final filter: keep only those that exist in the KG
        valid_entities = [e for e in entities if e in self.graph_builder.entity_to_id]

        logger.info(f"Entities extracted: {valid_entities}")
        return valid_entities
    

    def run_ppr(self, seed_entities: List[str]) -> Dict[str, float]:
        graph = self.graph_builder.graph
        id_map = self.graph_builder.entity_to_id
        N = graph.vcount()
        seeds = [id_map[e] for e in seed_entities if e in id_map]
        if not seeds:
            return {}

        personalization = np.zeros(N)
        for sid in seeds:
            personalization[sid] = 1.0 / len(seeds)

        pr = np.ones(N) / N
        damping = 0.90
        for _ in range(100):
            new_pr = np.zeros(N)
            for v in range(N):
                incoming = graph.incident(v, mode="in")
                for edge_id in incoming:
                    src = graph.es[edge_id].source
                    out_deg = graph.degree(src, mode="out")
                    if out_deg > 0:
                        new_pr[v] += pr[src] / out_deg
                new_pr[v] = damping * new_pr[v] + (1 - damping) * personalization[v]
            if np.linalg.norm(pr - new_pr, 1) < 1e-6:
                break
            pr = new_pr

        id_to_entity = {v: k for k, v in id_map.items()}
        return {id_to_entity[i]: pr[i] for i in range(N) if i in id_to_entity}

    def retrieve_from_passages(self, entity_list: List[str], top_k: int = 50) -> List[Dict[str, Any]]:
        results = []
        for entity in entity_list:
            try:
                vector = self.config.get_embedding(entity)
                search_result = self.config.qdrant_client.search(
                    collection_name="hipporag_passages",
                    query_vector=vector,
                    limit=top_k,
                    with_payload=True,
                    with_vectors=False,
                )
                for r in search_result:
                    payload = r.payload
                    results.append({
                        "text": payload.get("text", ""),
                        "subject": payload.get("subject", ""),
                        "predicate": payload.get("predicate", ""),
                        "object": payload.get("object", ""),
                        "score": r.score,
                        "source": "ppr_passage",
                        "query_entity": entity
                    })
            except Exception as e:
                logger.warning(f"Failed search for {entity}: {e}")
        return results

    def retrieve(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        entities = self.extract_entities(query)
        if not entities:
            logger.warning("No valid seed entities, fallback to vector search")
            return self.retrieve_from_passages([query], top_k=max_results)

        ppr_scores = self.run_ppr(entities)
        top_entities = sorted(ppr_scores.items(), key=lambda x: x[1], reverse=True)[:20]
        top_entity_list = [ent for ent, _ in top_entities]

        results = self.retrieve_from_passages(top_entity_list, top_k=max_results)
        return results


def main():
    config = HippoRAGConfig()
    retriever = PPRPassageRetriever(config)
    query = "Which SRs are related to Centerville and who resolved them?"
    logger.info(f"Query: {query}")
    results = retriever.retrieve(query)
    for i, r in enumerate(results[:10]):
        print(f"{i+1}. {r['text']} (score: {r['score']:.3f}, entity: {r['query_entity']})")


if __name__ == "__main__":
    main()
