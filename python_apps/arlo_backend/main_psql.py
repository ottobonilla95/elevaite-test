from iopexwise_psql.load_database_modified import DatabaseConnector, CaseHistoryLoader
from typing import Optional, Union


def get_opexwise_data(contact_email: Optional[str] = None, case_number: Optional[str] = None):

    # Initialize the database
    connector = DatabaseConnector()
    case_history_loader = CaseHistoryLoader(connector)

    if not contact_email and not case_number:
        print("Error: provide at least an email ID or a case number.")
        return

    case_history = case_history_loader.get_history(case_number=case_number, contact_email=contact_email)

    for i in case_history:
        print(type(i))

    if case_history:
        print(f"Case history found: {case_history}")
    else:
        print("No case history found for the provided user details.")
    return case_history


# if __name__ == "__main__":
#     # main(email="person_2@gmail.com")
#     main(case_number="1")