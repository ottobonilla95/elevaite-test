import requests
from . import GOOGLE
from rbac_api.app.errors.api_error import ApiError

def get_google_user(access_token: str):
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(GOOGLE["ENDPOINTS"]["GET_USER_INFO"], headers=headers) 
        return response.json()
    except Exception as e:
      print(f'Unexpected error in get_google_user method : {e}')
      raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

   