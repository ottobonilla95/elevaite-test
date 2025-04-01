import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI
from httpx import AsyncClient
from rbac_api.app.routes.role import role_router
from rbac_api.utils.deps import get_db
from ..models import Base

@pytest.fixture(scope="function")
def test_engine():
   return create_engine("sqlite:///:memory:")

@pytest.fixture(scope="function")
def test_session(test_engine):
   TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
   session = TestingSessionLocal()
   Base.metadata.create_all(bind=test_engine)
   yield session
   session.close()
   Base.metadata.drop_all(bind=test_engine)