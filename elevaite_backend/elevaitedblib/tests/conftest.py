import os
import sys
import json
import pytest
import subprocess


@pytest.fixture
def pipeline_files():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_file_path = os.path.join(current_dir, "ExamplePipeline.json")
    new_src_path = os.path.join(current_dir, "example_pipeline.py")

    with open(json_file_path, "r") as f:
        data = json.load(f)

    tasks = data.get("tasks", [])
    for task in tasks:
        if isinstance(task, dict) and "src" in task:
            task["src"] = new_src_path

    with open(json_file_path, "w") as f:
        json.dump(data, f, indent=2)

    return [json_file_path]


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
