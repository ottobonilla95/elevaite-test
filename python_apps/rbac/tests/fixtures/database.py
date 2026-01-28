import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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