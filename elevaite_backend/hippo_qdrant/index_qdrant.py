import json
import os
from typing import List, Dict, Any, Optional
from hippo_config import HippoRAGConfig
from triplets_passage import TripletToPassageConverter
from generate_embed import EmbeddingGenerator
from build_kg import KnowledgeGraphBuilder
import logging

logger = logging.getLogger(__name__)

class HippoRAGIndexer:
    """Handles indexing and storage consolidation for HippoRAG"""
    
    def __init__(self, config: HippoRAGConfig):
        self.config = config
        self.embedding_generator = EmbeddingGenerator(config)
        self.graph_builder = KnowledgeGraphBuilder(config)
    
    def create_comprehensive_index(self) -> Dict[str, Any]:
        """Create a comprehensive index mapping all components"""
        logger.info("Creating comprehensive index...")
        
        # Load all components
        converter = TripletToPassageConverter(self.config)
        passages = converter.load_passages()
        
        # Load graph
        self.graph_builder.load_graph()
        
        # Create mappings
        index = {
            'metadata': {
                'total_passages': len(passages),
                'total_entities': len(self.graph_builder.entity_to_id),
                'total_facts': len(self.graph_builder.fact_nodes),
                'graph_stats': self.graph_builder.get_graph_statistics()
            },
            'entity_to_passages': self._create_entity_passage_mapping(passages),
            'fact_to_passages': self._create_fact_passage_mapping(passages),
            'passage_to_entities': self._create_passage_entity_mapping(passages),
            'passage_to_facts': self._create_passage_fact_mapping(passages),
            'entity_relationships': self._create_entity_relationship_mapping(),
            'search_index': self._create_search_index(passages)
        }
        
        return index
    
    def _create_entity_passage_mapping(self, passages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Map entities to passages that mention them"""
        entity_to_passages = {}
        
        for passage in passages:
            passage_id = passage['id']
            entities = passage.get('entities', [])
            
            for entity in entities:
                entity_str = str(entity).strip()
                if entity_str not in entity_to_passages:
                    entity_to_passages[entity_str] = []
                entity_to_passages[entity_str].append(passage_id)
        
        logger.info(f"Created entity-to-passage mapping for {len(entity_to_passages)} entities")
        return entity_to_passages
    
    def _create_fact_passage_mapping(self, passages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Map facts to passages that contain them"""
        fact_to_passages = {}
        
        for passage in passages:
            passage_id = passage['id']
            facts = passage.get('facts', [])
            
            for fact in facts:
                fact_str = str(fact).strip()
                if fact_str not in fact_to_passages:
                    fact_to_passages[fact_str] = []
                fact_to_passages[fact_str].append(passage_id)
        
        logger.info(f"Created fact-to-passage mapping for {len(fact_to_passages)} facts")
        return fact_to_passages
    
    def _create_passage_entity_mapping(self, passages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Map passages to entities they mention"""
        passage_to_entities = {}
        
        for passage in passages:
            passage_id = passage['id']
            entities = [str(e).strip() for e in passage.get('entities', [])]
            passage_to_entities[passage_id] = entities
        
        return passage_to_entities
    
    def _create_passage_fact_mapping(self, passages: List[Dict[str, Any]]) -> Dict[str, List[str]]:
        """Map passages to facts they contain"""
        passage_to_facts = {}
        
        for passage in passages:
            passage_id = passage['id']
            facts = [str(f).strip() for f in passage.get('facts', [])]
            passage_to_facts[passage_id] = facts
        
        return passage_to_facts
    
    def _create_entity_relationship_mapping(self) -> Dict[str, Dict[str, List[str]]]:
        """Create mapping of entity relationships from the graph"""
        if self.graph_builder.graph is None:
            return {}
        
        relationships = {}
        
        for entity, entity_id in self.graph_builder.entity_to_id.items():
            relationships[entity] = {
                'connected_entities': [],
                'predicates': [],
                'neighbors': self.graph_builder.find_entity_neighbors(entity, max_hops=1)
            }
            
            # Get outgoing edges to find direct relationships
            for edge in self.graph_builder.graph.es.select(_source=entity_id):
                target_id = edge.target
                target_vertex = self.graph_builder.graph.vs[target_id]
                
                if target_vertex['type'] == 'entity':
                    target_entity = target_vertex['name']
                    # Fix igraph edge attribute access
                    predicate = edge['predicate'] if 'predicate' in edge.attributes() else 'connected_to'
                    
                    relationships[entity]['connected_entities'].append(target_entity)
                    relationships[entity]['predicates'].append(predicate)
        
        logger.info(f"Created relationship mapping for {len(relationships)} entities")
        return relationships
    
    def _create_search_index(self, passages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create inverted index for text search"""
        search_index = {
            'word_to_passages': {},
            'entity_synonyms': {},  # TODO
            'predicate_variations': {}  # TODO
        }
        
        # Simple word-based inverted index
        for passage in passages:
            passage_id = passage['id']
            text = passage['text'].lower()
            
            # Simple tokenization (can be enhanced with proper NLP)
            words = text.replace('.', '').replace(',', '').split()
            
            for word in words:
                word = word.strip()
                if len(word) > 2:  
                    if word not in search_index['word_to_passages']:
                        search_index['word_to_passages'][word] = []
                    if passage_id not in search_index['word_to_passages'][word]:
                        search_index['word_to_passages'][word].append(passage_id)
        
        logger.info(f"Created search index with {len(search_index['word_to_passages'])} words")
        return search_index
    
    def save_index(self, index: Dict[str, Any], filename: str = "hipporag_index.json"):
        """Save the comprehensive index to file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved comprehensive index to {filename}")
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def load_index(self, filename: str = "hipporag_index.json") -> Dict[str, Any]:
        """Load the comprehensive index from file"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                index = json.load(f)
            logger.info(f"Loaded comprehensive index from {filename}")
            return index
        except Exception as e:
            logger.error(f"Error loading index: {e}")
            raise
    
    def verify_storage_integrity(self) -> Dict[str, Any]:
        """Verify that all components are properly stored"""
        integrity_report = {
            'qdrant_collections': {},
            'graph_file': False,
            'passages_file': False,
            'index_file': False,
            'errors': []
        }
        
        # Check Qdrant collections
        collections = [
            self.config.PASSAGES_COLLECTION,
            self.config.ENTITIES_COLLECTION,
            self.config.FACTS_COLLECTION
        ]
        
        for collection in collections:
            try:
                info = self.config.qdrant_client.get_collection(collection)
                integrity_report['qdrant_collections'][collection] = {
                    'exists': True,
                    'points_count': info.points_count,
                    'status': info.status
                }
            except Exception as e:
                integrity_report['qdrant_collections'][collection] = {
                    'exists': False,
                    'error': str(e)
                }
                integrity_report['errors'].append(f"Qdrant collection {collection}: {e}")
        
        files_to_check = [
            (self.config.GRAPH_FILE, 'graph_file'),
            (self.config.PASSAGES_FILE, 'passages_file'),
            ('hipporag_index.json', 'index_file')
        ]
        
        for filepath, key in files_to_check:
            if os.path.exists(filepath):
                integrity_report[key] = True
            else:
                integrity_report[key] = False
                integrity_report['errors'].append(f"Missing file: {filepath}")
        
        return integrity_report
    
    def optimize_storage(self):
        """Optimize storage for better performance (placeholder for future enhancements)"""
        logger.info("Storage optimization not implemented in this version")
        # Future enhancements could include:
        # - Qdrant index optimization
        # - Graph compression
        # - Cache management

def main():
    """Main execution function"""
    # Initialize configuration
    config = HippoRAGConfig()
    indexer = HippoRAGIndexer(config)
    
    # Create comprehensive index
    index = indexer.create_comprehensive_index()
    
    # Save index
    indexer.save_index(index)
    
    # Verify storage integrity
    integrity_report = indexer.verify_storage_integrity()
    
    return index, integrity_report
