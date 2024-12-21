# config.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

SALESFORCE_USERNAME = os.getenv("SALESFORCE_USERNAME")
SALESFORCE_PASSWORD = os.getenv("SALESFORCE_PASSWORD")
SALESFORCE_SECURITY_TOKEN = os.getenv("SALESFORCE_SECURITY_TOKEN")
SALESFORCE_URL = os.getenv("SALESFORCE_URL", "https://iopextechnologies--newsandbox.sandbox.my.salesforce.com")
