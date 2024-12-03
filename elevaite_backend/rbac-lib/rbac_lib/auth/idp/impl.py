import os
import requests
from fastapi import HTTPException
from rbac_lib.utils.api_error import ApiError
from .interface import IDPInterface


class GoogleIDP(IDPInterface):
    _config = {
        "ENDPOINTS": {
            "GET_USER_INFO": "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
            "OPENID_CONFIG": "https://accounts.google.com/.well-known/openid-configuration",
        },
    }

    def get_user_email(self, access_token: str):
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(
                self._config["ENDPOINTS"]["GET_USER_INFO"], headers=headers
            )
            response = response.json()

            # Handle Google API Error Response
            if "error" in response:
                # print(f"in idp/google get_user : invalid or expired auth credentials")
                raise ApiError.unauthorized("invalid or expired auth credentials")

            email = response.get("email")
            return email
        except HTTPException as e:
            raise e
        except Exception as e:
            print(f"Unexpected error in idp/google get_user method : {e}")
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )


class FusionAuthIDP(IDPInterface):
    _config = {
        "ENDPOINTS": {
            "GET_USER_INFO": f"{os.getenv('FUSIONAUTH_URL')}/oauth2/userinfo",
            "OPENID_CONFIG": f"{os.getenv('FUSIONAUTH_URL')}/.well-known/openid-configuration",
        },
    }

    def get_user_email(self, access_token: str):
        """
        Retrieves the user's email address using the provided access token.
        """
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            response = requests.get(
                self._config["ENDPOINTS"]["GET_USER_INFO"] or "", headers=headers
            )
            response.raise_for_status()  # We ensure any HTTP error codes are raised as exceptions

            response_data = response.json()

            if "error" in response_data:
                raise ApiError.unauthorized("Invalid or expired auth credentials")

            email = response_data.get("email")
            if not email:
                raise ApiError.notfound("Email not found in user information response")

            return email
        except HTTPException as e:
            raise e
        except requests.RequestException as e:
            print(f"FusionAuth API error: {e}")
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except Exception as e:
            print(f"Unexpected error in FusionAuthIDP get_user_email method: {e}")
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )


# add other implementations here..
