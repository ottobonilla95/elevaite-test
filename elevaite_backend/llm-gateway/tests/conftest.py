import subprocess
import sys


# Install dotenv manually. As of today, poetry is incompatible with python-dotenv
def install_load_dotenv(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
    from dotenv import load_dotenv
except ImportError:
    install_load_dotenv("python-dotenv")
    from dotenv import load_dotenv

import os
import pytest

base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=dotenv_path)

from llm_gateway.models.provider import ModelProviderFactory


@pytest.fixture
def model_provider_factory():
    return ModelProviderFactory()


@pytest.fixture
def fake_prompt():
    return "Tell me a joke."
