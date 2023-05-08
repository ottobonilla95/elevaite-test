import redis
from redis.commands.graph.edge import Edge
from redis.commands.graph.node import Node
from typing import List
import re

REDIS_URL = ""
REDIS_PORT = ""
REDIS_PASSWORD = ''

def get_graph_connection(url: str, port: str, password: str):
    return redis.Redis(host=REDIS_URL, port=REDIS_PORT, password=REDIS_PASSWORD)

def get_graph(name: str):
    con = get_graph_connection(url=REDIS_URL, port=REDIS_PORT, password=REDIS_PASSWORD)
    return con.graph(name)

def is_relation_exists(graph, subject: str, predicate: str, object_: str):
    query = "MATCH (pe1:ProductEntity {name: 'subject_'})-[re1:features {name: 'object_'}]->(pe2:ProductEntity {name: 'predicate_'}) RETURN COUNT(pe1)"
    graph_labels = {"subject_": subject, "predicate_":predicate, "object_":object_}
    for key in graph_labels:
        nentity = re.sub('\'', '', graph_labels[key])
        nentity = re.sub('\"', '', nentity)
        nentity = re.sub('\)\\nEND OF EXAMPL', "", nentity)
        query = re.sub(key, nentity, query, flags=re.IGNORECASE)
        print(key)
        print(graph_labels[key])
    print(query + " sub - " + subject + "pred - " + predicate + "obj - " + object_)
    _relations = graph.query(query)
    rel_exists = True if _relations.result_set[0][0] > 0 else False
    return rel_exists

def create_node_in_graph(graph, node_: str):
    get_nodes = re.sub("node_", node_ , "MATCH (pe1:ProductEntity {name: 'node_'}) RETURN COUNT(pe1)")
    print(get_nodes)
    node_count = graph.query(get_nodes)
    if node_count.result_set[0][0] > 0:
        print(f"Node already exists {node_}")
        return None
    else:
        product_entity = Node(label="ProductEntity", properties={"name": node_})
        print(f"{node_} successfully created")
        return product_entity

def merge_rel_in_graph(graph, sub_: str, pred_: str, obj_: str):
    merge_query = re.sub('subject_', sub_, "MERGE (pe1:ProductEntity {name: 'subject_'}) \
                            MERGE (pe2:ProductEntity {name: 'predicate_'}) \
                            MERGE (pe1)-[re1:features {name: 'object_'}]->(pe2) return count(pe1)")
    merge_query = re.sub('predicate_', pred_, merge_query)
    merge_query = re.sub('object_', obj_, merge_query)
    print(merge_query)
    node_count = graph.query(merge_query)
    print(f"{node_count.result_set[0][0]} {sub_} successfully created")
    return node_count.result_set[0][0]

def add_relation_to_graph(graph, subject, predicate, object_):
    if (is_relation_exists(graph=graph, subject=subject, predicate=predicate, object_=object_)):
        return 0
    else:
        subject_p = re.sub('\)\\nEND OF EXAMPL', "", subject)
        subject_p = re.sub('\'', "", subject_p)
        subject_p = re.sub('\"', "", subject_p)
        subject_node = create_node_in_graph(graph=graph, node_=subject_p)
        #graph.add_node(subject_node)
        predicate_p = re.sub(r'\)\\nEND OF EXAMPL', "", predicate)
        predicate_p = re.sub('\'', "", predicate_p)
        predicate_p = re.sub('\"', "", predicate_p)
        predicate_node = create_node_in_graph(graph=graph, node_=predicate_p)
        #graph.add_node(predicate_node)
        object_p = re.sub('\)\\nEND OF EXAMPL', "", object_)
        object_p = re.sub('\'', "", object_p)
        object_p = re.sub('\"', "", object_p)
        #graph.add_edge(Edge(subject_node, "features", predicate_node, properties={'name':object_p}))
        merge_rel_in_graph(graph=graph, sub_=subject_p, pred_=predicate_p, obj_=object_p)
        print(f'{subject_p} - {object_p} - {predicate_p} successfully created')
        return 1


def get_triple_str(k_triple: tuple):
    subject, predicate, object_ = k_triple
    knowledge_str =  "{" + subject + ", " + predicate + ", " + object_ +"}"
    knowledge_str_p = re.sub(r'\)\\nEND OF EXAMPL', "", knowledge_str)
    return knowledge_str_p

def create_knowledge_graph(k_triples: List):
    kg = get_graph("PanProducts")
    rel_added = 0
    for k_triple in k_triples:
        if (len(k_triple) == 3):
            subject, predicate, object_ = k_triple
            rel_count = add_relation_to_graph(graph=kg, subject=subject, predicate=predicate, object_=object_)
            if (rel_count > 0):
                rel_added += rel_count
                kg.commit()
    print(f"Number of relations added {rel_added}")
            
    
