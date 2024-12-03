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
            "GET_USER_INFO": f"{os.getenv('FUSIONAUTH_URL', '').strip().rstrip('/')}/oauth2/userinfo",
            "OPENID_CONFIG": f"{os.getenv('FUSIONAUTH_URL', '').strip().rstrip('/')}/.well-known/openid-configuration",
        },
    }

    def get_user_email(self, access_token: str):
        """
        Retrieves the user's email address using the provided access token.
        """
        FUSIONAUTH_URL = os.getenv("FUSIONAUTH_URL", "").strip()
        if not FUSIONAUTH_URL:
            raise Exception("FUSIONAUTH_URL environment variable must be set.")

        # Validate URL protocol
        if not (
            FUSIONAUTH_URL.startswith("http://")
            or FUSIONAUTH_URL.startswith("https://")
        ):
            raise Exception("FUSIONAUTH_URL must start with 'http://' or 'https://'.")

        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            user_info_url = self._config["ENDPOINTS"]["GET_USER_INFO"]
            print(f"Requesting user info from: {user_info_url}")

            # We use verify=True for https and False for http to avoid SSL verification on http
            verify_ssl = FUSIONAUTH_URL.startswith("https://")
            response = requests.get(
                user_info_url,
                headers=headers,
                timeout=10,
                verify=verify_ssl,
            )

            print(f"Response status: {response.status_code}")
            if response.status_code != 200:
                print(f"Error response: {response.text}")
                raise ApiError.unauthorized("Failed to retrieve user info")

            response_data = response.json()

            # We check for error fields explicitly in the response
            if "error" in response_data:
                raise ApiError.unauthorized("Invalid or expired auth credentials")

            email = response_data.get("email")
            if not email:
                raise ApiError.notfound("Email not found in user information response")

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
