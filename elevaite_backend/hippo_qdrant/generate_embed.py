"""
HippoRAG Step 3: Embedding Generation
Generates embeddings for passages, entities, and facts using OpenAI embeddings.
"""

import json
from typing import List, Dict, Any, Set
from qdrant_client.models import PointStruct
from hippo_config import HippoRAGConfig
from triplets_passage import TripletToPassageConverter
import logging
from tqdm import tqdm
import time

logger = logging.getLogger(__name__)

class EmbeddingGenerator:
    """Generates and stores embeddings for passages, entities, and facts"""
    
    def __init__(self, config: HippoRAGConfig):
        self.config = config
        self.batch_size = 50  
        self.rate_limit_delay = 0.1 
    
    def extract_unique_entities_and_facts(self, passages: List[Dict[str, Any]]) -> tuple:
        """Extract unique entities and facts from passages"""
        unique_entities = set()
        unique_facts = set()
        
        for passage in passages:
            # Add entities
            for entity in passage.get('entities', []):
                if entity and str(entity).strip():
                    unique_entities.add(str(entity).strip())
            
            # Add facts
            for fact in passage.get('facts', []):
                if fact and str(fact).strip():
                    unique_facts.add(str(fact).strip())
        
        logger.info(f"Extracted {len(unique_entities)} unique entities and {len(unique_facts)} unique facts")
        return list(unique_entities), list(unique_facts)
    
    def generate_embeddings_batch(self, texts: List[str], batch_size: int = None) -> List[List[float]]:
        """Generate embeddings for a batch of texts"""
        if batch_size is None:
            batch_size = self.batch_size
        
        all_embeddings = []
        
        # Process in batches to avoid API limits
        for i in tqdm(range(0, len(texts), batch_size), desc="Generating embeddings"):
            batch = texts[i:i + batch_size]
            batch_embeddings = []
            
            for text in batch:
                embedding = self.config.get_embedding(text)
                batch_embeddings.append(embedding)
                time.sleep(self.rate_limit_delay) 
            
            all_embeddings.extend(batch_embeddings)
        
        return all_embeddings
    
    def store_passages_in_qdrant(self, passages: List[Dict[str, Any]]):
        """Generate embeddings for passages and store in Qdrant"""
        logger.info("Generating and storing passage embeddings...")
        
        # Prepare texts for embedding
        passage_texts = [passage['text'] for passage in passages]
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(passage_texts)
        
        # Prepare points for Qdrant
        points = []
        for i, (passage, embedding) in enumerate(zip(passages, embeddings)):
            point = PointStruct(
                id=i,
                vector=embedding,
                payload={
                    'passage_id': passage['id'],
                    'text': passage['text'],
                    'subject': passage['subject'],
                    'predicate': passage['predicate'],
                    'object': passage['object'],
                    'triplet_id': passage['triplet_id'],
                    'type': 'passage'
                }
            )
            points.append(point)
        
        # Upload to Qdrant
        try:
            self.config.qdrant_client.upsert(
                collection_name=self.config.PASSAGES_COLLECTION,
                points=points
            )
            logger.info(f"Stored {len(points)} passage embeddings in Qdrant")
        except Exception as e:
            logger.error(f"Error storing passages in Qdrant: {e}")
            raise
    
    def store_entities_in_qdrant(self, entities: List[str]):
        """Generate embeddings for entities and store in Qdrant"""
        logger.info("Generating and storing entity embeddings...")
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(entities)
        
        # Prepare points for Qdrant
        points = []
        for i, (entity, embedding) in enumerate(zip(entities, embeddings)):
            point = PointStruct(
                id=i,
                vector=embedding,
                payload={
                    'entity': entity,
                    'text': entity,
                    'type': 'entity'
                }
            )
            points.append(point)
        
        # Upload to Qdrant
        try:
            self.config.qdrant_client.upsert(
                collection_name=self.config.ENTITIES_COLLECTION,
                points=points
            )
            logger.info(f"Stored {len(points)} entity embeddings in Qdrant")
        except Exception as e:
            logger.error(f"Error storing entities in Qdrant: {e}")
            raise
    
    def store_facts_in_qdrant(self, facts: List[str]):
        """Generate embeddings for facts and store in Qdrant"""
        logger.info("Generating and storing fact embeddings...")
        
        # Convert fact identifiers to readable text for embedding
        fact_texts = []
        for fact in facts:
            # Convert "subject_predicate_object" to readable text
            parts = fact.split('_')
            if len(parts) >= 3:
                fact_text = f"{parts[0]} {parts[1]} {' '.join(parts[2:])}"
            else:
                fact_text = fact.replace('_', ' ')
            fact_texts.append(fact_text)
        
        # Generate embeddings
        embeddings = self.generate_embeddings_batch(fact_texts)
        
        # Prepare points for Qdrant
        points = []
        for i, (fact, fact_text, embedding) in enumerate(zip(facts, fact_texts, embeddings)):
            point = PointStruct(
                id=i,
                vector=embedding,
                payload={
                    'fact_id': fact,
                    'text': fact_text,
                    'type': 'fact'
                }
            )
            points.append(point)
        
        # Upload to Qdrant
        try:
            self.config.qdrant_client.upsert(
                collection_name=self.config.FACTS_COLLECTION,
                points=points
            )
            logger.info(f"Stored {len(points)} fact embeddings in Qdrant")
        except Exception as e:
            logger.error(f"Error storing facts in Qdrant: {e}")
            raise
    
    def get_collection_stats(self):
        """Get statistics about stored embeddings"""
        stats = {}
        collections = [
            self.config.PASSAGES_COLLECTION,
            self.config.ENTITIES_COLLECTION,
            self.config.FACTS_COLLECTION
        ]
        
        for collection in collections:
            try:
                info = self.config.qdrant_client.get_collection(collection)
                stats[collection] = {
                    'points_count': info.points_count,
                    'status': info.status
                }
            except Exception as e:
                stats[collection] = {'error': str(e)}
        
        return stats

def main():
    """Main execution function"""
    # Initialize configuration
    config = HippoRAGConfig()
    generator = EmbeddingGenerator(config)
    
    # Load passages from Step 2
    converter = TripletToPassageConverter(config)
    passages = converter.load_passages()
    
    # Extract unique entities and facts
    entities, facts = generator.extract_unique_entities_and_facts(passages)
    
    # Generate and store embeddings
    generator.store_passages_in_qdrant(passages)
    generator.store_entities_in_qdrant(entities)
    generator.store_facts_in_qdrant(facts)
    
    # Return statistics
    return generator.get_collection_stats()