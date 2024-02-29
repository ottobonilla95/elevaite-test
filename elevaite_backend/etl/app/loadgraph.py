from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.llms import OpenAI
from langchain.indexes import GraphIndexCreator
from langchain.llms import OpenAI
from langchain.graphs.networkx_graph import NetworkxEntityGraph, KnowledgeTriple
from typing import List
import graph
import sys,os

os.environ["OPENAI_API_KEY"] = ""
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 5

def get_text_chunks_from_document(document: str, chunk_size: int, chunk_overlap: int):
    text_splitter = RecursiveCharacterTextSplitter( chunk_size=chunk_size, chunk_overlap  = chunk_overlap)
    text_chunks = text_splitter.create_documents([document])
    print("---Chunks- Total Count -- {}".format(len(text_chunks)))
    print (text_chunks)
    return text_chunks

def get_paragraphs_from_document(document:str):
    paragraphs = []
    current_para = []
    lines = document.split("\n")
    for line in lines:
        if line.strip() == "":
            if len(current_para)>0:
                paragraphs.append(current_para)
                current_para = []
        else:
            current_para.append(line + "\n")
    return paragraphs
        
def get_text_from_file(file_path: str) -> str:
    fd = open(file_path, "r")
    file_content = fd.read()
    return file_content

def get_relation_graph(text: str):
    graph_index = GraphIndexCreator(llm=OpenAI(temperature=0))
    kg = graph_index.from_text(text)
    print(kg.get_triples())
    return kg

def get_all_triples(kgs: List):
    all_triples = []
    for kg in kgs:
        triples = kg.get_triples()
        for triple in triples:
            all_triples.append(triple)
    return all_triples

def get_triple_str(k_triple: tuple):
    subject, predicate, object_ = k_triple
    knowledge_str =  "{" + subject + ", " + predicate + ", " + object_ +"}"
    return knowledge_str

def get_knowledge_graph(k_triples: List):
    k_graph = NetworkxEntityGraph()
    for k_triple in k_triples:
        knowledge_str = get_triple_str(k_triple=k_triple)
        k_graph.add_triple(KnowledgeTriple.from_string(knowledge_str))
    return k_graph

def write_knowledge_graph_to_file(k_triples: List, file_path: str):
    fd = open(file_path, "w")
    for k_triple in k_triples:
        knowledge_str = get_triple_str(k_triple=k_triple)
        fd.write(knowledge_str + "\n")


def main(file_path: str):
    file_content = get_text_from_file(file_path)
    #print(file_content)
    paragraphs = get_paragraphs_from_document(file_content)
    #print(len(paragraphs))
    for ix, para in enumerate(paragraphs):
        print("para -- " + str(ix))
        print(para)
    #text_chunks = get_text_chunks_from_document(document=file_content,chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    knowledge_graphs = []
    for text_chunk in paragraphs:
    #    print(text_chunk)
        knowledge_graphs.append(get_relation_graph(text=text_chunk))
    all_rel_triples = get_all_triples(kgs=knowledge_graphs)
    #kg = get_knowledge_graph(k_triples=all_rel_triples)
    #kg.write_to_gml("/home/binu/elevaite/kg/graph.gml")
    #write_knowledge_graph_to_file(k_triples=all_rel_triples, file_path="/home/binu/elevaite/kg/kg_triples_coref.txt")
    graph.create_knowledge_graph(all_rel_triples)

    

if __name__ == "__main__":
    main(file_path=sys.argv[1])





