# src/salesforce_integration/update_case.py
# This script handles updating cases in Salesforce when new
#  information or alerts come from Arlo chatbot


from ..salesforce_integration.connect import connect_to_salesforce

def update_case(case_id, status, priority):
    try:
        sf = connect_to_salesforce()  # Make sure the connection is established
        if sf is None:
            print("Failed to connect to Salesforce.")
            return

        # Example code to update a Salesforce case
        case = sf.Case.get(case_id)
        if not case:
            print(f"Case ID {case_id} not found.")
            return

        # Update case details
        case['Status'] = status
        case['Priority'] = priority
        sf.Case.update(case_id, case)
        print(f"Case ID {case_id} updated successfully.")

    except Exception as e:
        print(f"Error updating Salesforce case: {e}")

# Usage in main.py
def main():
    # Example case details
    case_id = '00B7F000005jro4'
    status = 'In Progress'
    priority = 'High'

    # Establish Salesforce connection
    sf = connect_to_salesforce()
    if sf is None:
        print("Failed to connect to Salesforce.")
        return

    # Update case
    update_case(case_id, status, priority)

# if __name__ == "__main__":
#     main()
