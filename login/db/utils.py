import db
from pydantic import EmailStr, ValidationError
from datetime import datetime, timezone, timedelta
import secrets
import jwt
import secrets
import uuid

class Jwt_User_Claim:
    def __init__(self, name: str, email: str, sub: str):
        self.name = name
        self.email = email
        self.sub = sub

    def set_expiry_time(self, exp_time_in_secs: int = None):
        exp_time_in_secs = exp_time_in_secs if exp_time_in_secs else 3600
        self.exp = (datetime.utcnow() + timedelta(seconds=exp_time_in_secs)).timestamp()
    
    @classmethod
    def from_oauth(cls, oauth_user_data):
        return cls(name=oauth_user_data['name'], email=oauth_user_data['email'], sub=oauth_user_data['sub'])
    
    @staticmethod
    def jwt_token_from_oauth(oauth_user_data, key):
        jwt_user_data = Jwt_User_Claim.from_oauth(oauth_user_data=oauth_user_data)
        return jwt_user_data.encode(key=key)
    
    def encode(self, key):
        self.set_expiry_time(exp_time_in_secs=1800)
        payload_data = {"sub": self.sub, "name": self.name, "email": self.email, "exp": self.exp}
        return jwt.encode(payload=payload_data, key=key, algorithm="HS256")

def validate_oauth_user(oauth_user_data):
    try:
        create_or_update_user(oauth_user_data=oauth_user_data)
        elevaite_user = db.User(
            email = oauth_user_data['email'],
            first_name = oauth_user_data['given_name'],
            last_name = oauth_user_data['last_name'],
            name = oauth_user_data['name'],
            join_date = datetime.utcnow()
        )
        create_or_update_user(elevaite_user)
    except ValidationError as e:
        raise e

def create_user(oauth_user_data):
    elevaite_user = db.User(
            email = oauth_user_data['email'],
            first_name = oauth_user_data['given_name'],
            last_name = oauth_user_data['last_name'],
            name = oauth_user_data['name'],
            join_date = datetime.utcnow()
        )
    elevaite_user.save()
    return elevaite_user

def create_or_update_user_session(user_session_info):
    redis_con = db.get_redis_connection()
    session_key = secrets.token.url_safe(18)
    redis_con.hmset(session_key, user_session_info)
    return session_key

def create_or_update_user(oauth_user_data):
    user = db.User.find(db.User.email == oauth_user_data['email']).all()
    if (len(user.results) == 0):
        # create time
        elevaite_user = create_user(oauth_user_data=oauth_user_data)
        user_session_info = {'user':elevaite_user.pk, 'email': elevaite_user.email, 'name': elevaite_user.name}
    else:
        elevaite_user = user.results[0]
        user_session_info = {'user':elevaite_user['pk'], 'email': elevaite_user['email'], 'name': elevaite_user['name']}
    return user_session_info

def get_user_session(oauth_user_data):
    user_info = create_or_update_user(oauth_user_data=oauth_user_data)
    session_key = create_or_update_user_session(user_session_info=user_info)
