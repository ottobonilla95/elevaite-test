# from salesforce_integration.connect import connect_to_salesforce
from .salesforce_integration.connect import connect_to_salesforce
from .utils.config import SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_SECURITY_TOKEN, SALESFORCE_URL

def get_case_information(sf,case_number, limit=1):
    try:
        query = f"SELECT Id, CaseNumber, Subject, UX_Version__c, Problem__c, Rootcause__c, Symptoms__c, Contact_Phone__c, ContactEmail,AccountId, Description, Status FROM Case where CaseNumber='{case_number}' LIMIT {limit}"
        cases = sf.query(query)
        print("Successfully retrieved case information!")
        return cases['records']
    except Exception as e:
        print(f"Error fetching case information: {e}")
        return None


def get_sf_case(case_number="00001007"):
    salesforce_instance = connect_to_salesforce(SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_SECURITY_TOKEN, SALESFORCE_URL)
    if salesforce_instance:
        print("Connected to Salesforce successfully!")
    else:
        print("Failed to connect to Salesforce.")
    # salesforce_instance = connect_to_salesforce()
    if salesforce_instance:
        case_info = get_case_information(salesforce_instance,case_number=case_number)
        print(case_info)
        if case_info:
            for case in case_info:
                return case
                # print(f"Case Number: {case['CaseNumber']}, Subject: {case['Subject']}, : {case['Status']}, AccountId: {case['AccountId']}")

def save_summary_to_salesforce(case_number, summary):
    sf = connect_to_salesforce(SALESFORCE_USERNAME, SALESFORCE_PASSWORD, SALESFORCE_SECURITY_TOKEN, SALESFORCE_URL)
    if sf:
        print("Connected to Salesforce successfully!")
    else:
        print("Failed to connect to Salesforce.")


    case_query = sf.query(f"SELECT Id FROM Case WHERE CaseNumber = '{case_number}' LIMIT 1")
    if case_query['records']:
        case_id = case_query['records'][0]['Id']
        # Update the Case record
        sf.Case.update(case_id, {'Case_Summary__c': summary})
        return "Case updated successfully."
    else:
        return "Case not found."
