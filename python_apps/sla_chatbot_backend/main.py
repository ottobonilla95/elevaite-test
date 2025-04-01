from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
import uvicorn
import requests
import base64
from fastapi.middleware.cors import CORSMiddleware
from models import EventPayload, InferencePayload
from typing import List
from openai import OpenAI
from openai import AzureOpenAI
import json
import openai
import argparse
import re
from fuzzywuzzy import process

prompt = """The months you have data on are February, March, April.
You are an analyst who helps customers understand whether there is a breach of SLOs or not.
Your goal is to answer users' questions politely. Only use the information given below.
If you cannot find the information, decline politely.
Give specific answers.
There are three categories of SLOs: Availability, Risk and Compliance, and Service Operations.
- category: Availability, Risk and Compliance, or Service Operations
- breach_detected: Yes means a breach happened, No means that no breach
- service_target
- actual_service_level
- service_level_date
- service_credit: Also known as slo_breach_penalty
- earnback: The credit paid to the vendor
- data_source
- comment: Which can contain more details like (but not limited to) exception or overruling for the chargeback
- equation: The equation used to compute the service_credit. It can also be called a financial model.
If a user asks about how the service credit was calculated or "How was service credit calculated?", use the equation information for that specific category and month.
If user provides month but not the year, assume 2024.
If they do not specify month, ask the user about which month they are interested in first.
There is a breach if and only if breach_detected is set to Yes for a given date; then this is considered an SLO breach, and service_credit should be paid.
If a breach is detected, mention the service target and the actual service level, service credit and the comment associated with that specific category and month.
If no breach is detected, mention the service target and the actual service level, and the comment.
If the user asks about a breach and there are multiple breaches, do not answer the question directly and ask the user first about which category or month they are interested in based on what they provided.
If the user asks about a specific field, e.g., earnback or service_credit, and there are multiple records, then list the different values for different records.
Use the information in the comment that can contain exceptions (also known as overruling) on whether there is a service credit or not.
If a user asks about service credit for a month, make sure to add the service credit for all the categories: Availability, Risk & Compliance, and Service Operations. Do not forget a category!
If the user asks about the reason for earnback, then tell the user that this is because there have been no breaches since the last penalty for that category specifically was applied. 
If the information is not available, respond with "I don't have that information.
Format the output in HTML Table or HTML Bulletted List format when appropriate.
Use these css classes .custom-table  and .custom-list. Put your entire output in a .sla_section class.
"""
OpenAI.api_type = "azure"
OpenAI.api_version = "2023-08-01-preview"

event_payload = {}
llm_api_key = ""
cisco_app_key = ""
cisco_client_id = ""
cisco_client_secret = ""
filtered_data = [] # Global variable to maintain the state of filtered data

@asynccontextmanager
async def lifespan(app: FastAPI):
    global event_payload
    global llm_api_key
    global cisco_app_key
    global cisco_client_id
    global cisco_client_secret
    with open('event_payload.json') as f:
        event_payload = json.load(f)
    with open("api_keys.json") as f:
        payload = json.load(f)
        llm_api_key = payload["llm_api_key"]
        cisco_app_key = payload["cisco_app_key"]
        cisco_client_id = payload["cisco_client_ID"]
        cisco_client_secret = payload["cisco_client_secret"]
    yield

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Hello World"}

def correct_month_spelling(month):
    valid_months = [
        'january','feb','mar','apr', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
        'september', 'october', 'november', 'december'
    ]
    corrected_month, score = process.extractOne(month, valid_months)
    return corrected_month if score > 90 else None

def retrieve_relevant_data(query, current_data):

    
    # extract the month and year from the query using regex
    date_matches = re.findall(r'\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\b(?:\s+(\d{4}))?', query, re.IGNORECASE)
    if not date_matches:
        print("No date found in the query.")
        with open('event_payload.json') as f:
            current_data = json.load(f)
        return current_data

    # If multiple months are found, return all data
    if len(date_matches) > 1:
        print(f"Multiple months detected: {[match[0] for match in date_matches]}")
        with open('event_payload.json') as f:
            current_data = json.load(f)
        return current_data

    month, year = date_matches[0]
    year = year if year else '2024'
    month = correct_month_spelling(month.lower())
    if not month:
        print("Invalid month abbreviation.")
        return current_data

    print(f"Month: {month}, Year: {year}")

    print("Possible month, year, and category:", month, year)
    
    # convert month name or abbreviation to month abbreviation
    month_abbr = {
        'january': 'jan', 'february': 'feb', 'march': 'mar', 'april': 'apr',
        'may': 'may', 'june': 'jun', 'july': 'jul', 'august': 'aug',
        'september': 'sep', 'october': 'oct', 'november': 'nov', 'december': 'dec',
        'jan': 'jan', 'feb': 'feb', 'mar': 'mar', 'apr': 'apr',
        'may': 'may', 'jun': 'jun', 'jul': 'jul', 'aug': 'aug',
        'sep': 'sep', 'oct': 'oct', 'nov': 'nov', 'dec': 'dec'
    }.get(month[:3].lower())

    if not month_abbr:
        print("Invalid month abbreviation.")
        return current_data

    print("The model thinks it is month:",month_abbr)
    # create a list of documents (each payload as a string)
    documents = []
    for payload in current_data:
        # check if the payload matches the specified month and year
        service_date = payload.get("actual_service_date", "")
        if len(service_date.split(' ')) == 2:
            payload_month_abbr, payload_year = service_date.split(' ')
            if payload_month_abbr.lower() == month_abbr and payload_year == year:
                documents.append(payload)

    # debugging: print the filtered documents
    print("Filtered documents:", documents)

    # if no documents match the criteria, return an empty list
    if not documents:
        print("No matching documents found.")
        with open('event_payload.json') as f:
            current_data = json.load(f)
        return current_data

    # directly return the filtered documents
    return documents


