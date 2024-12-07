import os
from arlo_modules.agents.llm_service import LLMService
from data_models import SummaryInputModel
from langchain_core.prompts import PromptTemplate
import dotenv
import json

dotenv.load_dotenv(".env")

llm = LLMService("openai",api_key=os.getenv("OPENAI_API_KEY"))

def extract_entities(entity_input):
    entity_text = ""
    for key in entity_input.keys():
        entity_text+=f"{key}: {entity_input[key]}\n"

    return entity_text


def extract_summary(summary_input: SummaryInputModel):
    system_prompt = summary_input.system_prompt
    text = summary_input.text
    entities = extract_entities(summary_input.entities)
    history = summary_input.history if summary_input.history else []
    more_context = summary_input.more_context if summary_input.more_context else ""




    prompt = PromptTemplate(
        template=system_prompt,
        input_variables=["text"],
    )
    system_prompt = "You're a helpful assistant\n"
    user_prompt = prompt.partial(text=text).format()


    response = llm.generate_response(system_prompt=system_prompt,
                                     query=user_prompt, history=history, streaming=False)


    for r in response:
        r = json.loads(r)
        final_summary = ""
        for key in r.keys():
            values = '\n- '.join(r[key]) if isinstance(r[key], list) else r[key]
            final_summary += f"{key}:\n- {values}\n\n"

        return final_summary