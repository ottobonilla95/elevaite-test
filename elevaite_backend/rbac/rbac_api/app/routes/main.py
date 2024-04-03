# # routes/main.py
from fastapi import FastAPI
from .organization_routes import organization_router
from .account_routes import account_router
from .user_routes import user_router
from .project_routes import project_router
from .role_routes import role_router
from .auth_routes import auth_router
# from .apikey_routes import apikey_router

def attach_routes(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(organization_router)
    app.include_router(account_router)
    app.include_router(project_router)
    app.include_router(user_router)
    app.include_router(role_router)

#     app.include_router(apikey_router, prefix="/")
