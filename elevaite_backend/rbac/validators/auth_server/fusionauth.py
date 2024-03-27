# import requests
# from . import FUSIONAUTH
# from ...errors.api_error import ApiError
# from fastapi import (
#    status
# )
    
# # -------------- Need to write code for validate ApiKey function here -----------------:

# def validate_apikey(apikey: str):
#    """
#    Validates an API key against the FusionAuth server.

#    Parameters:
#    - apikey (str): The API key to validate.

#    Raises:
#    - HTTPException: With status code 401 for invalid apikey or 404 if url not found,
#                   or with status code 503 for server errors or connection issues.
#    """
#    url = FUSIONAUTH["ENDPOINTS"]["VALIDATE_APIKEY"]
#    headers = {"Authorization": apikey}
   
#    try:
#       response = requests.get(url, headers=headers)
#       # Check the FusionAuth server's response.
#       if response.status_code == status.HTTP_200_OK: # apikey valid
#          return
#       elif response.status_code == status.HTTP_401_UNAUTHORIZED: # invalid api key
#          raise ApiError.unauthorized("API key is invalid.")
#       elif response.status_code == status.HTTP_404_NOT_FOUND: # invalid url for validation
#          raise ApiError.notfound("API key Validation endpoint not found.")
#    except requests.RequestException:
#       # Handle connection errors or other request issues.
#       raise ApiError.serviceunavailable("An error occurred while validating the API key.")

