import openai
from langchain.prompts import load_prompt
from langchain.chains import LLMChain
from langchain.agents import Tool
from langchain import PromptTemplate
from langchain.llms import OpenAI
from _global import updateStatus
import json
import os

llm = OpenAI()
llm.temperature=0

def func_incidentScoringChain (query: str):
    updateStatus("func_incidentScoringChain")
    template=  "You are given incident Text. Do the following\n"\
             + "1.Classify  whether it is Issue, Upgrade, Migration, Query\n"\
             + "2. Identify whether enough information is provided to identify root cause of incident. "\
             + "Score in 1 to 10 scale. Be  strict in scoring, if input is just some open ended give low score. \n" \
             + "3. Identify whether Incident is about Palo Alto products, list of products below \n{Products}\n" \
             + "Just say 'PALO-ALTO' or  'NOT SUPPORTED', Nothing else." \
             + "5. Don\'t repeat the input incident text\n"\
             + "6. Give output ONLY in JSON Format with \"Classification\" : <val>, \"Score\" : <val>, \"Product\":\"PAL-ALTO OR NOT SUPPORTED\", \"Incident\":<input_sentence>\n  Incident Text =\"{input_sentence}\""
    #and unless all details are given dont score high\n"
    product_list="Product List below\n CLOUD NGFW\n,THREAT INTELLIGENCE MANAGEMENT\n,CORTEX XDR\n,CORTEX XSOAR\n,CORTEX XPANSE\n,DNS SECURITY\n,ENTERPRISE DATA LOSS PREVENTION\n,EXPEDITION\n,GLOBALPROTECT\n,IOT SECURITY\n,NEXT-GENERATION FIREWALLS\n,PA-SERIES\n,PANORAMA\n,PRISMA ACCESS\n,PRISMA CLOUD\n,PRISMA SD-WAN\n,SAAS SECURITY\n,THREAT PREVENTION\n,ADVANCED THREAT PREVENTION\n,ADVANCED URL FILTERING\n,VM-SERIES\n,WILDFIRE"
    prompt = PromptTemplate(
                input_variables=["Products", "input_sentence"],
                template=template,
             )
    
    incidentScoringChain = LLMChain(llm=llm, prompt=prompt, verbose=True)
    results= incidentScoringChain.run(input_sentence=query, Products=product_list)
    return(results)
