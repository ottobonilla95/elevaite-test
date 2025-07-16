import asyncio
import os
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from utils import client

from utils import agent_schema
from data_classes import Agent
from utils import function_schema
from prompts import toshiba_agent_system_prompt
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from load_data_table import load_excel_to_postgres


@function_schema
async def sql_query_executor(query: str) -> list:
    """
    SQL QUERY EXECUTOR TOOL

    Use this tool to execute SQL queries against the sr_data_agent_table.

    EXAMPLES:
    Example: query="SELECT * FROM sr_data_agent_table LIMIT 10"
    Example: query="SELECT count(*) FROM sr_data_agent_table WHERE status = 'closed'"
    Example: query="SELECT technician, COUNT(*) FROM sr_data_agent_table GROUP BY technician ORDER BY COUNT(*) DESC LIMIT 5"
    """
    database_url = os.getenv("SQLALCHEMY_DATABASE_URL")
    if not database_url:
        return [{"error": "Database URL not configured"}]

    try:
        engine = create_async_engine(database_url)
        async with engine.begin() as connection:
            result = await connection.execute(text(query))
            columns = result.keys()
            rows = result.fetchmany(10)

            # Convert to list of dictionaries
            # Convert to Markdown table
            if rows:
                header = "| " + " | ".join(columns) + " |"
                separator = "| " + " | ".join("---" for _ in columns) + " |"
                data_rows = [
                    "| " + " | ".join(str(cell) if cell is not None else "" for cell in row) + " |"
                    for row in rows
                ]
                markdown_table = "\n".join([header, separator] + data_rows)
                return [markdown_table]
            else:
                return ["No results found."]
    except Exception as e:
        return [{"error": str(e)}]


