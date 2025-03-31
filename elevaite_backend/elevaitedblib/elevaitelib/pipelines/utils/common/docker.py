import os
import subprocess
from sagemaker.processing import ScriptProcessor


# Global dictionary to cache persistent processors by command type.
CACHED_PROCESSORS = {}


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


def create_dockerfile(task: dict, dockerfile_path: str = "/tmp/Dockerfile"):
    """Dynamically create a Dockerfile based on a single task definition with `uv`."""

    if "src" not in task:
        raise ValueError("Task definition must include a 'src' path.")

    # Derive the project root from the task's source file
    project_root = find_project_root(task["src"])
    print(f"Project root identified as: {project_root}")

    # Create the Dockerfile
    with open(dockerfile_path, "w") as dockerfile:
        dockerfile.write("FROM debian:bullseye-slim\n")

        # Install uv
        dockerfile.write(
            """
RUN apt-get update && apt-get install -y \\
    curl \\
    ca-certificates \\
    gcc \\
    build-essential && rm -rf /var/lib/apt/lists/*
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

        # Copy project code to the container
        relative_project_root = os.path.relpath(project_root, os.getcwd())
        dockerfile.write(f"COPY {relative_project_root} /opt/ml/processing/code/\n")

        dockerfile.write("WORKDIR /opt/ml/processing/code\n")
        dockerfile.write("ENV PYTHONPATH=/opt/ml/processing/code:$PYTHONPATH\n")

        # Create and activate virtual environment
        dockerfile.write("RUN uv venv\n")
        dockerfile.write("ENV PATH=/opt/ml/processing/code/.venv/bin:$PATH\n")

        dockerfile.write("RUN uv pip install python-dotenv\n")

        # Install dependencies if provided
        dependencies = task.get("dependencies", [])
        for dependency in dependencies:
            dockerfile.write(f"RUN uv pip install {dependency}\n")

        # If no dependencies are provided, use sync
        if not dependencies:
            dockerfile.write("RUN uv sync\n")

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
    return CACHED_PROCESSORS[key]


def shutdown_processors():
    """
    Shutdowns (clears) all cached processors.
    """
    global CACHED_PROCESSORS
    CACHED_PROCESSORS.clear()
