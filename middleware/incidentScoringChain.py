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
    template= "You are given incident text within the <input_sentence></input_sentence> tags. Do the following based on the incident text:\n"\
        + "1.Classify whether it is Issue, Upgrade, Migration, Query and place your answer in <classification_val>\n"\
        + "2. Identify whether enough information is provided to identify root cause of incident. "\
        + "Score the incident text strictly in 1 to 10 scale and place your answer in <val> as an integer. Be strict in your scoring.\n" \
        + "3. Identify whether Incident text is even slightly about data or network or client security or about Netskope products."\
        + "If yes Just say 'SUPPORTED'. If not just say 'NOT SUPPORTED', Nothing else. Place your answer in <support_val>" \
        + "4. Don\'t repeat the input incident text\n"\
        + "5. Give output ONLY in JSON Format with \"Classification\" : <classification_val>, \"Score\" : <val>, \"Product\":<support_val>" \
        "\n Here is the incident text \n" \
        "<input_sentence>{input_sentence} </input_sentence>"
         #and unless all details are given dont score high\n"
    prompt = PromptTemplate(
    input_variables=["input_sentence"],
        template=template,
        )

    incidentScoringChain = LLMChain(llm=llm, prompt=prompt, verbose=True)
    results= incidentScoringChain.run(input_sentence=query,)
    print(results)
    return(results)


