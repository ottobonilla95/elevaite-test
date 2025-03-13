import os
import re
import ast
import subprocess
import pkg_resources
import importlib.util
from sagemaker.processing import ScriptProcessor
from typing import Set


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
    "datetime",
    "collections",
    "random",
    "functools",
    "itertools",
    "logging",
    "argparse",
    "copy",
    "pathlib",
    "uuid",
    "typing",
    "tempfile",
    "shutil",
    "glob",
    "pickle",
    "io",
    "urllib",
    "csv",
    "contextlib",
    "traceback",
    "multiprocessing",
    "threading",
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


def is_package_importable(package_name: str) -> bool:
    """Check if a package can be imported."""
    try:
        spec = importlib.util.find_spec(package_name)
        return spec is not None
    except (ModuleNotFoundError, ValueError):
        return False


def is_valid_pypi_package(dep: str) -> bool:
    """Check if a package is a valid installable PyPI package using importlib or pkg_resources."""
    try:
        pkg_resources.get_distribution(dep)
        return True
    except pkg_resources.DistributionNotFound:
        return is_package_importable(dep.split(".")[0])
    except Exception:
        return False


def extract_requirements_from_file(file_path: str) -> Set[str]:
    requirements = set()
    if not os.path.exists(file_path):
        return requirements

    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            # Skip comments and empty lines
            if not line or line.startswith("#"):
                continue

            # Handle editable/local installs
            if line.startswith("-e "):
                if "#egg=" in line:
                    # Extract the package name from the egg fragment
                    egg_part = line.split("#egg=")[1]
                    package = egg_part.split("[")[0].strip()
                    requirements.add(package)
                continue

            # Remove version specifiers and options
            for operator in [">=", "<=", "==", ">", "<", "~=", "!="]:
                if operator in line:
                    line = line.split(operator)[0].strip()

            # Remove square brackets for extras
            if "[" in line:
                line = line.split("[")[0].strip()

            if line:
                requirements.add(line)

    if requirements:
        print(f"Dependencies found in {file_path}: {requirements}")
    return requirements


def extract_setup_dependencies(setup_file: str) -> Set[str]:
    """Extract dependencies from setup.py file."""
    if not os.path.exists(setup_file):
        return set()

    requirements = set()

    with open(setup_file, "r") as f:
        content = f.read()

    # Look for install_requires list
    install_requires_match = re.search(
        r"install_requires\s*=\s*\[(.*?)\]", content, re.DOTALL
    )
    if install_requires_match:
        install_requires = install_requires_match.group(1)
        # Extract package names from quotes
        for match in re.finditer(r'[\'"]([^\'"\s\[\]<>=!~]+)', install_requires):
            package = match.group(1)
            requirements.add(package)

    # Look for extras_require dictionary
    extras_match = re.search(r"extras_require\s*=\s*{(.*?)}", content, re.DOTALL)
    if extras_match:
        extras = extras_match.group(1)
        # Extract package names from quotes in extras
        for match in re.finditer(r'[\'"]([^\'"\s\[\]<>=!~]+)', extras):
            package = match.group(1)
            requirements.add(package)

    if requirements:
        print(f"Dependencies found in {setup_file}: {requirements}")
    return requirements


def extract_pyproject_dependencies(pyproject_file: str) -> Set[str]:
    """Extract dependencies from pyproject.toml file."""
    if not os.path.exists(pyproject_file):
        return set()

    requirements = set()

    try:
        import toml

        with open(pyproject_file, "r") as f:
            pyproject_data = toml.load(f)

        # Poetry dependencies
        if "tool" in pyproject_data and "poetry" in pyproject_data["tool"]:
            poetry_data = pyproject_data["tool"]["poetry"]

            if "dependencies" in poetry_data:
                for dep, spec in poetry_data["dependencies"].items():
                    if dep != "python":  # Skip python version specification
                        requirements.add(dep)

            if "dev-dependencies" in poetry_data:
                for dep in poetry_data["dev-dependencies"]:
                    requirements.add(dep)

        if "project" in pyproject_data and "dependencies" in pyproject_data["project"]:
            for dep in pyproject_data["project"]["dependencies"]:
                clean_dep = re.split(r"[<>=!~]", dep)[0].strip()
                requirements.add(clean_dep)
    except ImportError:
        print("Warning: toml package not installed, skipping pyproject.toml parsing")
    except Exception as e:
        print(f"Error parsing pyproject.toml: {e}")

    if requirements:
        print(f"Dependencies found in {pyproject_file}: {requirements}")

    return requirements


