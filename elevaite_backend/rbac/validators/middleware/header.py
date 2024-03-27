from fastapi import Header
from app.errors.api_error import ApiError
from validators.idp.google import get_google_user
from pprint import pprint
from app.utils.RedisSingleton import RedisSingleton

async def validate_token(auth_header: str = Header(None, alias='Authorization')):
   # Validate header bearer token
   if not auth_header or not auth_header.startswith('Bearer '):
      print(f"in validate_token dependency : Request header must contain bearer access_token for authentication")
      raise ApiError.unauthorized("Request header must contain bearer access_token for authentication")

   # Get user info from google's public endpoint using token
   token = auth_header.split(" ")[1]
   cached_email = RedisSingleton(decode_responses=True).connection.get(token) 
   
   # get(key)
   if cached_email is None:
      google_user_info_response = get_google_user(token) 
      pprint(f'google user info response : {google_user_info_response}')

      # Handle Google API Error Response
      if "error" in google_user_info_response:
         print(f"in validate_token dependency : invalid or expired auth credentials")
         raise ApiError.unauthorized("invalid or expired auth credentials")
   
      email = google_user_info_response.get("email")
      RedisSingleton().connection.setex(token, 60*60, email)
      # .setex(key, expiration, value)
   else:
      email = cached_email
      print(f'retrieved cached email = {cached_email}')
   return email