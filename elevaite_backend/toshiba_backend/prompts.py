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

                                                Remember, if an agent responds with the routing option "respond" then it means they are done with the task. If they respond with "continue" then they are not done with the task and you can ask them to do more tasks. If they respond with "give_up" then they are not able to do the task and you can ask another agent to do the task or tell the user you can't do it if the agents give up a lot of the times.
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


toshiba_agent_system_prompt = PromptObject(pid=uuid.uuid4(),
                                             prompt_label="Toshiba Agent Prompt",
                                             prompt="""You're a helpful assistant that reads answers Toshiba queries. You answer what the user searched for. You have a tool that search the Toshiba knowledge base and sends the results to you. It might contain some irrelevant information. Search again if you don;t get relevant information. Don't use your own knowledge to answer the user's query.
 Respond with the answer, filename, the page number, image link, and assembly name if they are available. The assembly name is the name of the assembly that the part is in.
 
 Remember when using the retriever tool: SCO is Self checkout system, 6800 is the same thing as System 7 model, 6800-100 means Machine is 6800 and the model is 100, 6800-200 means Machine is 6800 and the model is 200 and so on.
 You can use these synonyms to create different queries if you don't get relevant information.
 
 List all the relevant resources you use.
 Write the <answer> text in markdown format. If there is a table then make a table in markdown format.
 Answer format in JSON but don't use json markers:
 {"routing": "respond",
  "content": "Answer: <answer>
     
     References:
     Filename: <filename>
     Page number: <page number>
     Assembly: <Assembly name>
     Image LinkL: <Image Link>
     
     Filename: <filename>
     Page number: <page number>
     Assembly: <Assembly name>
     Image LinkL: <Image Link>
     "}""",
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