@app.post("/")
async def post_message(inference_payload: InferencePayload):
    global filtered_data
    if not filtered_data:
        print("Reading the Data again.")
        with open('event_payload.json') as f:
            filtered_data = json.load(f)

    # Check if the query contains the keyword "earnback"
    if "earnback" in inference_payload.query.lower():
        with open('event_payload.json') as f:
            filtered_data = json.load(f)

    relevant_data = retrieve_relevant_data(inference_payload.query, filtered_data)
    filtered_data = relevant_data # Update the global filtered data

    if "earnback" in inference_payload.query.lower():
        with open('event_payload.json') as f:
            filtered_data = json.load(f)

    populated_prompt: str = prompt
    for payload in relevant_data:
        populated_prompt += f"""\n
        - Category: {payload["category"]}
        - breach_detected: {payload["breach_detected"]}
        - service_target: {payload["service_target"]}
        - actual_service_level: {payload["actual_service_level"]}
        - service_level_date: {payload["actual_service_date"]}
        - earnback: {payload["Earnback"]}
        - data_source: {payload["data_source"]}
        - comment: {payload["Comments"]}
        - equation: {payload["Equation"]}
        """
        if "exception" not in payload["Comments"].lower():
            populated_prompt += f' - service_credit: {payload["service_credits"]}'
    for turn in inference_payload.conversation_payload:
        populated_prompt += "\n"
        populated_prompt += turn.actor + ": " + turn.content


    if inference_payload.skip_llm_call:
        return {"prompt": populated_prompt}

    print("Populated Prompt:",populated_prompt)

    if inference_payload.use_openai_directly:
        client = openai.OpenAI(api_key=llm_api_key)
        print("Model used:",model_name)
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.0,
            top_p=1e-9,
            seed=1234,
            messages = [
                {"role": "system", "content": populated_prompt},
                {"role": "user", "content": inference_payload.query}
            ]
        )
    else:
        token_response = get_cisco_access_token()
        print("Cisco token:",token_response)
        print("Populated Prompt:",populated_prompt)
        print("User content:",inference_payload.query)
        messages = [
            {"role": "system", "content": populated_prompt},
            {"role": "user", "content": inference_payload.query}
        ]
        response = get_openai_response(token_response,messages)
        print(response.choices[0].message.content)
    return {
        "prompt": populated_prompt,
        "response": response.choices[0].message.content
    }


def get_openai_response(token_response, message_with_history):
    client = AzureOpenAI(
        azure_endpoint = 'https://chat-ai.cisco.com',
        api_key=token_response.json()["access_token"],
        api_version="2023-08-01-preview"
    )
    print("Model_used:", model_name)
    response = client.chat.completions.create(
        model=model_name, # model = "deployment_name".
        temperature=0,
        top_p=1e-9,
        seed=1234,
        messages=message_with_history,
        user=f'{{"appkey": "{cisco_app_key}"}}'
    )
    return response

def get_cisco_access_token():
    url = "https://id.cisco.com/oauth2/default/v1/token"
    payload = "grant_type=client_credentials"

    value = base64.b64encode(f'{cisco_client_id}:{cisco_client_secret}'.encode('utf-8')).decode('utf-8')
    headers = {
        "Accept": "*/*",
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {value}"
    }
    token_response = requests.request("POST", url, headers=headers, data=payload)
    return token_response

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastAPI server with a specified model.")
    parser.add_argument("--model", type=str, choices=["gpt-3.5-turbo", "gpt-4o-mini"], default="gpt-4o-mini", help="Specify the model to use.")
    args = parser.parse_args()
    model_name = args.model
    uvicorn.run(app, host="0.0.0.0", port=8000)