def get_project_dependencies(project_root: str) -> Set[str]:
    """Get dependencies from project files like requirements.txt, setup.py, or pyproject.toml."""
    dependencies = set()

    req_file = os.path.join(project_root, "requirements.txt")
    if os.path.exists(req_file):
        print(f"Extracting dependencies from {req_file}")
        dependencies.update(extract_requirements_from_file(req_file))

    setup_file = os.path.join(project_root, "setup.py")
    if os.path.exists(setup_file):
        print(f"Extracting dependencies from {setup_file}")
        dependencies.update(extract_setup_dependencies(setup_file))

    pyproject_file = os.path.join(project_root, "pyproject.toml")
    if os.path.exists(pyproject_file):
        print(f"Extracting dependencies from {pyproject_file}")
        dependencies.update(extract_pyproject_dependencies(pyproject_file))

    return dependencies


def get_python_dependencies(script_path: str, project_root: str) -> Set[str]:
    """Extract dependencies (imports) from a Python script, considering project structure."""
    dependencies = set()

    # Read the Python script
    with open(script_path, "r") as file:
        try:
            content = file.read()
            tree = ast.parse(content)

            # Walk through the AST nodes and extract imports
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        # Get the top-level package
                        top_level = alias.name.split(".")[0]
                        dependencies.add(top_level)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Get the top-level package
                        top_level = node.module.split(".")[0]
                        dependencies.add(top_level)

            import_patterns = [
                r"importlib\.import_module\(['\"]([a-zA-Z0-9_]+)",
                r"__import__\(['\"]([a-zA-Z0-9_]+)",
                r"pip\.main\(['\"]install['\"],\s*['\"]([a-zA-Z0-9_\-]+)",
                r"requirements\s*=\s*\[\s*['\"]([a-zA-Z0-9_\-]+)",
            ]

            for pattern in import_patterns:
                for match in re.finditer(pattern, content):
                    if match.group(1):
                        dependencies.add(match.group(1))
        except SyntaxError as e:
            print(f"Warning: Syntax error in {script_path}: {e}")

    # Remove standard Python modules
    dependencies = {dep for dep in dependencies if dep not in standard_modules}

    return dependencies


def find_local_dependency(dep: str, project_root: str) -> str:
    """Check if the dependency exists locally in the project root,
    or inside the project's main package folder, or one level above."""
    # Check various possible locations for local packages
    possible_paths = [
        os.path.join(project_root, dep.replace(".", os.sep)),
        os.path.join(project_root, dep.replace(".", os.sep) + ".py"),
        os.path.join(project_root, "src", dep.replace(".", os.sep)),
        os.path.join(
            project_root, os.path.basename(project_root), dep.replace(".", os.sep)
        ),
        os.path.join(os.path.dirname(project_root), dep.replace(".", os.sep)),
    ]

    # Also check for __init__.py to identify packages
    for base_path in possible_paths:
        if os.path.isdir(base_path) and os.path.exists(
            os.path.join(base_path, "__init__.py")
        ):
            return base_path
        elif os.path.exists(base_path):
            return base_path
        elif os.path.exists(base_path + ".py"):
            return base_path + ".py"

    return ""


def find_project_root(script_path: str) -> str:
    """
    Walk up from the script's directory until a directory containing
    either 'pyproject.toml', 'setup.py', or 'requirements.txt' is found.
    This directory is assumed to be the project root.
    """
    # Define project-specific markers.
    project_markers = {"pyproject.toml", "setup.py", "requirements.txt"}
    current_dir = os.path.dirname(os.path.abspath(script_path))
    print(f"[DEBUG] Starting search for project root from: {current_dir}")

    # If the current directory itself has a marker, use it.
    if any(
        os.path.exists(os.path.join(current_dir, marker)) for marker in project_markers
    ):
        print(
            f"[DEBUG] Found project marker in current directory: {current_dir}. Stopping search."
        )
        return current_dir

    candidate = None
    while True:
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:
            print(
                "[DEBUG] Reached filesystem root without finding any project marker. Using current directory."
            )
            break

        print(f"[DEBUG] Checking parent directory: {parent_dir}")
        # Check if a project marker exists in the parent directory.
        if any(
            os.path.exists(os.path.join(parent_dir, marker))
            for marker in project_markers
        ):
            candidate = parent_dir
            print(f"[DEBUG] Found project marker in directory: {parent_dir}")
            # Check for a global marker (.git) in the parent's parent.
            grandparent = os.path.dirname(parent_dir)
            if os.path.exists(os.path.join(grandparent, ".git")):
                print(
                    f"[DEBUG] Global marker (.git) found in grandparent: {grandparent}. Stopping at {parent_dir}"
                )
                break
            else:
                print(
                    f"[DEBUG] No global marker in grandparent: {grandparent}. Stopping search at {parent_dir}"
                )
                break
        current_dir = parent_dir

    project_root = (
        candidate
        if candidate is not None
        else os.path.dirname(os.path.abspath(script_path))
    )
    print(f"[DEBUG] Project root determined as: {project_root}")
    return project_root


