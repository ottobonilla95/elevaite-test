import os
import sys
import pytest
import subprocess


@pytest.fixture
def pipeline_files():
    files = ["/home/vuxxs/generated_pipelines/Script.json"]

    return files


def install_load_dotenv(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])


try:
    from dotenv import load_dotenv
except ImportError:
    install_load_dotenv("python-dotenv")
    from dotenv import load_dotenv


base_dir = os.path.dirname(os.path.abspath(__file__))
dotenv_path = os.path.join(base_dir, ".env")
load_dotenv(dotenv_path=dotenv_path)
