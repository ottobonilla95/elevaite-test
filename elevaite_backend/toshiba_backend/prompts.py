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
                                             prompt="""You're a helpful assistant that reads toshiba pages to answers what the user searched for. You have a tool that search the Toshiba knowledge base and sends the results to you. Use the results to answer the user's query. It might contain some irrelevant information. Search again if you don;t get relevant information but don't search more than 5 times. Don't use your own knowledge to answer the user's query.
For part number questions the assembly name must be exact. Ask the user for the exact assembly name and offer them the list of valid assembly names.
Here are the valid assembly names: 
'Standalone parts',
 'Fasteners',
 'Power Cords',
 'Cables',
 'Security conveyor and transport conveyor units',
 'Transport conveyor',
 'Security conveyor',
 'XXL Bagger base+ extension with enclosed cabinet (no weight security)(8Q3815)',
 'XXL Bagger base with enclosed cabinet (weight security) (8Q3938)',
 'XXL Bagger base + extension with pedestal legs (weight security)(8Q3990)',
 'XXL Bagger Base + Extension with pedestal legs (no weight security)(8Q3742)',
 'XXL Bagger base with pedestal legs (no weight security) (8Q3741)',
 'Carousel bagging unit',
 'Enclosed extra large bagging unit (Models 20C and 30C)',
 'Extra large bagging unit',
 'Large bagging unit',
 'Medium bagging unit',
 'Small bagging unit',
 'Enhanced scanner/scale lock',
 'Enhanced scanner/scale',
 'Original scanner/scale',
 'Cashless cabinet',
 'Bulk coin recycler',
 'Banknote recycler',
 'Cash cabinet door',
 'Cash cabinet general parts',
 'TCx EDGEcam+',
 'Lane PC',
 'Core unit upper front cover',
 'Core unit internal parts',
 'Transaction awareness light',
 'Updated Touchscreen Lane PC Assembly',
 'Static Monitor Mounting Assembly',
 'Core unit exterior'
 
 Offer the user some valid assembly names if the user asks for the assembly name or if the user asks for the part number but the assembly name is not clear. Offer only a few assembly names at a time to choose from. The assembly name should be in a list.
 
 """,
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