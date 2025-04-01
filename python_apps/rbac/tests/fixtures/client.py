import pytest
import httpx
from fastapi import FastAPI
from httpx import AsyncClient

from rbac_api.app.routes.main import (
   role_router,
   organization_router,
   account_router,
   project_router,
   user_router,
   auth_router,
)
from rbac_api.utils.deps import get_db

@pytest.fixture(scope="function")
def app(test_session):

   app = FastAPI()
   app.include_router(organization_router)
   app.include_router(account_router)
   app.include_router(role_router)
   # Override the get_db dependency
   def override_get_db():
      yield test_session

   app.dependency_overrides[get_db] = override_get_db
   return app

@pytest.fixture(scope="function")
async def client(app):
   async with AsyncClient(transport=httpx.ASGITransport(app), base_url="http://test") as ac:
      yield ac