def create_dockerfile(pipeline_def: dict, dockerfile_path: str = "/tmp/Dockerfile"):
    """Dynamically create a Dockerfile based on the pipeline definition with `uv`."""

    if not pipeline_def.get("tasks"):
        raise ValueError("Pipeline definition must have tasks with 'src' paths")

    # Derive the project root from the first task's source file
    first_task_src = pipeline_def["tasks"][0]["src"]
    project_root = find_project_root(first_task_src)
    print(f"Project root identified as: {project_root}")

    # Create the Dockerfile
    with open(dockerfile_path, "w") as dockerfile:
        dockerfile.write("FROM python:3.10-slim\n")

        # Install required packages
        dockerfile.write(
            """
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*
"""
        )

        # Install uv package manager
        dockerfile.write(
            """
ADD https://astral.sh/uv/install.sh /uv-installer.sh
RUN sh /uv-installer.sh && rm /uv-installer.sh
"""
        )

        dockerfile.write("ENV PATH=/root/.local/bin:$PATH\n")

        # Create a virtual environment explicitly
        dockerfile.write("RUN uv venv /opt/venv\n")

        # Make sure we activate the venv in all operations
        dockerfile.write("ENV PATH=/opt/venv/bin:$PATH\n")

        dockerfile.write("RUN uv pip install sagemaker-training python-dotenv\n")

        # Copy project code to the container
        relative_project_root = os.path.relpath(project_root, os.getcwd())
        dockerfile.write(f"COPY {relative_project_root} /opt/ml/processing/code/\n")

        dockerfile.write("WORKDIR /opt/ml/processing/code\n")

        dockerfile.write("ENV PYTHONPATH=/opt/ml/processing/code:$PYTHONPATH\n")

        dockerfile.write("RUN uv sync\n")

        # Build the command: run uv sync at container startup and then run each pyscript
        cmd_parts = []
        for task in pipeline_def["tasks"]:
            if task["task_type"] == "pyscript":
                script_path = task["src"]
                relative_script_path = os.path.relpath(script_path, project_root)
                cmd_parts.append(f"uv run ./{relative_script_path}")

        if cmd_parts:
            full_cmd = " && ".join(cmd_parts)
            dockerfile.write(f'CMD ["sh", "-c", "{full_cmd}"]\n')

    print(f"[DEBUG] Dockerfile created at {dockerfile_path}")


# def create_dockerfile(pipeline_def: dict, dockerfile_path: str = "/tmp/Dockerfile"):
#     """Dynamically create a Dockerfile based on the pipeline definition."""
#     script_dependencies = set()

#     if not pipeline_def.get("tasks"):
#         raise ValueError("Pipeline definition must have tasks with 'src' paths")

#     # Derive the project root from the first task's source file
#     first_task_src = pipeline_def["tasks"][0]["src"]
#     project_root = find_project_root(first_task_src)
#     print(f"Project root identified as: {project_root}")

#     # First get dependencies from project files
#     project_dependencies = get_project_dependencies(project_root)
#     print(f"Dependencies from project files: {project_dependencies}")

#     # Then inspect each task in the pipeline definition and gather additional dependencies
#     for task in pipeline_def["tasks"]:
#         if task["task_type"] == "pyscript":
#             script_path = task["src"]
#             if os.path.exists(script_path):
#                 task_deps = get_python_dependencies(script_path, project_root)
#                 script_dependencies.update(task_deps)

#     print(f"Additional dependencies from scripts: {script_dependencies}")

