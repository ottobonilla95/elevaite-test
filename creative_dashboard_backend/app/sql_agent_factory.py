from langchain_openai import ChatOpenAI
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain.agents.agent_types import AgentType
from langchain_community.utilities import SQLDatabase
from langchain import hub
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory
from db_connector import db_connector
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_campaign_sql_agent(conversation_history=None, temperature=0):
    """
    Factory function to create a SQL agent specialized for campaign data.
    
    Args:
        conversation_history: List of conversation messages
        temperature: Temperature for the LLM
        
    Returns:
        agent_executor: The SQL agent
        query_extractor: Callback handler for extracting SQL queries
    """
    # Initialize database connection
    db = SQLDatabase.from_uri(
        f"postgresql://{db_connector.username}:{db_connector.password}@{db_connector.host}:{db_connector.port}/{db_connector.database}",
        include_tables=["campaign_data_table","creative_data_table"],
        sample_rows_in_table_info=3
    )
    API_KEY = os.environ["OPENAI_API_KEY"]
    # Initialize the language model
    llm = ChatOpenAI(temperature=temperature, model="gpt-4o-mini",api_key=API_KEY)
    # Get table info
    table_info = db.get_table_info()
    # Create a proper ChatPromptTemplate
    # filter_instructions = ""
    # if selected_brand or selected_ad_surface or selected_campaign:
    #     filter_instructions = "IMPORTANT: You must filter your queries according to the user's current selection:\n"
        
    #     if selected_brand:
    #         filter_instructions += f"- Brand: {selected_brand}\n"
        
    #     if selected_ad_surface:
    #         filter_instructions += f"- Ad Surface: {selected_ad_surface}\n"
        
    #     if selected_campaign:
    #         filter_instructions += f"- Campaign: {selected_campaign}\n"
        
    #     filter_instructions += "\nAll SQL queries MUST include these filters in the WHERE clause to ensure results are relevant to the user's current view(Unless specified otherwise).\n"

    system_message = """You are an agent designed to interact with a SQL database.
        Given an input question, create a syntactically correct PostgreSQL query to run, then look at the results of the query and return the answer.
        Unless the user specifies a specific number of examples they wish to obtain, always limit your query to at most 10 results.
        You can order the results by a relevant column to return the most interesting examples in the database.
        Never query for all the columns from a specific table, only ask for the relevant columns given the question.
        You have access to tools for interacting with the database.
        Only use the below tools. Only use the information returned by the below tools to construct your final answer.
        You MUST double check your query before executing it. If you get an error while executing a query, rewrite the query and try again.
        
        DO NOT make any DML statements (INSERT, UPDATE, DELETE, DROP etc.) to the database.
        To start you should ALWAYS look at the tables in the database to see what you can query.
        Do NOT skip this step.
        Then you should query the schema of the most relevant tables.
        {table_info}

        The database contains two main tables:
        1. campaign_data_table: Contains campaign data with metrics like impressions, clicks, and conversions.
        2. creative_data_table: Contains creative asset data related to campaigns.

        For campaign_data_table, key metrics you can analyze:
        - booked_impressions: The number of impressions booked for a campaign
        - clickable_impressions: The number of impressions that were clickable
        - clicks: The number of clicks received
        - conversion: The conversion rate
        - ecpm: Effective cost per thousand impressions
        - budget: The campaign budget

        For creative_data_table, you can analyze:
        - creative_id: Unique identifier for the creative
        - campaign_name: Name of the campaign (can be joined with campaign_data_table)
        - industry_sectors: Industry sectors the creative belongs to
        - brand_logo details: Presence, size, location, and timing of brand logos
        - text details: Colors, sizes, locations, and content analysis
        - creative_classification: Classification of the creative
        - creative_video_length: Length of video creatives
        - visual elements: Information about landscape, person, animal content

        When analyzing creatives, consider:
        - Brand visibility metrics: logo presence, size, location
        - Text usage patterns: colors, sizes, word counts
        - Visual content analysis: presence of people, animals, landscapes
        - Relationship between creative elements and campaign performance

        You can join tables using campaign_name to analyze how creative elements impact campaign performance.
        
        Always provide insights that would be valuable for marketing analysis.
    """
    
    # Create the chat prompt template
    chat_prompt = ChatPromptTemplate.from_messages([
        ("system", system_message),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad")
    ])
    
    # Setup conversation memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Add conversation history to memory
    if conversation_history:
        for message in conversation_history:
            if message["role"] == "user":
                memory.chat_memory.add_user_message(message["content"])
            else:
                memory.chat_memory.add_ai_message(message["content"])
    
    # # Create SQL query extractor callback
    # query_extractor = SQLQueryExtractor()
    
    print("PROMPT SENT: ",chat_prompt)
    # Create the SQL agent
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        agent_type="openai-tools",
        verbose=True,
        prompt=chat_prompt,
        memory=memory
    )
    
    return agent_executor
