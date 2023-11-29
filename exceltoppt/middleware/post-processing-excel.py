'''
Functions pretaining to
    1. Querty Excel Workbook data using langchain csv agent
    
'''

from langchain_experimental.agents.agent_toolkits import create_csv_agent
from langchain.chat_models import ChatOpenAI
from langchain.agents.agent_types import AgentType

import openai
import os
from dotenv import load_dotenv

load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")
os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")
current_woring_dir = os.path.dirname(os.path.realpath(__file__))


def ask_csv_agent(sheet_list, question):
    try:
        agent = create_csv_agent(
            ChatOpenAI(temperature=0, model="gpt-4-1106-preview"),
            [sheet_list],
            verbose=False,
            agent_type=AgentType.OPENAI_FUNCTIONS
        )
        answer = agent.run(question)

        return {"response" : "Success", "answer" : answer}
    except  Exception as e:
        return str(e)