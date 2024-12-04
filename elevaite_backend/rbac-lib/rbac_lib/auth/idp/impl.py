import os
from typing import Optional
import requests
from fastapi import HTTPException
from fusionauth.fusionauth_client import FusionAuthClient

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
    def __init__(self):
        """
        Initializes the FusionAuth client with the API key and checks for necessary configurations.
        """
        FUSIONAUTH_API_KEY = os.getenv("FUSIONAUTH_API_KEY", "").strip()
        FUSIONAUTH_URL = os.getenv("FUSIONAUTH_URL", "").strip()

        if not FUSIONAUTH_API_KEY:
            raise Exception("FUSIONAUTH_API_KEY environment variable must be set.")
        if not FUSIONAUTH_URL:
            raise Exception("FUSIONAUTH_URL environment variable must be set.")

        # Validate URL protocol
        if not (
            FUSIONAUTH_URL.startswith("http://")
            or FUSIONAUTH_URL.startswith("https://")
        ):
            raise Exception("FUSIONAUTH_URL must start with 'http://' or 'https://'.")

        self.client = FusionAuthClient(FUSIONAUTH_API_KEY, FUSIONAUTH_URL)

    def get_user_email(self, access_token: str) -> Optional[str]:
        """
        Retrieves the user's email address using the provided access token.
        """
        try:
            # We use the FusionAuth SDK to interact with the /oauth2/userinfo endpoint
            response = self.client.retrieve_user_using_jwt(access_token)

            if not response.was_successful():
                print(f"FusionAuth error: {response.error_response}")
                if response.status == 401:
                    raise ApiError.unauthorized("Invalid or expired auth credentials.")
                else:
                    raise ApiError.serviceunavailable("Failed to retrieve user info.")

            success_response = response.success_response
            if not success_response:
                raise ApiError.serviceunavailable("No success response received.")
            user_info = success_response.get("user", {})
            email = user_info.get("email")
            if not email:
                raise ApiError.notfound("Email not found in user information response.")

            return email
        except requests.Timeout:
            print("FusionAuth API timeout error")
            raise ApiError.serviceunavailable(
                "The server is currently unavailable, please try again later."
            )
        except requests.exceptions.SSLError as ssl_error:
            print(f"SSL error occurred: {ssl_error}")
            raise ApiError.serviceunavailable(
                "SSL connection failed. Please try again later."
            )
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
