import os
import ast
import sys
import subprocess
from sagemaker.processing import ScriptProcessor


# Global dictionary to cache persistent processors by command type.
CACHED_PROCESSORS = {}


# List of standard Python modules that don't need to be installed
standard_modules = {
    "os",
    "sys",
    "time",
    "json",
    "ast",
    "subprocess",
    "re",
    "math",
}

IMPORT_TO_PACKAGE_MAP = {
    "dotenv": "python-dotenv",
    "bs4": "beautifulsoup4",
    "PIL": "pillow",
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "yaml": "pyyaml",
    "mx": "mxnet",
    "flask_cors": "Flask-Cors",
    "flask_restful": "Flask-RESTful",
}


def check_pypi_dependency(dep: str) -> bool:
    """Check if the dependency exists on PyPI."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", dep],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return result.returncode == 0
    except Exception:
        return False


def get_python_dependencies(script_path: str, project_root: str) -> set:
    """Extract dependencies (imports) from a Python script, considering project structure."""
    dependencies = set()

    # Read the Python script
    with open(script_path, "r") as file:
        tree = ast.parse(file.read())

        # Walk through the AST nodes and extract imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                dependencies.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                dependencies.add(node.module)

    # Remove standard Python modules
    dependencies = {dep for dep in dependencies if dep not in standard_modules}

    return dependencies


def find_local_dependency(dep: str, project_root: str) -> str:
    """Check if the dependency exists locally in the project root or one level above."""
    # First, check the project root
    dep_path = os.path.join(project_root, dep.replace(".", os.sep))
    if os.path.exists(dep_path):
        return dep_path

    # If not found, check one level up
    parent_dir = os.path.dirname(project_root)
    dep_path = os.path.join(parent_dir, dep.replace(".", os.sep))
    if os.path.exists(dep_path):
        return dep_path

    return ""


def find_project_root(script_path: str) -> str:
    """
    Walk up from the script's directory until a directory containing
    either 'pyproject.toml' or 'requirements.txt' is found.
    This directory is assumed to be the project root.
    """
    current_dir = os.path.dirname(os.path.abspath(script_path))
    markers = {"pyproject.toml", "requirements.txt"}
    while True:
        if markers.intersection(os.listdir(current_dir)):
            return current_dir
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            # Reached the filesystem root without finding any markers.
            raise ValueError(
                "Project root not found (no pyproject.toml or requirements.txt found)"
            )
        current_dir = parent_dir


def create_dockerfile(pipeline_def: dict, dockerfile_path: str = "/tmp/Dockerfile"):
    """Dynamically create a Dockerfile based on the pipeline definition."""
    dependencies = set()

    if not pipeline_def["tasks"]:
        raise ValueError("Pipeline definition must have tasks with 'src' paths")

    # Derive the project root from the first task's source file
    first_task_src = pipeline_def["tasks"][0]["src"]
    project_root = find_project_root(first_task_src)

    # Inspect each task in the pipeline definition and gather dependencies
    for task in pipeline_def["tasks"]:
        if task["task_type"] == "pyscript":
            script_path = task["src"]
            if os.path.exists(script_path):
                dependencies.update(get_python_dependencies(script_path, project_root))

    print(f"Raw dependencies extracted from scripts: {dependencies}")

    # Initialize sets for external and local dependencies
    local_dependencies = set()
    external_dependencies = set()

    # DIRECT APPROACH: Always add python-dotenv to ensure it's available
    external_dependencies.add("python-dotenv")

    # Process dependencies
    for dep in dependencies:
        # Extract the top-level package name
        top_level_package = dep.split(".")[0]

        # First check if this is a known mapped import
        if top_level_package in IMPORT_TO_PACKAGE_MAP:
            print(
                f"Found mapped dependency: {top_level_package} -> {IMPORT_TO_PACKAGE_MAP[top_level_package]}"
            )
            external_dependencies.add(IMPORT_TO_PACKAGE_MAP[top_level_package])
            continue

        # Then check if it's a standard library module
        if top_level_package in standard_modules:
            print(f"Skipping standard library module: {top_level_package}")
            continue

        # Try to find it locally
        local_path = find_local_dependency(top_level_package, project_root)
        if local_path:
            print(f"Found local dependency: {top_level_package} at {local_path}")
            local_dependencies.add(local_path)
        # If not found locally, assume it's a pip-installable package
        else:
            print(f"Assuming external dependency: {top_level_package}")
            external_dependencies.add(top_level_package)

    print(f"External dependencies to install: {external_dependencies}")
    print(f"Local dependencies to copy: {local_dependencies}")

    # Create a Dockerfile with the dependencies.
    with open(dockerfile_path, "w") as dockerfile:
        dockerfile.write("FROM python:3.8-slim\n")

        # Create required directory structure
        dockerfile.write(
            """
