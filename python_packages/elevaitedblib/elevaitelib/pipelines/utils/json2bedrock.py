import argparse
import json
import logging
import os
import re
import sys
import time
from typing import Any, Dict, Optional

import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("aws-pipeline")


class PipelineContext:
    """Maintains state across task executions in the pipeline."""

    def __init__(self):
        self.tasks = {}
        self.current_task_id = None

    def register_task(self, task_id: str, details: Dict[str, Any]):
        """Register a task and its details in the context."""
        self.tasks[task_id] = details

    def register_task_output(self, task_id: str, output_name: str, output_value: Any):
        """Register an output for a specific task."""
        if task_id not in self.tasks:
            self.tasks[task_id] = {"outputs": {}}

        if "outputs" not in self.tasks[task_id]:
            self.tasks[task_id]["outputs"] = {}

        self.tasks[task_id]["outputs"][output_name] = output_value

    def resolve_parameter(self, param_value: Any) -> Any:
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
    """
    Handles operations related to AWS Bedrock Knowledge Bases.
    Supports creating, querying, and updating knowledge bases.
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.session = boto3.Session()
        self.kb_name = config.get("name", "unnamed_kb")
        self.kb_id = None
        # Create the Bedrock client
        self.bedrock_agent = boto3.client("bedrock-agent")
        self.bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")
        # Create the OpenSearch client if collection ARN is provided
        if config.get("opensearchCollectionArn"):
            self.aoss_client = boto3.client("opensearchserverless")
            self.collection_arn = config.get("opensearchCollectionArn")
            if self.collection_arn:
                self.collection_id = self.collection_arn.split("/")[-1]
            self.vector_index_name = config.get("vectorIndexName", "bedrock-kb-index")

    def _ensure_opensearch_index_exists(self) -> bool:
        """Create the OpenSearch index if it doesn't exist."""
        if not hasattr(self, "aoss_client"):
            logger.warning(
                "No OpenSearch collection specified, skipping index creation"
            )
            return False

        try:
            logger.info(
                f"Ensuring index '{self.vector_index_name}' exists in collection {self.collection_id}..."
            )

            try:
                collection_response = self.aoss_client.batch_get_collection(
                    ids=[self.collection_id]
                )
                collections = collection_response.get("collectionDetails", [])

                if not collections:
                    logger.error(f"Collection {self.collection_id} not found")
                    return False

                collection = collections[0]
                if collection.get("status") != "ACTIVE":
                    wait_time = 60  # seconds to wait for collection to become active
                    logger.warning(
                        f"Collection {self.collection_id} exists but status is {collection.get('status')}, waiting up to {wait_time}s for ACTIVE status..."
                    )

                    # Wait for collection to become active
                    start_time = time.time()
                    while time.time() - start_time < wait_time:
                        time.sleep(10)
                        collection_response = self.aoss_client.batch_get_collection(
                            ids=[self.collection_id]
                        )
                        if (
                            collection_response.get("collectionDetails")[0].get(
                                "status"
                            )
                            == "ACTIVE"
                        ):
                            logger.info(
                                f"Collection {self.collection_id} is now ACTIVE"
                            )
                            break
                    else:
                        logger.error(
                            f"Timed out waiting for collection {self.collection_id} to become ACTIVE"
                        )
                        return False

                logger.info(
                    f"Verified collection {self.collection_id} exists and is active"
                )
            except ClientError as e:
                logger.error(f"Failed to verify collection status: {e}")
                return False

            try:
                all_policies = []

                try:
                    # Try to list policies directly first
                    policies_response = self.aoss_client.list_access_policies(
                        type="data"
                    )
                    all_policies = policies_response.get("accessPolicySummaries", [])
                except Exception as e:
                    logger.warning(f"Error listing access policies: {e}")

                # Check if policy for this collection exists
                policy_exists = False
                for policy in all_policies:
                    if self.collection_id in policy.get("name", ""):
                        policy_exists = True
                        logger.info(
                            f"Data access policy already exists for collection {self.collection_id}"
                        )
                        break

                # Create policy if it doesn't exist
                if not policy_exists:
                    # Create a shorter policy name that fits the constraints
                    # Must be <= 32 chars, follow pattern [a-z][a-z0-9-]+
                    policy_name = f"aoss-{self.collection_id[:20]}-policy"
                    logger.info(
                        f"Creating data access policy '{policy_name}' for collection {self.collection_id}"
                    )

                    policy_document = [
                        {
                            "Resource": f"aoss:collection/{self.collection_id}",
                            "Permission": [
                                "aoss:CreateIndex",
                                "aoss:DeleteIndex",
                                "aoss:UpdateIndex",
                                "aoss:DescribeIndex",
                                "aoss:ReadDocument",
                                "aoss:WriteDocument",
                            ],
                            "ResourceType": "index",
                            "Principal": "*",
                        }
                    ]

                    self.aoss_client.create_access_policy(
                        name=policy_name,
                        type="data",
                        policy=json.dumps(policy_document),
                        description=f"Data access policy for collection {self.collection_id}",
                    )
                    logger.info(
                        f"Created data access policy for collection {self.collection_id}"
                    )

                    # Wait for policy to take effect
                    logger.info("Waiting for policy to propagate (10 seconds)...")
                    time.sleep(10)
            except ClientError as e:
                logger.warning(f"Failed to create access policy: {e}")
                # Continue anyway, policy might already exist or be managed elsewhere

            try:
                # First, try using batch_get_collection to get the endpoint
                collection_response = self.aoss_client.batch_get_collection(
                    ids=[self.collection_id]
                )
                collections = collection_response.get("collectionDetails", [])

                # Get the region
                region = self.session.region_name or "us-west-2"

                # Construct the endpoint using the standard format
                collection_endpoint = (
                    f"{self.collection_id}.{region}.aoss.amazonaws.com"
                )
                logger.info(
                    f"Using constructed OpenSearch endpoint: {collection_endpoint}"
                )
            except ClientError as e:
                logger.error(f"Failed to get collection endpoint: {e}")

                # Fallback solution if API calls fail
                region = self.session.region_name or "us-west-2"
                collection_endpoint = (
                    f"{self.collection_id}.{region}.aoss.amazonaws.com"
                )
                logger.warning(
                    f"Using fallback constructed endpoint after API failure: {collection_endpoint}"
                )

            try:
                # Use the AWS OpenSearch Serverless create_index API instead of REST API
                logger.info(
                    f"Creating index '{self.vector_index_name}' in collection {self.collection_id} using AWS API..."
                )

                # Prepare the index settings
                index_settings = {
                    "mappings": {
                        "properties": {
                            "content": {"type": "text"},
                            "metadata": {"type": "object"},
                            "bedrock_embedding": {
                                "type": "knn_vector",
                                "dimension": 1536,  # Titan embedding dimension
                                "method": {
                                    "name": "hnsw",
                                    "space_type": "cosinesimil",
                                    "engine": "nmslib",
                                    "parameters": {"ef_construction": 128, "m": 16},
                                },
                            },
                        }
                    }
                }

                try:
                    if hasattr(self.aoss_client, "create_index"):
                        response = self.aoss_client.create_index(
                            id=f"{self.collection_id}/{self.vector_index_name}",
                            name=self.vector_index_name,
                            collectionId=self.collection_id,
                            body=json.dumps(index_settings),
                        )
                        logger.info(
                            f"Successfully created index via boto3 API: {response}"
                        )
                        time.sleep(5)  # Wait for index to be ready
                        return True
                except Exception as e:
                    if "already exists" in str(e).lower():
                        logger.info(
                            f"Index '{self.vector_index_name}' already exists (from boto3 API error)"
                        )
                        return True
                    logger.warning(f"Failed to create index via boto3 API: {e}")

                logger.info("Attempting to create index using REST API...")
                import requests
                from requests_aws4auth import AWS4Auth

                region = self.session.region_name or "us-west-2"
                credentials = self.session.get_credentials()

                auth = AWS4Auth(
                    credentials.access_key,
                    credentials.secret_key,
                    region,
                    "aoss",
                    session_token=credentials.token,
                )

                # REST API request
                host = f"{self.collection_id}.{region}.aoss.amazonaws.com"
                url = f"https://{host}/{self.vector_index_name}"

                logger.info(f"Using OpenSearch REST API endpoint: {url}")

                try:
                    head_response = requests.head(url, auth=auth, timeout=30)

                    if head_response.status_code == 200:
                        logger.info(
                            f"Index '{self.vector_index_name}' already exists, no need to create it"
                        )
                        return True
                    elif head_response.status_code != 404:
                        logger.warning(
                            f"Unexpected status code checking index: {head_response.status_code}"
                        )
                except Exception as e:
                    logger.warning(f"Error checking if index exists: {e}")

                # Create the index with multiple retries
                max_retries = 3
                for retry in range(max_retries):
                    try:
                        if retry > 0:
                            logger.info(
                                f"Retry {retry+1}/{max_retries} creating index..."
                            )
                            time.sleep(5 * (retry + 1))

                        # Create the index
                        response = requests.put(
                            url,
                            auth=auth,
                            json=index_settings,
                            headers={"Content-Type": "application/json"},
                            timeout=30,
                        )

                        if response.status_code in [200, 201]:
                            logger.info(
                                f"Successfully created index '{self.vector_index_name}' via REST API"
                            )
                            time.sleep(10)  # Wait for index to be fully ready
                            return True
                        elif (
                            response.status_code == 400
                            and "already_exists" in response.text
                        ):
                            logger.info(
                                f"Index '{self.vector_index_name}' already exists (from REST API)"
                            )
                            return True
                        else:
                            logger.warning(
                                f"REST API index creation failed: {response.status_code} - {response.text}"
                            )
                            # If the error is about index settings, try again with simpler settings
                            if "settings" in response.text.lower():
                                logger.info("Retrying without index settings...")
                                index_settings = {
                                    "mappings": {
                                        "properties": {
                                            "content": {"type": "text"},
                                            "metadata": {"type": "object"},
                                            "bedrock_embedding": {
                                                "type": "knn_vector",
                                                "dimension": 1536,
                                            },
                                        }
                                    }
                                }
                    except Exception as e:
                        logger.warning(f"Error creating index (attempt {retry+1}): {e}")

                logger.error(
                    f"Failed to create index '{self.vector_index_name}' after multiple attempts"
                )
                logger.error(
                    "All methods to create index failed. Cannot proceed with knowledge base creation."
                )
                return False

            except Exception as e:
                logger.error(f"Error creating index: {e}")
                return False

        except Exception as e:
            logger.error(f"Error ensuring OpenSearch index exists: {e}")
            return False

    def create_or_update(self) -> str:
        """Create or update the knowledge base."""
        self.kb_id = self._get_knowledge_base_id()

        if self.kb_id:
            logger.info(
                f"Knowledge base '{self.kb_name}' already exists (ID: {self.kb_id})."
            )
            return self.kb_id

        # Ensure the OpenSearch index exists before creating the knowledge base
        if hasattr(self, "aoss_client"):
            index_created = self._ensure_opensearch_index_exists()
            if not index_created:
                logger.error(
                    "Could not create OpenSearch index, knowledge base creation will fail"
                )
                raise ValueError("Failed to create required OpenSearch index")

        logger.info(f"Creating knowledge base '{self.kb_name}'...")

        # Build the base configuration for the knowledge base
        kb_config = {
            "name": self.config.get("name"),
            "roleArn": self.config.get("roleArn"),
        }

        # Only add description if provided and not empty
        if self.config.get("description"):
            kb_config["description"] = self.config.get("description")

        try:
            # Set required knowledgeBaseConfiguration
            if "knowledgeBaseConfiguration" in self.config:
                kb_config["knowledgeBaseConfiguration"] = self.config[
                    "knowledgeBaseConfiguration"
                ]
            else:
                # Fallback: build a minimal configuration
                embedding_model_arn = self.config.get("embeddingModelArn")
                if not embedding_model_arn:
                    raise ValueError(
                        "Either 'knowledgeBaseConfiguration' or 'embeddingModelArn' must be provided."
                    )
                kb_config["knowledgeBaseConfiguration"] = {
                    "type": "VECTOR",
                    "vectorKnowledgeBaseConfiguration": {
                        "embeddingModelArn": embedding_model_arn,
                        "embeddingModelConfiguration": {
                            "bedrockEmbeddingModelConfiguration": {
                                "embeddingDataType": "FLOAT32",
                            }
                        },
                    },
                }
                # Optionally add supplementalDataStorageConfiguration
                if "supplementalDataStorageConfiguration" in self.config:
                    kb_config["knowledgeBaseConfiguration"][
                        "vectorKnowledgeBaseConfiguration"
                    ]["supplementalDataStorageConfiguration"] = self.config[
                        "supplementalDataStorageConfiguration"
                    ]

            # Include storageConfiguration
            if "storageConfiguration" in self.config:
                kb_config["storageConfiguration"] = self.config["storageConfiguration"]
            else:
                # Default to OpenSearch Serverless with required parameters
                collection_arn = self.config.get("opensearchCollectionArn")
                vector_index_name = self.config.get(
                    "vectorIndexName", "bedrock-kb-index"
                )

                if not collection_arn:
                    raise ValueError(
                        "A valid 'opensearchCollectionArn' is required for the OpenSearch Serverless configuration."
                    )

                kb_config["storageConfiguration"] = {
                    "type": "OPENSEARCH_SERVERLESS",
                    "opensearchServerlessConfiguration": {
                        "collectionArn": collection_arn,
                        "vectorIndexName": vector_index_name,
                        "fieldMapping": {
                            "vectorField": self.config.get(
                                "vectorField", "bedrock_embedding"
                            ),
                            "textField": self.config.get("textField", "content"),
                            "metadataField": self.config.get(
                                "metadataField", "metadata"
                            ),
                        },
                    },
                }

            # Pass optional fields if present
            if "clientToken" in self.config:
                kb_config["clientToken"] = self.config["clientToken"]
            if "tags" in self.config:
                kb_config["tags"] = self.config["tags"]

            logger.info(
                f"Knowledge base configuration:\n{json.dumps(kb_config, indent=2)}"
            )

            # Create the knowledge base
            response = self.bedrock_agent.create_knowledge_base(**kb_config)

            self.kb_id = response.get("knowledgeBase", {}).get("knowledgeBaseId")
            logger.info(f"Knowledge base created successfully with ID: {self.kb_id}")

            # Wait for the knowledge base to become active
            self._wait_for_kb_active()

            return self.kb_id

        except ClientError as e:
            logger.error(f"Failed to create knowledge base: {e}")
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_message = e.response.get("Error", {}).get(
                "Message", "No error message"
            )
            logger.error(f"Error code: {error_code}")
            logger.error(f"Error message: {error_message}")
            logger.error(f"Attempted configuration:\n{json.dumps(kb_config, indent=2)}")
            raise

    def query(self, query_text: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Query the knowledge base with the given text."""
        if not self.kb_id:
            self.kb_id = self._get_knowledge_base_id()
            if not self.kb_id:
                raise ValueError(f"Knowledge base '{self.kb_name}' not found")

        logger.info(f"Querying knowledge base '{self.kb_name}' (ID: {self.kb_id})")

        # Default parameters
        params = {
            "retrievalConfiguration": {
                "vectorSearchConfiguration": {
                    "numberOfResults": 5,
                }
            }
        }

        # Override with user parameters if provided
        if parameters:
            if "numberOfResults" in parameters:
                params["retrievalConfiguration"]["vectorSearchConfiguration"][
                    "numberOfResults"
                ] = parameters["numberOfResults"]
            if "filter" in parameters:
                params["retrievalConfiguration"]["vectorSearchConfiguration"][
                    "filter"
                ] = parameters["filter"]

        try:
            response = self.bedrock_agent_runtime.retrieve(
                knowledgeBaseId=self.kb_id,
                retrievalQuery={"text": query_text},
                **params,
            )

            logger.info(
                f"Query successful with {len(response.get('retrievalResults', []))} results"
            )
            return response

        except ClientError as e:
            logger.error(f"Failed to query knowledge base: {e}")
            raise

    def _get_knowledge_base_id(self) -> Optional[str]:
        """Get the ID of an existing knowledge base with the same name."""
        try:
            paginator = self.bedrock_agent.get_paginator("list_knowledge_bases")

            for page in paginator.paginate():
                for kb in page.get("knowledgeBases", []):
                    if kb.get("name") == self.kb_name:
                        return kb.get("knowledgeBaseId")

            return None

        except ClientError as e:
            logger.error(f"Failed to list knowledge bases: {e}")
            return None

    def _wait_for_kb_active(self) -> None:
        """Wait for the knowledge base to reach ACTIVE status."""
        if not self.kb_id:
            logger.warning("No knowledge base ID available to check status")
            return

        logger.info(f"Waiting for knowledge base {self.kb_id} to become active...")
        max_attempts = 30
        sleep_time = 10

        for attempt in range(max_attempts):
            try:
                response = self.bedrock_agent.get_knowledge_base(
                    knowledgeBaseId=self.kb_id
                )
                status = response.get("knowledgeBase", {}).get("status")

                if status == "ACTIVE":
                    logger.info(f"Knowledge base {self.kb_id} is now active")
                    return
                elif status in ["FAILED", "DELETING", "DELETED"]:
                    logger.error(f"Knowledge base entered terminal state: {status}")
                    raise Exception(f"Knowledge base failed to become active: {status}")

                logger.info(
                    f"Knowledge base status: {status} (attempt {attempt+1}/{max_attempts})"
                )
                time.sleep(sleep_time)

            except ClientError as e:
                logger.error(f"Error checking knowledge base status: {e}")
                time.sleep(sleep_time)

        logger.warning(f"Timed out waiting for knowledge base to become active")


class LambdaTaskExecutor:
    """Executes tasks using AWS Lambda functions."""

    def __init__(self, context: PipelineContext):
        self.context = context
        self.lambda_client = boto3.client("lambda")

    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Execute a task using AWS Lambda."""
        task_id = task.get("id")
        assert task_id, "Task ID must be specified"

        lambda_function = task.get("lambda_function")
        assert lambda_function, "Lambda function ARN/name must be specified"

        parameters = task.get("parameters", {})
        expected_outputs = task.get("outputs", {})

        logger.info(f"Executing task {task_id} using Lambda function {lambda_function}")

        # Resolve parameters (substitute references to other task outputs)
        resolved_params = self.context.resolve_parameters(parameters)

        # Register the task in the context
        self.context.current_task_id = task_id
        self.context.register_task(
            task_id,
            {
                "id": task_id,
                "lambda_function": lambda_function,
                "parameters": resolved_params,
                "outputs": {},
                "status": "running",
            },
        )

        try:
            start_time = time.time()

            # Prepare Lambda payload
            payload = json.dumps(resolved_params)

            # Invoke Lambda function
            logger.info(f"Invoking Lambda function: {lambda_function}")
            response = self.lambda_client.invoke(
                FunctionName=lambda_function,
                InvocationType="RequestResponse",  # Synchronous execution
                Payload=payload,
            )

            # Check for Lambda execution errors
            status_code = response.get("StatusCode")
            if status_code != 200:
                raise Exception(
                    f"Lambda invocation failed with status code: {status_code}"
                )

            # Process Lambda response
            response_payload = json.loads(
                response.get("Payload").read().decode("utf-8")
            )

            # Check for function errors
            if "FunctionError" in response:
                error_type = response_payload.get("errorType", "Unknown")
                error_message = response_payload.get("errorMessage", "No error message")
                raise Exception(
                    f"Lambda function error ({error_type}): {error_message}"
                )

            # Save outputs to files if requested
            self._save_outputs(task_id, response_payload, expected_outputs)

            execution_time = time.time() - start_time

            # Update task status
            self.context.tasks[task_id]["status"] = "completed"
            self.context.tasks[task_id]["execution_time"] = execution_time
            self.context.tasks[task_id]["response"] = response_payload

            logger.info(
                f"Task {task_id} completed successfully in {execution_time:.2f}s"
            )
            return True

        except Exception as e:
            self.context.tasks[task_id]["status"] = "failed"
            self.context.tasks[task_id]["error"] = {"message": str(e)}
            logger.error(f"Task {task_id} failed: {str(e)}")
            return False

    def _save_outputs(
        self,
        task_id: str,
        response_payload: Dict[str, Any],
        expected_outputs: Dict[str, str],
    ) -> None:
        """Process response payload and save outputs."""
        # Register all response fields as outputs in the context
        for key, value in response_payload.items():
            self.context.register_task_output(task_id, key, value)

        # Save to expected output files if specified
        for output_name, output_path in expected_outputs.items():
            # Resolve the output value
            if output_name in response_payload:
                output_value = response_payload[output_name]
            else:
                logger.warning(f"Output '{output_name}' not found in Lambda response")
                continue

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            # Save the output to file
            with open(output_path, "w") as f:
                if isinstance(output_value, (dict, list)):
                    json.dump(output_value, f, indent=2)
                else:
                    f.write(str(output_value))

            logger.info(f"Saved output '{output_name}' to {output_path}")


class KnowledgeBaseTaskExecutor:
    """Executes tasks using AWS Bedrock Knowledge Base."""

    def __init__(
        self, context: PipelineContext, knowledge_bases: Dict[str, BedrockKnowledgeBase]
    ):
        self.context = context
        self.knowledge_bases = knowledge_bases

    def execute_task(self, task: Dict[str, Any]) -> bool:
        """Execute a task using AWS Bedrock Knowledge Base."""
        task_id = task.get("id")
        assert task_id, "Task ID must be specified"

        kb_name = task.get("knowledge_base")
        assert kb_name, "Knowledge base name must be specified"

        # Make sure the knowledge base exists
        if kb_name not in self.knowledge_bases:
            logger.error(f"Knowledge base '{kb_name}' not found")
            return False

        kb = self.knowledge_bases[kb_name]

        if kb is None:
            logger.error(
                f"Knowledge base '{kb_name}' failed to be created earlier. Cannot execute task."
            )
            return False

        query = task.get("query")
        assert query, "Query must be specified for knowledge base task"

        parameters = task.get("parameters", {})
        expected_outputs = task.get("outputs", {})

        logger.info(f"Executing task {task_id} using knowledge base {kb_name}")

        # Resolve parameters (substitute references to other task outputs)
        resolved_params = self.context.resolve_parameters(parameters)
        resolved_query = self.context.resolve_parameter(query)

        # Register the task in the context
        self.context.current_task_id = task_id
        self.context.register_task(
            task_id,
            {
                "id": task_id,
                "knowledge_base": kb_name,
                "query": resolved_query,
                "parameters": resolved_params,
                "outputs": {},
                "status": "running",
            },
        )

        try:
            start_time = time.time()

            # Query the knowledge base
            response = kb.query(resolved_query, resolved_params)

            # Save outputs to files if requested
            self._save_outputs(task_id, response, expected_outputs)

            execution_time = time.time() - start_time

            # Update task status
            self.context.tasks[task_id]["status"] = "completed"
            self.context.tasks[task_id]["execution_time"] = execution_time
            self.context.tasks[task_id]["response"] = response

            logger.info(
                f"Task {task_id} completed successfully in {execution_time:.2f}s"
            )
            return True

        except Exception as e:
            self.context.tasks[task_id]["status"] = "failed"
            self.context.tasks[task_id]["error"] = {"message": str(e)}
            logger.error(f"Task {task_id} failed: {str(e)}")
            return False

    def _save_outputs(
        self, task_id: str, response: Dict[str, Any], expected_outputs: Dict[str, str]
    ) -> None:
        """Process response and save outputs."""
        # Register the retrieval results as an output in the context
        self.context.register_task_output(
            task_id, "retrievalResults", response.get("retrievalResults", [])
        )

        # Register additional response fields
        for key, value in response.items():
            if key != "retrievalResults":
                self.context.register_task_output(task_id, key, value)

        # Save to expected output files if specified
        for output_name, output_path in expected_outputs.items():
            # Determine what to save based on the output name
            if output_name == "retrievalResults":
                output_value = response.get("retrievalResults", [])
            elif output_name in response:
                output_value = response[output_name]
            else:
                logger.warning(
                    f"Output '{output_name}' not found in knowledge base response"
                )
                continue

            # Ensure directory exists
            os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

            # Save the output to file
            with open(output_path, "w") as f:
                if isinstance(output_value, (dict, list)):
                    json.dump(output_value, f, indent=2)
                else:
                    f.write(str(output_value))

            logger.info(f"Saved output '{output_name}' to {output_path}")


def load_and_validate_config(json_file: str) -> Dict[str, Any]:
    """Load and validate the JSON configuration file."""
    try:
        with open(json_file, "r") as f:
            config = json.load(f)

        # Validate knowledge base configurations if present
        if "knowledge_bases" in config:
            for kb_name, kb_config in config["knowledge_bases"].items():
                if not kb_config.get("name"):
                    kb_config["name"] = kb_name
                if "roleArn" not in kb_config:
                    logger.warning(f"Knowledge base {kb_name} is missing roleArn")

        # Validate tasks
        if "tasks" not in config or not config["tasks"]:
            logger.error("No tasks defined in configuration")
            raise ValueError("Configuration must contain at least one task")

        for i, task in enumerate(config["tasks"]):
            if not task.get("id"):
                logger.error(f"Task at index {i} is missing an id")
                raise ValueError(f"Task at index {i} is missing an id")

            # Check task type and required parameters
            if "lambda_function" in task:
                pass  # Lambda function name is already checked
            elif "knowledge_base" in task:
                if not task.get("query"):
                    logger.error(
                        f"Knowledge base task {task.get('id')} is missing query"
                    )
                    raise ValueError(
                        f"Knowledge base task {task.get('id')} is missing query"
                    )

                kb_name = task.get("knowledge_base")
                if (
                    "knowledge_bases" not in config
                    or kb_name not in config["knowledge_bases"]
                ):
                    logger.error(
                        f"Referenced knowledge base '{kb_name}' is not defined"
                    )
                    raise ValueError(
                        f"Referenced knowledge base '{kb_name}' is not defined"
                    )
            else:
                logger.error(
                    f"Task {task.get('id')} must specify either 'lambda_function' or 'knowledge_base'"
                )
                raise ValueError(
                    f"Task {task.get('id')} must specify either 'lambda_function' or 'knowledge_base'"
                )

        return config

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON file: {e}")
        raise
    except FileNotFoundError:
        logger.error(f"File not found: {json_file}")
        raise


def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="AWS pipeline orchestrator for Lambda functions and Bedrock Knowledge Bases."
    )
    parser.add_argument("json_file", help="Path to the JSON configuration file")
    parser.add_argument(
        "--skip-kb", action="store_true", help="Skip knowledge base creation"
    )
    args = parser.parse_args()

    try:
        # Load and validate configuration
        config = load_and_validate_config(args.json_file)

        # Initialize pipeline context
        context = PipelineContext()

        # Initialize knowledge bases
        knowledge_bases = {}
        if "knowledge_bases" in config and not args.skip_kb:
            for kb_name, kb_config in config["knowledge_bases"].items():
                try:
                    kb = BedrockKnowledgeBase(kb_config)
                    kb_id = kb.create_or_update()
                    knowledge_bases[kb_name] = kb
                    logger.info(f"Using knowledge base '{kb_name}' (ID: {kb_id})")
                except Exception as e:
                    error_msg = str(e)
                    logger.error(
                        f"Failed to create knowledge base '{kb_name}': {error_msg}"
                    )

                    # Report the error more clearly
                    if (
                        "no such index" in error_msg.lower()
                        or "index not found" in error_msg.lower()
                    ):
                        logger.error(
                            "OpenSearch index error: The required index is missing."
                        )
                    elif "Bad Authorization" in error_msg or "403" in error_msg:
                        logger.error(
                            "Authorization error: The IAM role doesn't have sufficient permissions."
                        )
                    elif "ValidationException" in error_msg:
                        logger.error("Validation error when creating knowledge base.")
                    elif "AccessDeniedException" in error_msg:
                        logger.error("Access denied error. Check IAM permissions.")
                    else:
                        logger.error(f"Knowledge base creation failed: {error_msg}")

                    # Knowledge base creation is critical - exit with error
                    logger.error(
                        f"Stopping execution - knowledge base '{kb_name}' is required but could not be created"
                    )
                    return 1

        # Initialize task executors
        lambda_executor = LambdaTaskExecutor(context)
        kb_executor = KnowledgeBaseTaskExecutor(context, knowledge_bases)

        # Execute tasks sequentially
        task_success = True

        for task in config["tasks"]:
            if not task_success:
                logger.warning(
                    f"Skipping task {task.get('id')} due to previous failure"
                )
                continue

            # Choose the appropriate executor based on task type
            if "lambda_function" in task:
                task_success = lambda_executor.execute_task(task)
            elif "knowledge_base" in task:
                task_success = kb_executor.execute_task(task)
            else:
                logger.error(f"Unknown task type for task {task.get('id')}")
                task_success = False

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

    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
