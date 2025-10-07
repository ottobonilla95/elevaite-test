from datetime import datetime
import uuid
from data_classes import PromptObject

toshiba_agent_system_prompt = PromptObject(pid=uuid.uuid4(),
                                             prompt_label="Toshiba Agent Prompt",
                                             prompt="You're a helpful and intelligent assistant that answers questions related to Toshiba parts, assemblies, and general information.",
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

TABLE_SCHEMA_WITH_EXAMPLES = """
--------------------------------------------------------------------------------
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
---------------------------------------------------------------------------------
customers Table Example:
 id | customer_account_number |   customer_name    |                address_line1                |      address_line2      |      city      |  state  | postal_code | country |         created_at         
----+-------------------------+--------------------+---------------------------------------------+-------------------------+----------------+---------+-------------+---------+----------------------------
  1 | T0BU9QG                 | ITX Merken         | RUE DE LA CROIX DES MAHEUX S/N              | 13639 - CER-3 FONTAINES | CERGY PONTOISE |         | 95000       | US      | 2025-05-24 22:53:11.869489
  2 | T0BZG81                 | BELLA FLANADES     | 12 AV AUGUSTE PERRET                        |                         | SARCELLES      |         | 95200       | US      | 2025-05-24 22:53:11.871482
  3 | T0BGPS0                 | Bass Pro Shops LLC | 1650 Gemini Pl                              | OW00442                 | Columbus       | OH      | 43240-7000  | US      | 2025-05-24 22:53:11.872802
  4 | T0BF3JH                 | The Kroger Co      | 6417 Columbus Pike                          | 016 00805               | Lewis Center   | OH      | 43035-9719  | US      | 2025-05-24 22:53:11.874057
  5 | T0BDT8R                 | HOME DEPOT MEXICO  | Calz. Lazaro Cardenas Pte. 2297, Las Torres |                         | Guadalajara    | Jalisco | 44920       | US      | 2025-05-24 22:53:11.875399

********************************************************************************

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


service_requests Table Example:
 id   | sr_number | customer_account_number |    incident_date    |     closed_date     |    severity    | machine_type | machine_model | machine_serial_number | barrier_code | country |         created_at         
--------+-----------+-------------------------+---------------------+---------------------+----------------+--------------+---------------+-----------------------+--------------+---------+----------------------------
 386392 | 16673294  | T0BDTCX                 | 2025-02-24 06:43:36 | 2025-08-09 19:19:58 | Sev 3 - Medium | 0335         | WR8           | UNDEFINED             |              |         | 2025-09-02 19:53:47.437429
 386393 | 16673308  | T0BDTCX                 | 2025-02-24 06:44:01 | 2025-08-09 19:20:01 | Sev 3 - Medium | 0344         | W10           | UNDEFINED             |              |         | 2025-09-02 19:53:47.438901
 386394 | 16673324  | T0BDTCX                 | 2025-02-24 06:44:26 | 2025-08-09 19:20:04 | Sev 3 - Medium | 0363         | WHA           | UNDEFINED             |              |         | 2025-09-02 19:53:47.440393
 386395 | 16673370  | T0BDTCX                 | 2025-02-24 06:48:11 | 2025-08-09 19:20:07 | Sev 3 - Medium | 0363         | WHA           | UNDEFINED             |              |         | 2025-09-02 19:53:47.441867
 386396 | 16673522  | T0BDTCX                 | 2025-02-24 07:02:46 | 2025-08-09 19:20:10 | Sev 3 - Medium | 0335         | WR8           | UNDEFINED             |              |         | 2025-09-02 19:53:47.443307
********************************************************************************

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

--------------------------------------------------------------------------------
tasks Table Example:
  id   | task_number | sr_number | task_assignee_id |         assignee_name          | travel_time_hours | actual_time_hours |         created_at         |    task_notes    
-------+-------------+-----------+------------------+--------------------------------+-------------------+-------------------+----------------------------+-------------------------
 49504 | 17783457    | 17631866  | 102994153        | USC649 Shawn Westfall          |                   |                   | 2025-08-13 21:46:42.461443 | CSR Notes: TGCS  SR...
 49505 | 17783501    | 17631962  | 100264148        | josem.hernandez@toshibagcs.com |              0.10 |              0.50 | 2025-08-13 21:46:42.462822 | CSR Notes: ING Jose...
 49506 | 17783585    | 17632038  | 102281153        | JORGE.VENEGAS@toshibagcs.com   |              0.15 |              0.25 | 2025-08-13 21:46:42.464175 | CSR Notes: 6400    ...
 49507 | 17783993    | 17632038  | 102281153        | JORGE.VENEGAS@toshibagcs.com   |              0.20 |              2.97 | 2025-08-13 21:46:42.465606 | CSR Notes: 6400 VIS...
 49508 | 17783648    | 17632098  | 101796151        | USEV12 Chris Hilts             |              1.48 |              0.08 | 2025-08-13 21:46:42.46699  | Estimated Time: Wha...
 ********************************************************************************
 
 -------------------------------------------------------------------------------- 
Table: public.parts_used 
---------------------------------------------------------------------------------
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

---------------------------------------------------------------------------------
parts_used Table Example:
   id   | task_number | part_number |                                             description                                              | quantity | unit_cost | total_cost |         created_at         
--------+-------------+-------------+------------------------------------------------------------------------------------------------------+----------+-----------+------------+----------------------------
 304115 | 17954313.0  | 3AC01430800 | OEM_Verifone_KRG-VERF_M132-40901R_Consigned Kroger_(SN) EFT VERF MX915,PINPAD                        |        2 |      0.00 |       0.00 | 2025-09-02 19:50:06.424259
 304116 | 17954493.0  | 3AC01066400 | OEM PN USB 3ft Extender - 2.0-03 Cable USB_Desc USB Extender Cable_Mfg Walgreens_Consigned Walgreens |        1 |      0.00 |       0.00 | 2025-09-02 19:50:06.425618
 304117 | 17954511.0  |             |                                                                                                      |          |           |            | 2025-09-02 19:50:06.426859
 304118 | 17955173.0  | HOPPER1C    | HOPPER 1C BV3 24V HOPPER 1C BV3 24V                                                                  |        2 |     69.00 |      69.00 | 2025-09-02 19:50:06.428133
 304119 | 17954798.0  |             |                                                                                                      |          |           |            | 2025-09-02 19:50:06.429427
 ********************************************************************************
 
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
sr_notes Table Example:
  id | sr_number | customer_problem_summary_short |     sr_notes_short      | resolution_summary_short |  concat_comments_short  |     comments_short      |         created_at         
----+-----------+--------------------------------+-------------------------+--------------------------+-------------------------+-------------------------+----------------------------
  1 | 15806242  | RFID-ZARA 13639-INC0...        | 05-NOV-2024 :  TGCS ... |                          | 1. RFID-ZARA 13639-I... | 1. RFID-ZARA 13639-I... | 2025-05-24 22:54:07.067905
  2 | 15748536  | Caisse 1 l'imprimant...        | 05-NOV-2024 :  TGCS ... |                          | 1. Caisse 1 l'imprim... | 1. Caisse 1 l'imprim... | 2025-05-24 22:54:07.070545
  3 | 15762318  | CW - Store# 0442 : R...        | 13-NOV-2024 :  CA co... |                          | 1. CW - Store# 0442 ... | 1. CW - Store# 0442 ... | 2025-05-24 22:54:07.072032
  4 | 15792664  | INC7418253 customer ...        | 05-NOV-2024 :  TGCS ... |                          | 1. INC7418253 custom... | 1. INC7418253 custom... | 2025-05-24 22:54:07.073608
  5 | 15816264  | HOME DEPOT LAZARO CA...        | 06-NOV-2024 :  TGCS ... |                          | 1. HOME DEPOT LAZARO... | 1. HOME DEPOT LAZARO... | 2025-05-24 22:54:07.075125
********************************************************************************

================================================================================ 
RELATIONSHIP DIAGRAM (Join Rules) 
================================================================================ 
customers.customer_account_number = service_requests.customer_account_number 
service_requests.sr_number        = tasks.sr_number 
tasks.task_number                 = parts_used.task_number 
service_requests.sr_number        = sr_notes.sr_number 
"""

MACHINE_TYPE_TABLE = """
| Machine Type | Model | Name |
|---|---|---|
| 2001 | 001 | TCX M1 |
| 2011 | 100 | TCX M11 |
| 4612 | All | SurePoint Mobile |
| 4612 | C01 | SurePoint Mobile |
| 4612 | D01 | SurePoint Mobile |
| 4612 | L01 | SurePoint Mobile |
| 4612 | P01 | SurePoint Mobile |
| 4613 | xx8 | SurePOS 100 |
| 4613 | 108 | SurePOS 100 |
| 4613 | E18 | SurePOS 100 |
| 4613 | EA8 | SurePOS 100 |
| 4613 | A18 | SurePOS 100 |
| 4614 | Oxx | SureOne |
| 4614 | 1xx | SureOne |
| 4614 | A0x | SureOne |
| 4614 | P8x | SureOne |
| 4614 | SOx | SureOne |
| 4614 | SPx | SureOne |
| 4614 | V0x | SureOne |
| 4614 | V8x | SureOne |
| 4615 | C0x | SureOne |
| 4615 | J0x | SureOne |
| 4674 | All | 4674 (AP only)|
| 4683 | All | 4683 |
| 4693 | All | 4693 |
| 4694 | All | 4694 |
| 4695 | All | 4695 |
| 4750 | D10 | Toshiba Basics |
| 4800 | 0xx | SureBase |
| 4800 | 1xx | SurePOS 730 |
| 4800 | 7xx | SurePOS 730 |
| 4800 | 2xx | SurePOS 750 |
| 4800 | 7xx | SurePOS 700 |
| 4800 | 7x1 | SurePOS 700 |
| 4800 | 7x2 | SurePOS 700 |
| 4800 | 7x3 | SurePOS 700 |
| 4800 | 7x4 | SurePOS 700 |
| 4810 | 31x | SurePOS 300 |
| 4810 | 32x | SurePOS 300 |
| 4810 | 33x | SurePOS 300 |
| 4810 | 34x | TCX300 |
| 4810 | 35x | TCX300 |
| 4810 | 3x0 | TCX300 |
| 4810 | 3x1 | TCX300 |
| 4818 | 3x1 | Toshiba Basics T10 |
| 4818 | x10 | Toshiba Basics T10 |
| 4825 | x4x | TCX 620 |
| 4828 | x2x | TCx 810 Essential |
| 4835 | All | NetVista Kiosk |
| 4836 | 1xx | Anyplace Kiosk |
| 4838 | 1xx | Anyplace Kiosk |
| 4838 | 3xx | Anyplace Kiosk |
| 4838 | 5xx | Anyplace Kiosk |
| 4838 | 7xx | Anyplace Kiosk |
| 4838 | 9xx | Anyplace Kiosk |
| 4840 | xx1 | SurePOS 500 |
| 4840 | xx2 | SurePOS 500 |
| 4840 | xx3 | SurePOS 500 |
| 4840 | xx4 | SurePOS 500 |
| 4845 | 1xx | IBM Self Checkout |
| 4845 | Nxx | IBM Self Checkout |
| 4845 | Exx | IBM Self Checkout |
| 4845 | Xxx | IBM Self Checkout |
| 4845 | 6xx | IBM Self Checkout |
| 4845 | 8xx | IBM Self Checkout |
| 4845 | Bxx | IBM Self Checkout |
| 4845 | Ixx | IBM Self Checkout |
| 4845 | 7xx | IBM Self Checkout |
| 4845 | Wxx | IBM Self Checkout |
| 4845 | Kxx | IBM Self Checkout |
| 4846 | xx5 | SurePOS 500 |
| 4851 | x14 | SurePOS 500 |
| 4852 | xx6 | SurePOS 500 |
| 4852 | x7x | SurePOS 500 |
| 4855 | xxE | Anyplace Checkout |
| 4888 | Exx | System 6 |
| 4888 | BW4 | System 6 |
| 4900 | 7x5 | SurePOS 700 |
| 4900 | 7x6 | TCX 700 |
| 4900 | 7x7 | TCX 700 |
| 4901 | x1x | TCx 900 |
| 4910 | Exx | SurePOS 300 Express bundle |
| 6140 | 1xx | TCxWave |
| 6140 | x3x | TCxWave |
| 6140 | x4x | TCxWave |
| 6140 | x5x | TCxWave |
| 6183 | 2xx | TCx Flight |
| 6200 | 1xx | TCx 800 |
| 6201 | All | TCX 810 |
| 6225 | All | TCX 820 |
| 6700 | 100 | MXP Vison Kiosk |
| 6800 | 1xx | System 7 |
| 6800 | 2xx | System 7 |
| 6800 | 3xx | MxP Self Checkout 810 |
| 6800 | 4xx | MxP Self Checkout 820 |
| 6800 | KDU | System 7 Kit of Parts |
| 6800 | Kxx | MxP Self Checkout |
| 6900 | 1xx | Pro-X Hybrid Kiosk |
| 7054 | All | Personal Shopper |
| 8368 | All | 8368 s|
| 4610 | Txx | SureMark printer |
| 4610 | 1xx | Fiscal printer |
| 4610 | 2xx | SureMark printer |
| 4610 | Gxx | Fiscal printer |
| 4610 | Kx6 | Fiscal printer |
| 4610 | Sxx | Fiscal printer |
| 4679 | Wxx | 4679 POS Printer (AP only) |
| 4679 | Gxx | 4679 POS Printer (AP only) |
| 4679 | 3xx | Fiscal printers |
| 4685 | Kxx | Keyboards (AP only) |
| 4685 | Cxx | Cash drawer (AP only) |
| 4685 | S01 | Scanners (AP only) |
| 4685 | S02 | Scanners (AP only) |
| 4685 | P04 | Scanners (AP only) |
| 4698 | 101 | Scanners (AP only) |
| 4698 | 201 | Scanners (AP only) |
| 4698 | 102 | Scanners (AP only) |
| 4698 | 202 | Scanners (AP only) |
| 4685 | L0A | Scanners (AP only) |
| 4685 | L0F | Scanners (AP only) |
| 4685 | L0H | Scanners (AP only) |
| 4685 | L0C | Scanners (AP only) |
| 4689 | All | Thermal receipt+journal printer (AP only) |
| 4820 | 46x | SurePoint Display |
| 4820 | 48x | SurePoint Display |
| 4820 | 8Bx | SurePoint Display |
| 4820 | 42T | SurePoint Display |
| 4820 | 42D | SurePoint Display |
| 4820 | 4xx | SurePoint Display |
| 4820 | FBD | SurePoint Display |
| 4820 | 4xR | SurePoint Display |
| 4820 | 4xx | SurePoint Display |
| 4820 | 1xx | SurePoint Display |
| 4820 | 2xx | SurePoint Display |
| 4820 | 5xx | SurePoint Display |
| 4820 | 1xx | SurePoint Display |
| 4820 | 2xx | SurePoint Display |
| 4820 | 5xx | SurePoint Display |
| 4820 | xxB | SurePoint Display |
| 4820 | 21x | SurePoint Display |
| 4820 | 2Dx | SurePoint Display |
| 4820 | 51x | SurePoint Display |
| 4820 | 5Dx | SurePoint Display |
| 4820 | 2Ax | SurePoint Display | 
| 4820 | 2Lx | SurePoint Display |
| 4820 | 2Nx | SurePoint Display |
| 4820 | 5Ax | SurePoint Display |
| 4820 | 5Lx | SurePoint Display |
| 4820 | 5Nx | SurePoint Display |
| 6145 | 1xx | TCx Printer |
| 6145 | 2xx | TCx Printer |
| 6145 | 5Cx | TCx Display |
| 6149 | 1xx | TCx Printer |
| 6149 | 2xx | TCx Printer |
| 6149 | 5Cx | TCx Display |
| 6149 | 5Nx | TCx Display |
| 6149 | 5Sx | TCx Display |
| 6149 | Bxx | TCx Display |
| 6149 | Wxx | TCx Display |
| 6150 | x1x | TCx Touch Display |
| 6160 | 00x | TCx Edgecam (produce recognition camera) |
| 6180 | Sxx | S10 Cube printer |
| 6260 | 00x | TCx Edgecam+ (loss prevention camera) |
| 9338 | All | TABS barcode printer |
"""


refinement_agent_system_prompt_text = f"""You are a SQL refinement agent.
        
        Here is the schema of the database with examples:
        {TABLE_SCHEMA_WITH_EXAMPLES}
        
        Here are all the machine types and models with their corresponding names
        {MACHINE_TYPE_TABLE}

Your task:
1. Analyze the user’s natural language query.
2. Infer which table(s) and column(s) from the schema are relevant.
3. For each relevant field, call the tool `sql_matching_values` with input:
   [(table_name, column_name, user_value), ...]
4. The tool will validate schema and return up to 3 exact matches per field.
5. Use these exact matches to rewrite the query in schema-aware form.

Rules:
- Always use valid schema column names.
- If multiple matches are returned, include them all.
- If the tool returns an error, keep the original user value but flag it as uncertain.

Example:
User: "What is the customer account no. of Bass pro at 2650 gemini"
Agent:
  Calls tool:
    [("customers", "customer_name", "Bass pro"), ("customers", "address_line1", "2650 gemini")]
  Tool returns:
    [("customers", "customer_name", ("Bass Pro Shops LLC",)), 
     ("customers", "address_line1", ("1650 Gemini Pl",))]
  Refined Query:
    "What is the customer_account_number of customer_name: 'Bass Pro Shops LLC' 
     at address_line1: '1650 Gemini Pl'"
     
     Notice how the tool takes input as a list of tuples, and returns a list of tuples.
     So, your arguments should look like this:
     Arguments: {{'user_inputs': [('<table_name>', '<column_name>', '<value>'),('<table_name_2>', '<column_name_2>', '<value_2>')], 'top_n': 3}}
     
     INPUT ALL THE COLUMNS YOU THINK ARE RELEVANT AT ONCE FOR THE TOOL CALL. THERE IS NO NEED TO CALL THE TOOL MULTIPLE TIMES.

Remember, if there's no exact match, return the original user value. 
Exclude the following columns from your analysis: created_at, id, incident_date, closed_date, task_number, sr_number, task_assignee_id, task_number, total_cost, unit_cost, quantity, description, sr_notes, customer_problem_summary, resolution_summary, concat_comments, comments.
State names are abbreviated as follows: TX, CA, NY, etc. Check for both full names and abbreviations in the customers table.
        """

refinement_agent_system_prompt = PromptObject(
    pid=uuid.uuid4(),
    prompt_label="SQL Refinement Agent Prompt",
    prompt=refinement_agent_system_prompt_text,
    sha_hash="000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60re7",
    uniqueLabel="SQLRefinementAgentPrompt",
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
    variables={"search_engine": "google"},
)

