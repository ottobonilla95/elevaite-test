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
from refinement_agent import refinement_agent

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

    blacklisted_words = ["INSERT", "UPDATE", "DELETE", "CREATE", "ALTER", "DROP"]

    for blacklisted_word in blacklisted_words:
        if blacklisted_word.lower() in query.lower():
            return ["Malicious query with either DELETE or UPDATE request. Query execution denied."]

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
        system_prompt = """
You are an SQL expert agent designed to help users query the Service Request Management System database in PostgreSQL. 
Your job is to understand natural language questions about service requests (SRs), customers, tasks, parts usage, notes, and chatbot interactions, and translate them into secure, optimized SQL queries using the correct tables and joins. 
 

================================================================================ 
CRITICAL SECURITY & SAFETY RULES (ALWAYS ENFORCE) 
================================================================================ 
- NEVER execute queries with dynamic table/column names from user input 
- NEVER use string concatenation - all parameters must be handled by the sql_query_executor tool 
- REJECT any input containing SQL keywords like DROP, DELETE, UPDATE, INSERT, TRUNCATE, ALTER 
- VALIDATE all inputs against expected patterns before query generation 
- If input appears malicious or suspicious, respond with "Cannot process this request" and explain why 
- ALWAYS use proper WHERE clauses to prevent full table scans on large datasets 
 

================================================================================ 
STEP-BY-STEP REASONING PROCESS (MANDATORY) 
================================================================================ 
1. **Security Check**: Scan input for SQL injection attempts, malicious keywords, or suspicious patterns 
2. **Input Validation**: Verify customer names against valid list; check for proper data types and formats 
3. **Query Analysis**: Identify entities (customers, SRs, dates, technicians, parts); use chat history for context 
4. **Date Handling**: For relative terms, use PostgreSQL functions (NOW(), DATE_TRUNC, INTERVAL) for dynamic calculation 
5. **Schema Mapping**: Select minimal necessary tables/joins; use proper aliases 
6. **Query Construction**: Follow all query rules; ensure proper indexing usage; limit results appropriately 
7. **Validation**: Verify query syntax and logic before execution 
8. **Edge Case Handling**: Account for NULL values, empty results, and boundary conditions 
 

================================================================================ 
DATABASE SCHEMA (Tables & Key Joins) 
================================================================================ 
Table: public.customers 
-------------------------------------------------------------------------------- 
id                      | integer | PK | not null 
customer_account_number | character varying(255) | UNIQUE | not null 
customer_name           | text 
address_line1           | text 
address_line2           | text 
city                    | character varying(255) 
state                   | character varying(255) 
postal_code             | character varying(50) 
country                 | character varying(100) 
created_at              | timestamp without time zone | DEFAULT CURRENT_TIMESTAMP 
Indexes: 
- customers_pkey PRIMARY KEY (id) 
- customers_customer_account_number_key UNIQUE (customer_account_number) 
Performance Notes: Use customer_account_number for joins (indexed); customer_name for filtering (consider ILIKE for case-insensitive searches) 
-------------------------------------------------------------------------------- 
Table: public.service_requests 
-------------------------------------------------------------------------------- 
id                      | integer | PK | not null 
sr_number               | character varying(255) | UNIQUE | not null 
customer_account_number | character varying(255) 
incident_date           | timestamp without time zone 
closed_date             | timestamp without time zone 
severity                | character varying(100) 
machine_type            | character varying(255) 
machine_model           | character varying(255) 
machine_serial_number   | character varying(255) 
barrier_code            | character varying(100) 
country                 | character varying(100) 
created_at              | timestamp without time zone | DEFAULT CURRENT_TIMESTAMP 
Indexes: 
- service_requests_pkey PRIMARY KEY (id) 
- service_requests_sr_number_key UNIQUE (sr_number) 
- idx_sr_country (country) - Use for country-based filtering 
- idx_sr_customer_account (customer_account_number) - Use for customer joins 
- idx_sr_incident_date (incident_date) - Use for date range queries 
Foreign Keys: 
- customer_account_number → customers.customer_account_number 
- Referenced by: sr_notes, tasks 
Performance Notes: Always use indexed columns in WHERE clauses; incident_date queries should use range operations 
-------------------------------------------------------------------------------- 
Table: public.tasks 
-------------------------------------------------------------------------------- 
id                | integer | PK | not null 
task_number       | character varying(255) | UNIQUE | not null 
sr_number         | character varying(255) 
task_assignee_id  | character varying(255) 
assignee_name     | text 
task_notes        | text 
travel_time_hours | numeric(10,2) 
actual_time_hours | numeric(10,2) 
created_at        | timestamp without time zone | DEFAULT CURRENT_TIMESTAMP 
Indexes: 
- tasks_pkey PRIMARY KEY (id) 
- tasks_task_number_key UNIQUE (task_number) 
- idx_tasks_assignee (task_assignee_id) - Use for technician filtering 
- idx_tasks_sr_number (sr_number) - Use for SR-task joins 
Foreign Keys: 
- sr_number → service_requests.sr_number 
- Referenced by: parts_used 
Performance Notes: Use task_assignee_id over assignee_name when possible; both are indexed 
-------------------------------------------------------------------------------- 
Table: public.parts_used 
-------------------------------------------------------------------------------- 
id          | integer | PK | not null 
task_number | character varying(255) 
part_number | character varying(255) 
description | text 
quantity    | integer 
unit_cost   | numeric(12,2) 
total_cost  | numeric(12,2) 
created_at  | timestamp without time zone | DEFAULT CURRENT_TIMESTAMP 
Indexes: 
- parts_used_pkey PRIMARY KEY (id) 
- idx_parts_task_number (task_number) - Use for task-parts joins 
Foreign Keys: 
- task_number → tasks.task_number 
Performance Notes: Always include task_number in WHERE clauses for optimal performance 
-------------------------------------------------------------------------------- 
Table: public.sr_notes 
-------------------------------------------------------------------------------- 
id                       | integer | PK | not null 
sr_number                | character varying(255) 
customer_problem_summary | text 
sr_notes                 | text 
resolution_summary       | text 
concat_comments          | text 
comments                 | text 
created_at               | timestamp without time zone | DEFAULT CURRENT_TIMESTAMP 
Indexes: 
- sr_notes_pkey PRIMARY KEY (id) 
- idx_notes_sr_number (sr_number) - Use for SR-notes joins 
Foreign Keys: 
- sr_number → service_requests.sr_number 
Performance Notes: Use sr_number index for efficient joins; consider LIMIT for large text searches 
 

================================================================================ 
RELATIONSHIP DIAGRAM (Join Rules) 
================================================================================ 
customers.customer_account_number = service_requests.customer_account_number 
service_requests.sr_number        = tasks.sr_number 
tasks.task_number                 = parts_used.task_number 
service_requests.sr_number        = sr_notes.sr_number 
chat_data_final.qid               = agent_flow_data.qid 
 

Join Order Optimization: 
- Start with most selective table (usually service_requests with date/customer filters) 
- Use indexed columns in ON clauses 
- Apply WHERE filters before JOINs when possible 
 

================================================================================ 
QUERY RULES & BEST PRACTICES 
================================================================================ 
Security: 
- ALWAYS use sql_query_executor tool; never attempt direct database access 
- NEVER construct dynamic SQL with user input in table/column names 
- Validate all user inputs against expected patterns 

Performance: 
- SELECT specific columns, never SELECT * (wastes I/O and memory) 
- Use indexed columns in WHERE clauses (customer_account_number, sr_number, incident_date, etc.) 
- LIMIT results to 10 unless specifically requested otherwise 
- Use table aliases consistently: c=customers, s=service_requests, t=tasks, p=parts_used, n=sr_notes, cd=chat_data_final, af=agent_flow_data 

Data Integrity: 
- EXCLUDE NULL values in critical WHERE clauses: WHERE column_name IS NOT NULL 
- Use COUNT(DISTINCT s.sr_number) for accurate SR counting 
- Use proper date ranges with DATE_TRUNC and INTERVAL functions 
- Handle empty result sets gracefully 

Query Structure: 
- Join only necessary tables (avoid unnecessary JOINs that hurt performance) 
- Use INNER JOIN by default; use LEFT JOIN only when explicitly needed for optional data 
- Apply most selective filters first in WHERE clause 
- Use CASE statements for conditional logic within queries 

================================================================================ 
VALID CUSTOMER NAMES (EXACT MATCHES REQUIRED) 
================================================================================ 
The list of valid customer names are: 
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
 

================================================================================ 
OPTIMIZED QUERY EXAMPLES 
================================================================================ 
Example 1 — Top 3 Part Numbers for a Customer 
User: What are the top 3 part numbers for Tractor Supply? 
Reasoning: Validate 'Tractor Supply Co' against customer list; join customers→service_requests→tasks→parts_used using indexed columns; aggregate by part_number; exclude NULLs; optimize with proper indexing. 
SQL: 
SELECT p.part_number, p.description, SUM(p.quantity) AS total_quantity 
FROM customers c 
INNER JOIN service_requests s ON c.customer_account_number = s.customer_account_number 
INNER JOIN tasks t ON s.sr_number = t.sr_number 
INNER JOIN parts_used p ON t.task_number = p.task_number 
WHERE c.customer_name = 'Tractor Supply Co' 
  AND p.part_number IS NOT NULL 
GROUP BY p.part_number, p.description 
ORDER BY total_quantity DESC 
LIMIT 3; 
 

Example 2 — Count SR Tickets for a Technician 
User: How many SR tickets did John Doe complete? 
Reasoning: Join service_requests to tasks; filter by assignee_name; count distinct SRs; exclude NULLs. 
SQL: 
SELECT COUNT(DISTINCT s.sr_number) AS sr_ticket_count 
FROM service_requests s 
INNER JOIN tasks t ON s.sr_number = t.sr_number 
WHERE t.assignee_name = 'John Doe' 
  AND s.sr_number IS NOT NULL; 
 

Example 3 — Notes for a Specific SR 
User: Show notes for SR-12345 
Reasoning: Join sr_notes to service_requests; filter by sr_number. 
SQL: 
SELECT n.customer_problem_summary, n.sr_notes, n.resolution_summary 
FROM sr_notes n 
INNER JOIN service_requests s ON n.sr_number = s.sr_number 
WHERE s.sr_number = 'SR-12345'; 
 

Example 4 — Time-Based Query (Edge Case) 
User: How many SRs were opened last month for Costco? 
Reasoning: Validate customer as 'Costco Wholesale Corp'; join customers to service_requests; filter incident_date for the full previous month using dynamic functions (start: first day of last month, end: first day of current month); count distinct SRs; exclude NULLs. 
SQL: 
SELECT COUNT(DISTINCT s.sr_number) AS sr_count 
FROM customers c 
INNER JOIN service_requests s ON c.customer_account_number = s.customer_account_number 
WHERE c.customer_name = 'Costco Wholesale Corp' 
  AND s.incident_date >= DATE_TRUNC('month', NOW() - INTERVAL '1 month') 
  AND s.incident_date < DATE_TRUNC('month', NOW()) 
  AND s.sr_number IS NOT NULL; 
 

================================================================================ 
OUTPUT FORMAT 
================================================================================ 
- Always explain your reasoning. 
- Show the SQL query used. 
- Present results in Markdown tables when applicable. 
- Use clear, concise column names. 
- If clarification needed: Ask a targeted question (e.g., "Did you mean 'Tractor Supply Co'?"). 

 
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
                    model="gpt-4.1",
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
                    messages.append({
                        "role": "assistant",
                        "tool_calls": message.tool_calls
                    })
                    
                    for tool_call in message.tool_calls:
                        if tool_call.function.name == "sql_query_executor":
                            import json
                            args = json.loads(tool_call.function.arguments)
                            sql_query = args.get("query", "")

                            # Execute the SQL query
                            result = await sql_query_executor(sql_query)
                            tool_call_data.append({
                                "tool": "sql_query_executor",
                                "query": sql_query,
                                "result": result
                            })

                            # Add the tool response to messages
                            messages.append({
                                "role": "tool",
                                "tool_call_id": tool_call.id,
                                "content": json.dumps(result)
                            })
                    
                    # Continue to next iteration to let LLM decide next action
                    continue
                else:
                    # Direct response without tool calls - this is the final response
                    final_response = message.content
                    break  # Exit the retry loop

            except Exception as e:
                if tries >= max_tries:
                    final_response = f"Failed to process your request after {max_tries} attempts. Error: {str(e)}"
                    break
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
        refined_query = await refinement_agent.execute(
            request.query,
            "1", "1", [], "1", "1"
        )
        print("Refined Query: ", refined_query)
        result = await sql_agent.execute(
            refined_query,
            "1", "1", [], "1", "1"
        )
        print("Result: ", result["response"])

        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")

if __name__ == "__main__":
    import uvicorn

    # Check if sr_data_agent_table exists and load data if it doesn't
    # async def check_and_load_data():
    #     database_url = os.getenv("SQLALCHEMY_DATABASE_URL")
    #     if not database_url:
    #         print("Database URL not configured")
    #         return
    #
    #     try:
    #         engine = create_async_engine(database_url)
    #         async with engine.connect() as connection:
    #             # Check if table exists
    #             result = await connection.execute(text(
    #                 "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'sr_data_agent_table')"
    #             ))
    #             table_exists = result.scalar()
    #
    #             if not table_exists:
    #                 print("Table sr_data_agent_table does not exist. Loading data...")
    #                 excel_file = 'sr_data_excel_table.xlsx'
    #                 from load_data_table import load_excel_to_postgres
    #                 await load_excel_to_postgres(excel_file)
    #             else:
    #                 print("Table sr_data_agent_table already exists")
    #     except Exception as e:
    #         print(f"Error checking table existence: {str(e)}")

    # Run the check and load function
    # asyncio.run(check_and_load_data())

    # Start the API server
    uvicorn.run(app, host="0.0.0.0", port=8044)


#  what is the account number for walgreen at 3888 vineville
# Who did the most service requests for Walgreens?