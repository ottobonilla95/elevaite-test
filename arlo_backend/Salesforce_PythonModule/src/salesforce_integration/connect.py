 # Script to establish Salesforce connection 
# connect.py
#This script is responsible for establishing a 
# connection to Salesforce using the simple-salesforce Python library.


from simple_salesforce import Salesforce

from dotenv import load_dotenv
import os
from ..utils.config import (
    SALESFORCE_USERNAME,
    SALESFORCE_PASSWORD,
    SALESFORCE_SECURITY_TOKEN,
    SALESFORCE_URL
)

#here I am defining a function
def connect_to_salesforce(username=None, password=None, security_token=None, url=None):
    username = username or SALESFORCE_USERNAME
    password = password or SALESFORCE_PASSWORD
    security_token = security_token or SALESFORCE_SECURITY_TOKEN
    domain = "test" if (url or SALESFORCE_URL).endswith("test.salesforce.com") else "login"
    load_dotenv()  # Load environment variables from .env file
    try:
        sf = Salesforce(
            username=os.getenv("SALESFORCE_USERNAME"),
            password=os.getenv("SALESFORCE_PASSWORD"),
            security_token=os.getenv("SALESFORCE_SECURITY_TOKEN"),
            domain="test"
        )
        return sf
    except Exception as e:
        print(f"Error connecting to Salesforce: {e}")
        return None
#Define a function to fetch case information
def get_case_information(sf, limit=1):
    try:
        query = f"SELECT Id, CaseNumber, Subject, Status FROM Case LIMIT {limit}"
        cases = sf.query(query)
        print("Successfully retrieved case information!")
        return cases['records']
    except Exception as e:
        print(f"Error fetching case information: {e}")
        return None





