import argparse
import json
import logging
import os
import re
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict

import boto3

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("json2bedrock")


class PipelineContext:
    """Maintains state across task executions in the pipeline."""

    def __init__(self):
        self.tasks = {}
        self.current_task_id = None

    def register_task(self, task_id: str, details: Dict[str, Any]):
        """Register a task and its details in the context."""
        self.tasks[task_id] = details

    def register_task_output(self, task_id: str, output_name: str, output_value: str):
        """Register an output for a specific task."""
        if task_id not in self.tasks:
            self.tasks[task_id] = {"outputs": {}}

        if "outputs" not in self.tasks[task_id]:
            self.tasks[task_id]["outputs"] = {}

        self.tasks[task_id]["outputs"][output_name] = output_value

    def resolve_parameter(self, param_value: str) -> str:
        """Resolve parameter values containing references to task outputs."""
        if not isinstance(param_value, str):
            return param_value

        # Pattern to match ${{tasks.TASK_ID.outputs.OUTPUT_NAME}}
        pattern = r"\$\{\{tasks\.([^.]+)\.outputs\.([^}]+)\}\}"

        def replace_reference(match):
            task_id = match.group(1)
            output_name = match.group(2)

            if task_id not in self.tasks or "outputs" not in self.tasks[task_id]:
                raise ValueError(f"Referenced task {task_id} has no outputs registered")

            if output_name not in self.tasks[task_id]["outputs"]:
                raise ValueError(f"Output {output_name} not found for task {task_id}")

            return self.tasks[task_id]["outputs"][output_name]

        return re.sub(pattern, replace_reference, param_value)

    def resolve_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve all parameters in a parameter dictionary."""
        resolved = {}
        for key, value in parameters.items():
            if isinstance(value, dict):
                resolved[key] = self.resolve_parameters(value)
            elif isinstance(value, list):
                resolved[key] = [
                    (
                        self.resolve_parameters(item)
                        if isinstance(item, dict)
                        else self.resolve_parameter(item)
                    )
                    for item in value
                ]
            else:
                resolved[key] = self.resolve_parameter(value)
        return resolved


class BedrockKnowledgeBase:
    """Handles operations related to AWS Bedrock Knowledge Bases."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = boto3.Session()
        self.kb_name = config.get("name", "unnamed_kb")

    def create_or_update(self) -> str:
        """Create or update the knowledge base using AWS CLI."""
        if self._knowledge_base_exists():
            logger.info(f"Knowledge base '{self.kb_name}' already exists.")
            return self.kb_name

        logger.info(f"Creating knowledge base '{self.kb_name}'...")

        kb_config_file = self._generate_kb_config()

        with open(kb_config_file, "r") as f:
            config_content = f.read()
            logger.info(f"Knowledge base configuration: {config_content}")

        cmd = [
            "aws",
            "bedrock-agent",
            "create-knowledge-base",
            "--cli-input-json",
            f"file://{kb_config_file}",
        ]

        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            logger.info(f"Knowledge base created successfully: {result.stdout}")
        except subprocess.CalledProcessError as e:
            logger.error(
                f"Failed to create knowledge base with bedrock-agent: {e.stderr}"
            )
            logger.error(f"Command failed with exit code {e.returncode}")

            try:
                help_result = subprocess.run(
                    ["aws", "bedrock-agent", "help"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                logger.info(f"Available Bedrock Agent commands: {help_result.stdout}")
            except:
                logger.error(
                    "Could not retrieve Bedrock Agent command help. The service might not be available in the selected region or AWS CLI version."
                )
        finally:
            if os.path.exists(kb_config_file):
                os.unlink(kb_config_file)

        return self.kb_name

    def _knowledge_base_exists(self) -> bool:
        """Check if the knowledge base already exists."""
        cmd = ["aws", "bedrock-agent", "list-knowledge-bases", "--output", "json"]

        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            kbs = json.loads(result.stdout).get("knowledgeBases", [])
            return any(kb.get("name") == self.kb_name for kb in kbs)
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to list knowledge bases: {e.stderr}")

            # Try using boto3 as fallback
            try:
                bedrock_agent = boto3.client("bedrock-agent")
                response = bedrock_agent.list_knowledge_bases()
                kbs = response.get("knowledgeBases", [])
                return any(kb.get("name") == self.kb_name for kb in kbs)
            except Exception as boto_err:
                logger.error(f"Failed to list knowledge bases via boto3: {boto_err}")

            return False

    def _generate_kb_config(self) -> str:
        """Generate a temporary file with the knowledge base configuration."""
        kb_config = {
            "name": self.config.get("name"),
            "description": self.config.get("description", ""),
            "knowledgeBaseConfiguration": {
                "type": "VECTOR",
                "vectorKnowledgeBaseConfiguration": {
                    "embeddingModelArn": self.config.get("model_id")
                },
            },
        }

        if "roleArn" in self.config:
            kb_config["roleArn"] = self.config["roleArn"]

        if self.config.get("storage_config", {}).get("type") == "s3":
            s3_config = self.config.get("storage_config", {})
            kb_config["storageConfiguration"] = {
                "type": "S3",
                "s3Configuration": {
                    "bucketName": s3_config.get("bucket"),
                    "prefix": s3_config.get("prefix", ""),
                },
            }
        else:
            kb_config["storageConfiguration"] = {"type": "BEDROCK_MANAGED"}

        fd, path = tempfile.mkstemp(suffix=".json")
        with os.fdopen(fd, "w") as f:
            json.dump(kb_config, f, indent=2)

        return path


class TaskExecutor:
    """Executes tasks defined in the pipeline configuration."""

    def __init__(self, context: PipelineContext):
        self.context = context

    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Execute a single task and capture its outputs."""
        task_id = task.get("id")
        assert task_id
        src_path = task.get("src")
        assert src_path
        parameters = task.get("parameters", {})
        expected_outputs = task.get("outputs", {})

        logger.info(f"Executing task {task_id} from {src_path}")

        # Resolve parameters (substitute references to other task outputs)
        resolved_params = self.context.resolve_parameters(parameters)

        # Register the current task in the context
        self.context.current_task_id = task_id
        self.context.register_task(
            task_id,
            {
                "id": task_id,
                "src": src_path,
                "parameters": resolved_params,
                "outputs": {},
                "status": "running",
            },
        )

        env = os.environ.copy()
        for key, value in resolved_params.items():
            env[f"BEDROCK_PARAM_{key}"] = str(value)

        try:
            start_time = time.time()
            result = subprocess.run(
                [sys.executable, src_path],
                env=env,
                check=True,
                capture_output=True,
                text=True,
            )  # type: ignore
            execution_time = time.time() - start_time

            for output_name, output_path in expected_outputs.items():
                if os.path.exists(output_path):
                    logger.info(f"Registering output {output_name} at {output_path}")
                    self.context.register_task_output(task_id, output_name, output_path)
                else:
                    logger.warning(f"Expected output file not found: {output_path}")

            self.context.tasks[task_id]["status"] = "completed"
            self.context.tasks[task_id]["execution_time"] = execution_time
            self.context.tasks[task_id]["stdout"] = result.stdout

            logger.info(
                f"Task {task_id} completed successfully in {execution_time:.2f}s"
            )
            return True

        except subprocess.CalledProcessError as e:
            self.context.tasks[task_id]["status"] = "failed"
            self.context.tasks[task_id]["error"] = {
                "returncode": e.returncode,
                "stderr": e.stderr,
            }

            logger.error(
                f"Task {task_id} failed with return code {e.returncode}: {e.stderr}"
            )
            return False


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Convert JSON to Bedrock knowledge base and execute tasks."
    )
    parser.add_argument("json_file", help="Path to the JSON configuration file")
    parser.add_argument(
        "--skip-kb", action="store_true", help="Skip knowledge base creation"
    )
    args = parser.parse_args()

    # Load and validate JSON configuration
    try:
        with open(args.json_file, "r") as f:
            config = json.load(f)

        if "knowledge_base" not in config:
            logger.warning(
                "No knowledge_base configuration found. Proceeding with tasks only."
            )

        if "tasks" not in config or not config["tasks"]:
            logger.error("No tasks defined in configuration.")
            return 1

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file: {e}")
        return 1
    except FileNotFoundError:
        logger.error(f"File not found: {args.json_file}")
        return 1

    # Initialize pipeline context
    context = PipelineContext()

    # Create knowledge base if configured and not skipped
    if "knowledge_base" in config and not args.skip_kb:
        try:
            kb = BedrockKnowledgeBase(config["knowledge_base"])
            kb_name = kb.create_or_update()
            logger.info(f"Using knowledge base: {kb_name}")
        except Exception as e:
            logger.error(f"Failed to create knowledge base: {e}")
            proceed = input("Do you want to proceed with tasks anyway? (y/n): ").lower()
            if proceed != "y":
                return 1

    # Execute tasks sequentially
    task_executor = TaskExecutor(context)
    task_success = True

    for task in config["tasks"]:
        if not task_success:
            logger.warning(f"Skipping task {task.get('id')} due to previous failure")
            continue

        task_success = task_executor.execute_task(task)

    # Report pipeline results
    success_count = sum(
        1 for task in context.tasks.values() if task.get("status") == "completed"
    )
    failed_count = sum(
        1 for task in context.tasks.values() if task.get("status") == "failed"
    )

    logger.info(
        f"Pipeline execution complete: {success_count} succeeded, {failed_count} failed"
    )

    return 0 if failed_count == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