RUN mkdir -p /opt/ml/processing/input && \
    mkdir -p /opt/ml/processing/output && \
    mkdir -p /opt/ml/processing/code && \
    chmod -R 777 /opt/ml/processing
"""
        )

        # Install external dependencies with pip - explicitly include python-dotenv
        if external_dependencies:
            dockerfile.write(
                "RUN pip install --no-cache-dir "
                + " ".join(external_dependencies)
                + "\n"
            )

        # Copy the entire project folder to the container first to preserve structure
        project_name = os.path.basename(project_root)
        dockerfile.write(
            f"COPY {project_name} /opt/ml/processing/code/{project_name}\n"
        )

        # Copy local dependencies into the Docker image if they're outside the main project folder
        for local_dep in local_dependencies:
            if project_root not in local_dep or not local_dep.startswith(project_root):
                relative_local_dep = os.path.relpath(
                    local_dep, os.path.dirname(project_root)
                )
                dest_path = os.path.join(
                    "/opt/ml/processing/code", os.path.basename(local_dep)
                )
                dockerfile.write(f"COPY {relative_local_dep} {dest_path}\n")

        # Set the working directory.
        dockerfile.write("WORKDIR /opt/ml/processing/code\n")

        # Add the processing/code directory to the Python path to ensure modules can be imported
        dockerfile.write("ENV PYTHONPATH=/opt/ml/processing/code:$PYTHONPATH\n")

        # Default command for the container.
        dockerfile.write('CMD ["python", "${ENTRY_POINT}"]\n')

    print(f"Dockerfile created at {dockerfile_path}")


def remove_docker_image(image_name: str):
    """Remove the Docker image after pipeline execution."""
    try:
        print(f"Removing Docker image {image_name}...")
        subprocess.run(["docker", "rmi", image_name], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error removing Docker image: {e}")


def get_cached_processor(
    container_image: str, command: list, instance_type: str, role: str
) -> ScriptProcessor:
    """
    Returns a cached ScriptProcessor for the given command type.
    If none exists, creates one, caches it, and prints a warning message.
    """
    key = tuple(command)
    if key not in CACHED_PROCESSORS:
        processor = ScriptProcessor(
            image_uri=container_image,
            command=command,
            instance_type=instance_type,
            instance_count=1,
            role=role,
            volume_size_in_gb=30,
            max_runtime_in_seconds=86400,  # 24 hours
            base_job_name="processing",
            env={
                "PYTHONUNBUFFERED": "1"  # Ensures Python output is sent to CloudWatch immediately
            },
        )
        CACHED_PROCESSORS[key] = processor
        print(
            "⚠️⚠️ WARNING: A PERSISTENT CONTAINER HAS BEEN INITIALIZED. REMEMBER TO CALL shutdown_processors() AT THE END OF YOUR PIPELINE EXECUTION! ⚠️⚠️"
        )
    return CACHED_PROCESSORS[key]


def shutdown_processors():
    """
    Shutdowns (clears) all cached processors.
    REMINDER: ⚠️⚠️ YOU MUST CALL shutdown_processors() ONCE PER PIPELINE EXECUTION TO RELEASE RESOURCES! ⚠️⚠️
    """
    global CACHED_PROCESSORS
    CACHED_PROCESSORS.clear()
    print("⚠️⚠️ ALL CACHED CONTAINERS HAVE BEEN SHUT DOWN. ⚠️⚠️")
