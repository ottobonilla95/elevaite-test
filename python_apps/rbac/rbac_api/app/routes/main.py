# # routes/main.py
from fastapi import FastAPI
from .organization import organization_router
from .account import account_router
from .user import user_router
from .project import project_router
from .role import role_router
from .auth import auth_router
from .apikey import apikey_router


def attach_routes(app: FastAPI) -> None:
    app.include_router(auth_router)
    app.include_router(organization_router)
    app.include_router(account_router)
    app.include_router(project_router)
    app.include_router(user_router)
    app.include_router(role_router)
    app.include_router(apikey_router)
