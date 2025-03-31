# Unused functions for automatic dependency scanning
import os
import re
import ast
import importlib.util
import pkg_resources
from typing import Set


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