@agent_schema
class SQLAgent(Agent):
    async def execute(self, query: Any, qid: str, session_id: str, chat_history: Any, user_id: str, agent_flow_id: str) -> Any:
        """
        SQL agent to answer questions by querying the sr_data_agent_table.
        Returns a complete response with the answer based on SQL query results.
        """
        tries = 0
        max_tries = self.max_retries
        start_time = datetime.now()
        system_prompt = """You are an SQL expert agent designed to help users query the sr_data_agent_table.
        Your job is to understand natural language questions about service requests (SRs) and translate them into SQL queries.
        
        
        The list of valid customer names are:
        # Company Names List
        
        - ITX Merken
        - BELLA FLANADES
        - Bass Pro Shops LLC
        - The Kroger Co
        - HOME DEPOT MEXICO
        - Walgreen National Corp
        - Sodimac Sa
        - Sams Club
        - Salcobrand S.A.
        - Harbor Freight Tools
        - Dollar General Corp
        - Wegmans Food Markets Inc
        - NUEVA WAL MART DE MEXICO
        - Costco Wholesale Corp
        - Winn-Dixie Stores Inc
        - CVS Pharmacy Inc
        - Whole Foods Market US
        - Plus Retail Bv
        - The Fragrance Outlet
        - Boston Pizza International Head Office
        - Best Buy Stores Lp
        - Badger Technologies LLC
        - Tractor Supply Co
        - West Marine
        - BJs Wholesale Club Inc
        - Costco Wholesale Canada Ltd.
        - Grupo Upper S.C
        - Safeway Inc
        - The Southern Co-operative Ltd
        - SERVICIOS LIVERPOOL
        - Harris Teeter Llc
        - Asda Stores Limited
        - Poiesz Supermarkten B.V.
        - Party City Corporation
        - COSTCO DE MEXICO
        - Almacenes Exito Sa
        - The Markets Llc
        - Wal-Mart Stores Inc
        - Wal-Mart Canada Corp
        - Sunrise Records & Entertainment Ltd trading as HMV and Fopp
        - Princess Auto Ltd
        - Saks & Company LLC
        - Whole Foods Market Inc CA
        - TravelCenters of America LLC
        - Greggs plc
        - STIME
        - Dunnes Stores
        - ALDI Stores (a limited partnership)
        - Michael Kors (USA), Inc.
        - NORBERT PICEU NV
        - COUDELHO SA
        - Bouwmaat Nederland B.V
        - JD SPORTS FASHION PLC
        - RVL HOOGSTRATEN
        - Torfs
        - TOELPA BVBA
        - Mavilo BV
        - BELLO DOK BVBA
        - SUPERMARKT VAN ONCEN NV
        - ROI DU JAMBON SPRL
        - HHGL Ltd
        - Chemist Warehouse
        - Alex Lee, Inc.
        - BV Nettorama Distributie
        - DWS Fast Food GmbH
        - Popular Book Company Pte Ltd
        - Inditex S.A.
        - SpartanNash Company
        - Asda Stores Ltd
        - Weis Markets Inc
        - Windsor Fashions Inc
        - DISTRIFOLQ G20
        - CASA FRANCE
        - Tommy Hilfiger Usa Inc
        - Singapore Pools (Private) Limited
        - The Fresh Market
        - Abarrotes Economicos S.A
        - CEFFAGE
        - Stew Leonard's Inc.
        - The Works Stores Limited
        - Sligro Food Group Nederland BV
        - Giant Eagle Inc
        - Ahold USA Inc
        - Liquor Control Board Of Ontario
        - Wayfair LLC
        - BIO NATURE OCEAN
        - World Market, LLC
        - Lakeland
        - BARTELS-LANGNESS HANDELSGES. MBH & CO. KG
        - OYSHO MEXICO
        - AGENTUREN DE CLERCQ BV
        - SCHLOSS BURGER GMBH
        - Adm.de Supermercados Express Ltda.
        - British Heart Foundation
        - ZARA MEXICO, S.A. DE C.V.
        - Ross Stores Inc.
        - Anciens Ets G.Schiever Et Fils
        - Kirklands Inc
        - STALSHOP SPRL
        - Brilmij Groep B.V.
        - KFC Corporation
        - Fiesta Foods
        - Michaels Stores Procurement Co Inc
        - KODAK ALARIS MEXICO
        - TIENDAS CHEDRAUI SA DE CV
        - Tiendas Chedraui, Sa De C.V.
        - CASA LEY
        - Key Food
        - Marukai Corp
        - Costco Wholesale UK Limited
        - POSSO LOIRE Sarl
        - GNC Holdings, LLC
        - Hudson News
        - Calvin Klein
        - Systemgastro Sudwest GmbH
        - Dollar Tree Management, LLC
        - Tedox KG
        - EDJ Enterprises, Inc.
        - Wakefern Food Corp
        - Alvoka
        - Fielmann AG
        - Variety Wholesalers Inc.
        - HOVAN BVBA
        - VANGENINDEN BVBA
        - Altairia Distribution
        - ITIM
        - Walmart Chile Sa
        - CHARLES BENS G20
        - Disney Consumer Products and Interactive Media, Inc.
        - DIVELCO SPRL
        - Heinen's Grocery Store
        - Daves Supermarkets
        - Footlocker
        - At Home Stores LLC
        - Spencer Technologies Inc.
        - Corporacion El Rosado S.A.
        - Normal A/S
        - Red Apple Stores Inc
        - Ekono Limitada
        - PriceLess IGA
        - S3A Distribution
        - BARLANG
        - ACADIS
        - Casels Marketplace
        - MOTO HOSPITALITY LTD
        - MPJ MY AUCHAN
        - PULL & BEAR MEXICO
        - JA Procurement LLC
        - SOCIEDAD COMERCIAL TENAUN LTDA.
        - GVDIS SPRL
        - Toshiba Global Commerce Solutions (U.K.) Limited
        - VLS DISTRIBUTION MY AUCHAN
        - SODIPLEIX
        - SOCIETE ALIMENTAIRE MIRABEAU MY AUCHAN
        - SUPERMARCHE SAINT HONORE MY AUCHAN
        - D.A. GAMBETTA
        - Colombiana De Comercio Sa - Alkosto Sa
        - BERKELEY BOWL WEST
        - RS ASTRID 27
        - Quick Chek
        - REDES Y SISTEMAS INTEGRADOS S.A.S.
        - Enterprise Holdings Inc
        - NAEMALYS
        - RS STATION 47 BVBA
        - GRUPO TEXMODA S.A.S
        - Metcalfe Inc
        - CARREFOUR SYSTEMES D INFORMATION
        - TIMES SUPERMARKETS LTD
        - Kmart Australia Ltd
        - ALGEMENE VOEDING VAN TICHELEN NV
        - David Jones Limited
        - MGD NV
        - Pomeroy Technologies, LLC
        - Gordon Food Service Inc
        - Mckay's Market
        - Albert Heijn BV Afdeling Support
        - Eynadis Srl
        - Costa Coffee
        - STCR Business Systems, Inc.
        - Big C Supercenter Public Co,Ltd
        - ETAM SCE SASU CSP ETAM
        - KLASSESLAGER BURMS
        - Costco Wholesale Australia Pty Ltd
        - Toshiba Global Commerce Solutions, Inc.
        - Punto Fa, SL
        - DUHESME DISTRIBUTION G20
        - Key Food Stores Co-operative Inc
        - Intratuin Hulst
        - Good Food Holdings, Inc.
        - ECONOCOM France SAS
        - NCR Nederland BV
        - Husky Oil Marketing Company Div Of Husky Oil Limited
        - METCASH/IGA
        - Toshiba Global Commerce Solutions (France), SAS
        - BK JULLIEN GMBH
        - Pre Unic S.A
        - STRADIVARIUS MEXICO
        - Calvin Klein Inc
        - UA Sports (S.E.A.) Pte Ltd
        - MERCADONA SA
        - Distribuidora Comercial Textil Limitada
        - Newfoundland And Labrador Liquor Corporation
        - Lowes Foods Llc
        - MF SERVICES SRL
        - Westlake Hardware
        - BURGER KING Deutschland GmbH
        - DISTRIBUTION CASINO FRANCE
        - LIBERTY AND TECHNOLOGY
        - Autobahn Tank & Rast GmbH
        - THOMANTO BVBA
        - Etam
        - SUBURBIA
        - MIGA SA
        - Beeline Retail BVBA
        - TIGIDI SA
        - Data Cash Register Company, Inc.
        - WELDOM
        - Diwanze
        - Flower Power Pty Ltd
        - EPICERIES HANKAR MIDI
        - PrismRBS, LLC
        - Harmons Neighborhood Grocer
        - Tommy Hilfiger
        - Kwik Trip
        - Braums Inc
        - Landry's, Inc.
        - Ernsting'S Family Gmbh & Co Kg
        - DOBBIES GARDEN CENTRES PLC
        - MBF 17 BVBA
        - LODES CONSULTORES
        - United Radio Inc
        - Tops Market, LLC
        - VAN LAECKE-VEYS NV
        - BRUGDIS SPRL
        - Auchan Polska Sp.Z O.O.
        - Costcutter Supermarkets Group
        - CHATEAUDIS FRANPRIX
        - BP Brightmore Brands Holdings LLC
        - Amix Tpv
        - MEC Mountain Equipment Company Ltd.
        - TOSHIBA TEC GERMANY
        - Calimax Tiendas
        - COSTCO FRANCE
        - Northern Tool & Equipment Company, Inc
        - HURLEY'S SUPERMARKET
        - Intratuin Pijnacker
        - Punto Fa, S.L
        - Ideal Food Basket
        - Apsoft, Inc
        - DISHUY
        - Nike Inc
        - FRANCE MAGASINS G20
        - HOT TOPIC
        - Hometown Iga
        - Sociedad Comercial O' Higgins Ltda
        - North Country Business Products, Inc.
        - Pricesmart Inc
        - Information Technology International
        - Cash Register Services, Inc.
        - CANADA BREAD COMPANY LTD
        - Globe POS Systems, Inc.
        - Smithsonian Institute
        - ALPHA I MARKETING CORP
        - Dunn-Edwards
        - Dirk Rossmann GmbH
        - Sligro-ISPC Belgium NV
        - DESMA SA
        - Distri Benats NV
        - DELFOOD SA (MONTIGNIES)
        - QUALITY FOOD STORE SPRL
        - BEENHOUWERIJ COCQUYT BVBA
        - VALENTYN-VAN HAUWERMEIREN BVBA
        - Delitraiteur S.A.
        - SARICAL DISTRIBUTION SRL
        - BE Parts
        - AMEDIS SPRL
        - SCHELCK-HUWAERT NV
        - BASTIJN BVBA
        - DESSEIN FILIP NP
        - AB DISTRIBUTION
        - MASSELUS NV
        - ROYAL AUTOMOBILE CLUB OF BELGIUM KARTING SPA-FRANCORCHAMPS
        - MERALAN BVBA
        - MARCAN NV.
        - REFRINAM EXPORT SA
        - ETS SCHNONGS SPRL
        - SUPER TAGADA SA
        - PROXY QUETIN BVBA
        - Grand Opticiens Belgium NV
        - PAUWELS-ASSELMAN BVBA
        - Casa International BV
        - Toshiba Global Commerce Solutions (Netherlands) B.V., Branch Belgique/Bijkantoor België
        - RICO LOGISTICS LTD
        - Toshiba Global Commerce Solutions Mexico, S. de R.L. de C.V.
        - Aptos, Inc.
        - Mark G. Miller, Inc.
        - MICHAEL KORS UK LTD
        - M. Weber GmbH & Co KG
        - Rella Investments Sp. z o.o. - Poland
        - Zensho Holdings
        - Foodland Super Market Ltd
        - SIMA ANTILLES GUYANE
        - BIO VEYRE
        - EHG Service GmbH
        - Tommy Bahama Group, Inc.
        - Gries Deco Company Gmbh
        - VERLINDEN BVBA
        - ACP TEKAEF GmbH
        - BASILIEK NV
        - Bridge SMS Retail Solutions
        - Loc Software
        - KUWAIT PETROLEUM (BELGIUM) NV
        - Academy Sports and Outdoors
        - Retail Sales Solutions
        - University of Vermont
        - TOP LIN BVBA
        - MPV
        - DISTRIBREMONTIER
        - DELIANDA BVBA
        - BINHEXS SRL
        - Longos
        - I.M.A srl
        - BHS Consulting
        - Supermercado Econo Centr
        - SIEL G20
        - Asset Enterprises, Inc.
        - BIZOT DISTRIBUTION
        - New Brunswick Liquor
        - Costco Wholesale New Zealand Limited
        - Köln Kasse
        - SHAYMA 
        
        Here is the data schema. The sr_data_agent_table contains service request data with columns like:
        sr_number : The unique identifier for the service request. REMEMBER THAT IT IS NOT THE PRIMARY KEY AND MULTIPLE ROWS MAY HAVE THE SAME sr_number
        sr_customer_account_number : The customer account number associated with the service request.
        customer_name : The name of the customer associated with the service request.
        task_number : The task number associated with the service request.
        sr_incident_date : The date the service request was created.
        sr_closed_date : The date the service request was closed.
        sr_severity : The severity of the service request.
        sr_machine_type : The type of machine associated with the service request.
        sr_machine_model : The model of the machine associated with the service request.
        sr_machine_serial_number : The serial number of the machine associated with the service request.
        sr_customer_problem_summary : A summary of the customer's problem.
        sr_notes : Additional notes associated with the service request.
        sr_resolution_summary : A summary of the resolution of the service request.
        sr_barrier_code : The barrier code associated with the service request.
        task_notes_external : External notes associated with the task.
        task_assignee : The person assigned to the task.
        task_assignee_id : The ID of the person assigned to the task.
        sr_address_line_4 : The address line 4 associated with the service request.
        sr_address_line_1 : The address line 1 associated with the service request.
        sr_city : The city associated with the service request.
        sr_state : The state associated with the service request.
        sr_postal_code : The postal code associated with the service request.
        task_travel_time_hours (FLOAT) : The travel time in hours associated with the task.
        task_actual_time_hours (FLOAT) : The actual time in hours associated with the task.
        part_quantity (INTEGER): The quantity of parts associated with the service request.
        part_unit_cost (FLOAT): The unit cost of parts associated with the service request.
        part_total_cost(FLOAT) : The total cost of parts associated with the service request.
        part_number : The part number associated with the service request. IMPORTANT: These are the parts numbers that were replaced.
        part_description : The description of the part associated with the service request.
        sr_country : The country associated with the service request.
        comments_text : Comments associated with the service request.
        
        Always use the sql_query_executor tool to run your queries. Never try to access the database directly.
        Explain your reasoning, show the SQL query you're using, and provide a clear answer based on the results.
        Always remember to exclude Null values in the query.
        For instance, if the user asks for the part number for the Motorized Controller, the query should be "SELECT part_number FROM table WHERE description = 'Motorized Controller'".
        
        IMPORTANT:
        If the user asks for the number of sr_numbers then always count the unique number of sr_numbers rather than just the count.
        For example: How many SR tickets did "John Doe" do.
        Then the SQL query should be 
        SELECT COUNT(DISTINCT sr_number) FROM sr_data_agent_table WHERE task_assignee = 'John Doe' AND sr_number IS NOT NULL;
        
        Similarly, when ranking a group by their SR tickets, then also take the distinct sr_numbers into consideration.
        For example: List top 5 customers by SR tickets.
        Then the SQL query should be 
        
        SELECT customer_name, COUNT(DISTINCT sr_number) AS sr_ticket_count
        FROM sr_data_agent_table
        WHERE customer_name IS NOT NULL AND sr_number IS NOT NULL
        GROUP BY customer_name
        ORDER BY sr_ticket_count DESC
        LIMIT 5;
        
        
        OUTPUT FORMAT:
        Always output the answer in markdown format, and table whenever required.
        User: What are the top 3 part numbers for Tractor Supply?
        
        Here are the top 3 part numbers for Tractor Supply, including their descriptions and quantities:
        Part Number	Description	Quantity
        3AC01740900	OEM_APG_TSC-CD-102A_Consigned TSC_Drawer Cable [Field 2 0368-TCC]	3
        3AC02069800	OEM_Aruba_Q9H63A TSC Consigned (SN) - Aruba 515 Indoor Access Point [Field 2 0365-TAQ]	2
        3AC02068100	OEM_ELO_E938113 TSC Consigned (SN) - Elo 22" POS [Field 2 0335-TE9]	2
        
        Note how the agent proactively added the description and quantity columns to the output.

        """
        final_response = ""
        tool_call_data = []
        sources = []

        # Initialize messages with chat history and system prompt
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": "Use the chat history as context and answer this query: " + query + "Remember to exclude null values."})

        while tries < max_tries:
            tries += 1
            try:
                # Call the LLM with the messages
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=[self.functions[0]],
                    temperature=0.1,
                    tool_choice="auto",
                    max_tokens=2000,
                    stream=False
                )

                # Process the response
                message = response.choices[0].message

                if hasattr(message, 'tool_calls') and message.tool_calls:
                    # Handle tool calls
                    for tool_call in message.tool_calls:
                        if tool_call.function.name == "sql_query_executor":
                            import json
                            args = json.loads(tool_call.function.arguments)
                            print(f"Arguments: {args}")
                            sql_query = args.get("query", "")

                            # Execute the SQL query - now with await
                            result = await sql_query_executor(sql_query)
                            tool_call_data.append({
                                "tool": "sql_query_executor",
                                "query": sql_query,
                                "result": result
                            })
                            print(f"Result: {result}")

                            # Add the tool response to messages
                            messages.append({
                                "role": "assistant",
                                "tool_calls": [
                                    {
                                        "id": tool_call.id,
                                        "function": {"name": "sql_query_executor", "arguments": tool_call.function.arguments},
                                        "type": "function"
                                    }
                                ]
                            })
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            })

                    # Get the final response after tool calls
                    final_response_obj = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=messages,
                        temperature=0.1
                    )
                    final_response = final_response_obj.choices[0].message.content
                else:
                    # Direct response without tool calls
                    final_response = message.content

                break  # Exit the retry loop if successful

            except Exception as e:
                if tries >= max_tries:
                    final_response = f"Failed to process your request after {max_tries} attempts. Error: {str(e)}"
                # Continue to retry if not reached max tries

        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        return {
            "response": final_response,
            "execution_time": execution_time,
            "tool_calls": tool_call_data,
            "sources": sources
        }


