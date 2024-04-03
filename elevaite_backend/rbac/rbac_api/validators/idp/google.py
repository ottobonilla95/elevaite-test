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

    # try:
    #     # Fetch Google's OpenID configuration
    #     openid_config_response = requests.get(GOOGLE["ENDPOINTS"]["OPENID_CONFIG"])
    #     openid_config = openid_config_response.json()

    #     # Extract the URI for the public keys
    #     jwks_uri = openid_config["jwks_uri"]

    #     # Use PyJWKClient to fetch the public keys
    #     jwk_client = PyJWKClient(jwks_uri)

    #     # Get the signing key from Google's public keys
    #     signing_key = jwk_client.get_signing_key_from_jwt(access_token)

    #     # Verify the token's signature and decode it
        
    #     decoded_token = jwt.decode(
    #         access_token, 
    #         signing_key.key, 
    #         algorithms=["RS256"], 
    #     )
    #     print(f'decoded token = {decoded_token}')

    #     return decoded_token
    # except jwt.PyJWTError as e:
    #     print(f'JWT validation error in get_google_user: {e}')
    #     raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")
    # except Exception as e:
    #     print(f'Unexpected error inget_google_user method : {e}')
    #     raise ApiError.serviceunavailable("The server is currently unavailable, please try again later.")