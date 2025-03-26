from datetime import datetime
import uuid
from data_classes import PromptObject


web_agent_system_prompt = PromptObject(pid=uuid.uuid4(),
                                             prompt_label="Web Agent Prompt",
                                             prompt="You're a helpful assistant that reads web pages to answer user's query.",
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

api_agent_system_prompt = PromptObject(pid=uuid.uuid4(),
                                             prompt_label="API Agent Prompt",
                                             prompt="You're a helpful assistant that calls different APIs at your disposal to respond to user's query.",
                                             sha_hash="000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8c",
                                             uniqueLabel="APIAgentDemo",
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


data_agent_system_prompt = PromptObject(pid=uuid.uuid4(),
                                             prompt_label="API Agent Prompt",
                                             prompt="You're a helpful assistant that reads and writes to the database as per user's query.",
                                             sha_hash="000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8c",
                                             uniqueLabel="DataAgentDemo",
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


command_agent_system_prompt = PromptObject(pid=uuid.uuid4(),
                                                prompt_label="Command Agent",
                                                prompt="""You're a command agent. Assign proper tasks to the agents and look at their outputs to generate a final output. Try to ask multiple questions at once to the agent that is capable of doing so. For instance, if the agent is capable of doing three things, ask the agent to do the three things at once.

                                                Remeember, if an agent responds with the routing option "respond" then it means they are done with the task. If they respond with "continue" then they are not done with the task and you can ask them to do more tasks. If they respond with "give_up" then they are not able to do the task and you can ask another agent to do the task or tell the user you can't do it if the agents give up a lot of the times.
                                                """,
                                                sha_hash="000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8c",
                                                uniqueLabel="CommandAgent",
                                                appName="iopex",
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