#     # Combine all dependencies
#     all_dependencies = project_dependencies.union(script_dependencies)

#     # Initialize sets for external and local dependencies
#     local_dependencies = set()
#     external_dependencies = set()

#     # Always include python-dotenv
#     external_dependencies.add("python-dotenv")

#     # Process dependencies
#     for dep in all_dependencies:
#         # Extract the top-level package name
#         top_level_package = dep.split(".")[0]

#         # Check if this is a known mapped import
#         if top_level_package in IMPORT_TO_PACKAGE_MAP:
#             print(
#                 f"Found mapped dependency: {top_level_package} -> {IMPORT_TO_PACKAGE_MAP[top_level_package]}"
#             )
#             external_dependencies.add(IMPORT_TO_PACKAGE_MAP[top_level_package])
#             continue

#         # Skip standard library modules
#         if top_level_package in standard_modules:
#             print(f"Skipping standard library module: {top_level_package}")
#             continue

#         # Try to find it locally
#         local_path = find_local_dependency(top_level_package, project_root)
#         if local_path:
#             print(f"Found local dependency: {top_level_package} at {local_path}")
#             local_dependencies.add(local_path)
#         elif top_level_package in project_dependencies or is_valid_pypi_package(
#             top_level_package
#         ):
#             print(f"Adding external dependency: {top_level_package}")
#             external_dependencies.add(top_level_package)
#         else:
#             print(
#                 f"⚠️ Warning: '{top_level_package}' is neither local nor a valid PyPI package. Skipping."
#             )

#     print(f"External dependencies to install: {external_dependencies}")
#     print(f"Local dependencies to copy: {local_dependencies}")

#     # Create the Dockerfile
#     with open(dockerfile_path, "w") as dockerfile:
#         dockerfile.write("FROM python:3.11-slim\n")
#         dockerfile.write("ENV DEBIAN_FRONTEND=noninteractive\n")

#         # Create required directory structure
#         dockerfile.write(
#             """
# RUN mkdir -p /opt/ml/processing/input && \
#     mkdir -p /opt/ml/processing/output && \
#     mkdir -p /opt/ml/processing/code && \
#     chmod -R 777 /opt/ml/processing
# """
#         )

#         # Install necessary build tools
#         dockerfile.write(
#             """
# RUN apt-get update && \
#     apt-get install -y --no-install-recommends \
#     build-essential \
#     gcc \
#     && apt-get clean && rm -rf /var/lib/apt/lists/*
# """
#         )

#         # Install all external dependencies
#         if external_dependencies:
#             deps_list = list(external_dependencies)
#             batch_str = " ".join(deps_list)
#             dockerfile.write(
#                 f"""
#         RUN mkdir -p /tmp/pipelines_pip_cache && \
#             pip install --upgrade pip && \
#             attempt=0; \
#             until [ $attempt -ge 3 ]; do \
#                 if pip install --cache-dir /tmp/pipelines_pip_cache {batch_str}; then \
#                     break; \
#                 fi; \
#                 attempt=$((attempt+1)); \
#                 echo "Attempt $attempt failed. Retrying..." && sleep 1; \
#             done || (echo "Error: Failed to install packages: {batch_str}" && exit 1)
#         """
#             )

#         # Copy the entire project folder to the container
#         project_name = os.path.basename(project_root)
#         dockerfile.write(
#             f"COPY {project_name} /opt/ml/processing/code/{project_name}\n"
#         )

#         # Copy local dependencies if they're outside the project folder
#         for local_dep in local_dependencies:
#             if project_root not in local_dep or not local_dep.startswith(project_root):
#                 relative_local_dep = os.path.relpath(
#                     local_dep, os.path.dirname(project_root)
#                 )
#                 dest_path = os.path.join(
#                     "/opt/ml/processing/code", os.path.basename(local_dep)
#                 )
#                 dockerfile.write(f"COPY {relative_local_dep} {dest_path}\n")

#         # Set the working directory
#         dockerfile.write("WORKDIR /opt/ml/processing/code\n")

#         # Add the processing/code directory to PYTHONPATH
#         dockerfile.write("ENV PYTHONPATH=/opt/ml/processing/code:$PYTHONPATH\n")

#         # Default command for the container
#         dockerfile.write('CMD ["python", "${ENTRY_POINT}"]\n')

#     print(f"Dockerfile created at {dockerfile_path}")


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
