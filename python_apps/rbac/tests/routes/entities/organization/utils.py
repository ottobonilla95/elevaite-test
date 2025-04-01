import os 
# Define a function that will act as the side effect for 'ORGANIZATION_ID' key
def mock_getenv_org_id(key):
    if key == 'ORGANIZATION_ID':
        return "Invalid UUID or valid UUID associated with no organization in db"
    return os.getenv(key)  # Call the original function for other keys