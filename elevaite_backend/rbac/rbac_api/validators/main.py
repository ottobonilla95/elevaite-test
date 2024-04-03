# Need to define a validator_decorator here which takes in resource_type and action, and returns another decorator which has the injected request from the route handler. 
# Implement this at the end. Right now, finish implementing all the API's first. The nested decorator would look something like this:

# def auth_decorator(action: str) -> Callable: # define the top-most decorating function which takes action from backend for security
#    def decorator(callback : Callable[..., Any]) -> Callable: # define the decorator which returns the wrapper
#       async def wrapper(request: Request): # wrapper with role-based safeguarding logic before calling callback
         
#          if not request:
#             raise ApiError.internal_error("Request object not found") # path operation function needs to expect 'fastapi.Request' in argument

#          if action not in Actions._value2member_map_:
#             raise ApiError.badRequest("Invalid or missing action")
         
#          # Validate header bearer token
#          auth_header = request.headers.get('Authorization')
#          if not auth_header or not auth_header.startswith('Bearer '):
#             raise ApiError.unauthorized("Request header must contain Google access_token for authentication")

#          token = auth_header.split(" ")[1]
#          google_user_info_response = get_google_user(token) 
#          print(f'google user info response : {google_user_info_response}')
#          # Handle Google API Error Response
#          if "error" in google_user_info_response:
#             raise ApiError.unauthorized(google_user_info_response["error"]["message"])
         
#          # Extract email and call FusionAuth's API
#          email = google_user_info_response.get("email")
#          print(f'google user email extracted : {email}')
#          fusionauth_user_response = get_fusionauth_user(email)
#          print(f'fusionauth_user_resposne : {fusionauth_user_response}')
#          # Initialize a variable to track if the required application is found
#          application_found = False

#          # Parse FusionAuth response to get roles for the specific application
#          user_roles = set()
#          for registration in fusionauth_user_response["user"]["registrations"]:
#             if registration["applicationId"] == FUSIONAUTH["APPLICATIONS"]["ELEVAITE"]["ID"]:
#                   registered_roles = set(registration.get("roles", []))
#                   # Filter roles to include only those that exist in Roles enum
#                   valid_roles = {role for role in registered_roles if role in Roles._value2member_map_}
#                   user_roles.update(valid_roles)
#                   application_found = True
#                   break  # Break the loop once the required application ID is found
         
#          print(f'user_roles : {user_roles}')
#          # Check if the required application was found
#          if not application_found:
#             raise ApiError.unauthorized("User not registered in Elevaite application")

#          # Check if action is allowed for any of the user's roles
#          is_action_allowed = any(action in role_permissions.get(role, set()) for role in user_roles)
#          if not is_action_allowed:
#             raise ApiError.forbidden("Action is not allowed for user's roles")

#          return await callback(request)
#       return wrapper
#    return decorator