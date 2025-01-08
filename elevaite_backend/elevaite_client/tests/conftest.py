import os
import pytest
from dotenv import load_dotenv


base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, "../.env.test")
load_dotenv(dotenv_path=dotenv_path)

from elevaite_client.rpc.client import ModelProviderFactory


@pytest.fixture
def model_provider_factory():
    return ModelProviderFactory()


@pytest.fixture
def fake_prompt():
    return "Tell me a joke."
