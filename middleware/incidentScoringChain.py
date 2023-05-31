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
    template= "You are given incident Text. Do the following\n"\
        + "1.Classify whether it is Issue, Upgrade, Migration, Query\n"\
        + "2. Identify whether enough information is provided to identify root cause of incident. "\
        + "Score in 1 to 10 scale. Be strict in scoring, if input is just some open ended give low score. \n" \
        + "3. Identify whether Incident text is even slightly about data or network or client security or about Netskope products."\
        + "if yes Just say 'SUPPORTED'. If not just say 'NOT SUPPORTED', Nothing else." \
        + "4. Don\'t repeat the input incident text\n"\
        + "5. Give output ONLY in JSON Format with \"Classification\" : <val>, \"Score\" : <val>, \"Product\":\"SUPPORTED OR NOT SUPPORTED\", \"Incident\":<input_sentence>\n  Incident Text =\"{input_sentence}\""
         #and unless all details are given dont score high\n"
    prompt = PromptTemplate(
    input_variables=["input_sentence"],
        template=template,
        )

    incidentScoringChain = LLMChain(llm=llm, prompt=prompt, verbose=True)
    results= incidentScoringChain.run(input_sentence=query)
    print(results)
    return(results)


