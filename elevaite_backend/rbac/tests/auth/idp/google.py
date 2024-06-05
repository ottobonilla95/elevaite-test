
def get_user_email_response_with_success(email: str):
    return {"email": email}

def get_user_email_response_with_error():
    return {"error": "invalid or expired token"}