# Initialize the SQL Agent
sql_agent = SQLAgent(
    name="SQLAgent", #
    agent_id=uuid.uuid4(), #
    system_prompt=toshiba_agent_system_prompt, #
    routing_options={"respond": "Respond to the user"},
    persona="SQL Expert",
    functions=[sql_query_executor.openai_schema],
    short_term_memory=True,
    long_term_memory=False,
    reasoning=True,
    response_type="json",
    max_retries=3,
    timeout=None,
    deployed=False,
    status="active",
    priority=None,
    failure_strategies=["retry"],
    session_id=None,
    last_active=datetime.now(),
    collaboration_mode="single",
)

# Add to agent store
# agent_store = {
#     "SQLAgent": sql_agent.execute,
# }
#
# agent_schemas = {"SQLAgent": sql_agent.openai_schema}

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/query")
async def query_endpoint(query: str):
    try:
        request = QueryRequest(query=query)
        print("Query: ", request.query)
        result = await sql_agent.execute(
            request.query,
            "1", "1", [], "1", "1"
        )

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    # Check if sr_data_agent_table exists and load data if it doesn't
    async def check_and_load_data():
        database_url = os.getenv("SQLALCHEMY_DATABASE_URL")
        if not database_url:
            print("Database URL not configured")
            return

        try:
            engine = create_async_engine(database_url)
            async with engine.connect() as connection:
                # Check if table exists
                result = await connection.execute(text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sr_data_agent_table')"
                ))
                table_exists = result.scalar()

                if not table_exists:
                    print("Table sr_data_agent_table does not exist. Loading data...")
                    excel_file = 'sr_data_excel_table.xlsx'
                    from load_data_table import load_excel_to_postgres
                    await load_excel_to_postgres(excel_file)
                else:
                    print("Table sr_data_agent_table already exists")
        except Exception as e:
            print(f"Error checking table existence: {str(e)}")

    # Run the check and load function
    asyncio.run(check_and_load_data())

    # Start the API server
    uvicorn.run(app, host="0.0.0.0", port=8044)