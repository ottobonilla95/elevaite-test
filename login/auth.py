import uvicorn
import logging
import os
from datetime import datetime

from authlib.integrations.starlette_client import OAuth
from authlib.integrations.starlette_client import OAuthError
from fastapi import FastAPI
from fastapi import Request
from starlette.config import Config
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import JSONResponse
from starlette.responses import RedirectResponse
from starlette.responses import HTMLResponse

import jwt
from db.utils import Jwt_User_Claim

# Create the auth app
auth_app = FastAPI()
logger = logging.getLogger("auth_app")

# OAuth settings
GOOGLE_CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID') or None
GOOGLE_CLIENT_SECRET = os.environ.get('GOOGLE_CLIENT_SECRET') or None
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY") or None
if GOOGLE_CLIENT_ID is None or GOOGLE_CLIENT_SECRET is None:
    raise BaseException('Missing Google Auth env variables')

# Set up OAuth
config_data = {'GOOGLE_CLIENT_ID': GOOGLE_CLIENT_ID, 'GOOGLE_CLIENT_SECRET': GOOGLE_CLIENT_SECRET}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)
oauth.register(
    name='google',
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)

# Set up the middleware to read the request session
SECRET_KEY = os.environ.get('SECRET_KEY') or None
if SECRET_KEY is None or JWT_SECRET_KEY is None:
    raise 'Missing SECRET_KEY'
auth_app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

@auth_app.route('/login/google')
async def login(request: Request):
    redirect_uri = request.url_for('auth')  # This creates the url for our /auth endpoint
    return await oauth.google.authorize_redirect(request, "https://login.iopex.ai/oauth/google")

@auth_app.route('/oauth/google')
async def auth(request: Request):
    try:
        access_token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        return RedirectResponse(url='/')
    token = Jwt_User_Claim.jwt_token_from_oauth(oauth_user_data=dict(user_data = access_token['userinfo']))
    headers = {'Authorization' : 'Bearer ' + token}
    return RedirectResponse(url='https://elevaite-cb.iopex.ai', headers=headers)

@auth_app.route('/logout')
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

@auth_app.get('/')
def public(request: Request):
    user = request.session.get('user')
    if user:
        name = user.get('name')
        return HTMLResponse(f'<p>Hello {name}!</p><a href=/logout>Logout</a>')
    return HTMLResponse('<a href=/login/google>Login</a>')

@auth_app.get("/hc")
def hc(request: Request):
    return {"status": "ok"}

if __name__ == '__main__':
    uvicorn.run(auth_app, port=7000)
