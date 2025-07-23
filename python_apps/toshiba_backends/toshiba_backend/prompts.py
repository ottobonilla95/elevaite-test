from datetime import datetime
import uuid
from data_classes import PromptObject
from prompt_text import *

toshiba_agent_system_prompt = PromptObject(pid=uuid.uuid4(),
                                             prompt_label="Toshiba Agent Prompt",
                                             prompt=TOSHIBA_AGENT_PROMPT6,
                                             sha_hash="000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8c",
                                             uniqueLabel="WebAgentDemo",
                                             appName="iOPEX",
                                             version="1.0",
                                             createdTime=datetime.now(),
                                             deployedTime=None,
                                             last_deployed=None,
                                             modelProvider="OpenAI",
                                             modelName="GPT-4o-mini",
                                             isDeployed=False,
                                             tags=["search", "web"],
                                             hyper_parameters={"temperature": "0.7"},
                                             variables={"search_engine": "google"})