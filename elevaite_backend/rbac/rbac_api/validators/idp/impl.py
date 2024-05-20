import requests
from fastapi import HTTPException
from rbac_api.app.errors.api_error import ApiError
from .interface import IDPInterface

class GoogleIDP(IDPInterface):
   _config = {
        "ENDPOINTS" : {
            "GET_USER_INFO": "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
            "OPENID_CONFIG": "https://accounts.google.com/.well-known/openid-configuration",
        },
   }

   def get_user_email(self, access_token: str):
      try:
         headers = {"Authorization": f"Bearer {access_token}"}
         response = requests.get(self._config["ENDPOINTS"]["GET_USER_INFO"], headers=headers) 
         response = response.json()

         # Handle Google API Error Response
         if "error" in response:
            print(f"in idp/google get_user : invalid or expired auth credentials")
            raise ApiError.unauthorized("invalid or expired auth credentials")
         
         email = response.get("email")
         return email
      except HTTPException as e:
         raise e
      except Exception as e:
         print(f'Unexpected error in idp/google get_user method : {e}')
         raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")

# add other implementations here.. 