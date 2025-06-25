"""
HippoRAG Step 4: Knowledge Graph Construction
Builds a knowledge graph using igraph from the triplets and passages.
"""

import json
import pickle
import igraph as ig
from typing import List, Dict, Any, Set, Tuple
from hippo_config import HippoRAGConfig
from triplets_passage import TripletToPassageConverter
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

class KnowledgeGraphBuilder:    
    def __init__(self, config: HippoRAGConfig):
        self.config = config
        self.graph = None
        self.entity_to_id = {}
        self.id_to_entity = {}
        self.fact_nodes = {}
        self.passage_nodes = {}
    
    def build_graph_from_passages(self, passages: List[Dict[str, Any]]) -> ig.Graph:
        """Build knowledge graph from passages"""
        logger.info("Building knowledge graph...")
        self.graph = ig.Graph(directed=True)
        
        all_entities = set()
        all_facts = set()
        
        for passage in passages:
            # Add entities
            for entity in passage.get('entities', []):
                if entity and str(entity).strip():
                    all_entities.add(str(entity).strip())
            
            # Add facts
            for fact in passage.get('facts', []):
                if fact and str(fact).strip():
                    all_facts.add(str(fact).strip())
        
        # Add entity nodes
        entity_list = list(all_entities)
        self.graph.add_vertices(len(entity_list))
        
        # Create entity mappings
        for i, entity in enumerate(entity_list):
            self.entity_to_id[entity] = i
            self.id_to_entity[i] = entity
            self.graph.vs[i]['name'] = entity
            self.graph.vs[i]['type'] = 'entity'
            self.graph.vs[i]['label'] = entity
        
        # Add fact nodes
        fact_start_id = len(entity_list)
        fact_list = list(all_facts)
        self.graph.add_vertices(len(fact_list))
        
        for i, fact in enumerate(fact_list):
            node_id = fact_start_id + i
            self.fact_nodes[fact] = node_id
            self.graph.vs[node_id]['name'] = fact
            self.graph.vs[node_id]['type'] = 'fact'
            self.graph.vs[node_id]['label'] = fact
        
        # Add passage nodes
        passage_start_id = fact_start_id + len(fact_list)
        self.graph.add_vertices(len(passages))
        
        for i, passage in enumerate(passages):
            node_id = passage_start_id + i
            self.passage_nodes[passage['id']] = node_id
            self.graph.vs[node_id]['name'] = passage['id']
            self.graph.vs[node_id]['type'] = 'passage'
            self.graph.vs[node_id]['text'] = passage['text']
            self.graph.vs[node_id]['label'] = passage['id']
        
        logger.info(f"Added {len(entity_list)} entity nodes, {len(fact_list)} fact nodes, {len(passages)} passage nodes")
        
        # Add edges
        self._add_triplet_edges(passages)
        self._add_entity_fact_edges(passages)
        self._add_passage_edges(passages)
        
        logger.info(f"Knowledge graph built with {self.graph.vcount()} nodes and {self.graph.ecount()} edges")
        return self.graph
    
    def _add_triplet_edges(self, passages: List[Dict[str, Any]]):
        """Add edges based on triplet relationships"""
        edges_added = 0
        
        for passage in passages:
            subject = passage.get('subject')
            predicate = passage.get('predicate')
            obj = passage.get('object')
            
            if subject and obj:
                subject_str = str(subject).strip()
                obj_str = str(obj).strip()
                
                if subject_str in self.entity_to_id and obj_str in self.entity_to_id:
                    subject_id = self.entity_to_id[subject_str]
                    obj_id = self.entity_to_id[obj_str]
                    
                    # Add edge with predicate as label
                    self.graph.add_edge(subject_id, obj_id)
                    edge_id = self.graph.ecount() - 1
                    self.graph.es[edge_id]['label'] = str(predicate)
                    self.graph.es[edge_id]['type'] = 'triplet'
                    self.graph.es[edge_id]['predicate'] = str(predicate)
                    edges_added += 1
        
        logger.info(f"Added {edges_added} triplet edges")
    
    def _add_entity_fact_edges(self, passages: List[Dict[str, Any]]):
        """Add edges between entities and facts"""
        edges_added = 0
        
        for passage in passages:
            # Connect entities to facts
            entities = passage.get('entities', [])
            facts = passage.get('facts', [])
            
            for entity in entities:
                entity_str = str(entity).strip()
                if entity_str in self.entity_to_id:
                    entity_id = self.entity_to_id[entity_str]
                    
                    for fact in facts:
                        fact_str = str(fact).strip()
                        if fact_str in self.fact_nodes:
                            fact_id = self.fact_nodes[fact_str]
                            
                            # Add bidirectional edges
                            self.graph.add_edge(entity_id, fact_id)
                            edge_id = self.graph.ecount() - 1
                            self.graph.es[edge_id]['type'] = 'entity_fact'
                            self.graph.es[edge_id]['label'] = 'participates_in'
                            
                            self.graph.add_edge(fact_id, entity_id)
                            edge_id = self.graph.ecount() - 1
                            self.graph.es[edge_id]['type'] = 'fact_entity'
                            self.graph.es[edge_id]['label'] = 'involves'
                            
                            edges_added += 2
        
        logger.info(f"Added {edges_added} entity-fact edges")
    
    def _add_passage_edges(self, passages: List[Dict[str, Any]]):
        """Add edges between passages and entities/facts"""
        edges_added = 0
        
        for passage in passages:
            passage_id = self.passage_nodes.get(passage['id'])
            if passage_id is None:
                continue
            
            # Connect passage to entities
            entities = passage.get('entities', [])
            for entity in entities:
                entity_str = str(entity).strip()
                if entity_str in self.entity_to_id:
                    entity_id = self.entity_to_id[entity_str]
                    
                    # Add bidirectional edges
                    self.graph.add_edge(passage_id, entity_id)
                    edge_id = self.graph.ecount() - 1
                    self.graph.es[edge_id]['type'] = 'passage_entity'
                    self.graph.es[edge_id]['label'] = 'mentions'
                    
                    self.graph.add_edge(entity_id, passage_id)
                    edge_id = self.graph.ecount() - 1
                    self.graph.es[edge_id]['type'] = 'entity_passage'
                    self.graph.es[edge_id]['label'] = 'mentioned_in'
                    
                    edges_added += 2
            
            # Connect passage to facts
            facts = passage.get('facts', [])
            for fact in facts:
                fact_str = str(fact).strip()
                if fact_str in self.fact_nodes:
                    fact_id = self.fact_nodes[fact_str]
                    
                    # Add bidirectional edges
                    self.graph.add_edge(passage_id, fact_id)
                    edge_id = self.graph.ecount() - 1
                    self.graph.es[edge_id]['type'] = 'passage_fact'
                    self.graph.es[edge_id]['label'] = 'contains'
                    
                    self.graph.add_edge(fact_id, passage_id)
                    edge_id = self.graph.ecount() - 1
                    self.graph.es[edge_id]['type'] = 'fact_passage'
                    self.graph.es[edge_id]['label'] = 'contained_in'
                    
                    edges_added += 2
        
        logger.info(f"Added {edges_added} passage edges")
    
    def add_synonymy_edges(self, similarity_threshold: float = 0.8):
        """Add synonymy edges between similar entities (placeholder for future enhancement)"""
        # This would require additional entity similarity computation
        # For now, we'll skip this to keep the implementation simple
        logger.info("Synonymy edges not implemented in this version")
    
    def save_graph(self, filename: str = None):
        """Save the knowledge graph to file"""
        if filename is None:
            filename = self.config.GRAPH_FILE
        
        try:
            graph_data = {
                'graph': self.graph,
                'entity_to_id': self.entity_to_id,
                'id_to_entity': self.id_to_entity,
                'fact_nodes': self.fact_nodes,
                'passage_nodes': self.passage_nodes
            }
            
            with open(filename, 'wb') as f:
                pickle.dump(graph_data, f)
            
            logger.info(f"Saved knowledge graph to {filename}")
        except Exception as e:
            logger.error(f"Error saving graph: {e}")
            raise
    
    def load_graph(self, filename: str = None):
        """Load the knowledge graph from file"""
        if filename is None:
            filename = self.config.GRAPH_FILE
        
        try:
            with open(filename, 'rb') as f:
                graph_data = pickle.load(f)
            
            self.graph = graph_data['graph']
            self.entity_to_id = graph_data['entity_to_id']
            self.id_to_entity = graph_data['id_to_entity']
            self.fact_nodes = graph_data['fact_nodes']
            self.passage_nodes = graph_data['passage_nodes']
            
            logger.info(f"Loaded knowledge graph from {filename}")
            return self.graph
        except Exception as e:
            logger.error(f"Error loading graph: {e}")
            raise
    
    def get_graph_statistics(self) -> Dict[str, Any]:
        """Get statistics about the knowledge graph"""
        if self.graph is None:
            return {'error': 'Graph not built yet'}
        
        # Count nodes by type
        node_types = defaultdict(int)
        for vertex in self.graph.vs:
            node_types[vertex['type']] += 1
        
        # Count edges by type
        edge_types = defaultdict(int)
        for edge in self.graph.es:
            edge_types[edge['type']] += 1
        
        return {
            'total_nodes': self.graph.vcount(),
            'total_edges': self.graph.ecount(),
            'node_types': dict(node_types),
            'edge_types': dict(edge_types),
            'is_directed': self.graph.is_directed(),
            'density': self.graph.density()
        }
    
    def find_entity_neighbors(self, entity: str, max_hops: int = 3) -> List[str]:
        """Find neighboring entities within max_hops"""
        if entity not in self.entity_to_id:
            return []
        
        entity_id = self.entity_to_id[entity]
        neighbors = set()
        
        # BFS to find neighbors within max_hops
        queue = [(entity_id, 0)]
        visited = {entity_id}
        
        while queue:
            current_id, hops = queue.pop(0)
            
            if hops < max_hops:
                # Get all neighbors
                for neighbor_id in self.graph.neighbors(current_id):
                    if neighbor_id not in visited:
                        visited.add(neighbor_id)
                        queue.append((neighbor_id, hops + 1))
                        
                        # Add to neighbors if it's an entity
                        if self.graph.vs[neighbor_id]['type'] == 'entity':
                            neighbors.add(self.id_to_entity[neighbor_id])
        
        return list(neighbors)

def main():
    """Main execution function"""
    # Initialize configuration
    config = HippoRAGConfig()
    builder = KnowledgeGraphBuilder(config)
    
    # Load passages from Step 2
    converter = TripletToPassageConverter(config)
    passages = converter.load_passages()
    
    # Build knowledge graph
    graph = builder.build_graph_from_passages(passages)
    
    # Save the graph
    builder.save_graph()
    
    # Return statistics
    return builder.get_graph_statistics()
