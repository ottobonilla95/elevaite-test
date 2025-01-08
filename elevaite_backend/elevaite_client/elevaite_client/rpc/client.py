#!/usr/bin/env python
import json
import logging
import os
import pika
import uuid
from typing import Any, Dict, List, Union


from ..connectors import embeddings
from ..connectors import text_generation
from ..connectors.embeddings.core.abstract import BaseEmbeddingProvider
from ..connectors.text_generation.core.abstract import BaseTextGenerationProvider
from ..connectors.text_generation.core.interfaces import TextGenerationType
from ..connectors.embeddings.core.interfaces import (
    EmbeddingType,
    EmbeddingRequest,
    EmbeddingResponse,
)
from .constants import EXCHANGE_NAME, RPCRoutingKeys
from .connection import get_rmq_connection
from .interfaces import (
    CreateDatasetVersionInput,
    GetCollectionNameInput,
    GetDatasetVersionCommitIdInput,
    LogInfo,
    MaxDatasetVersionInput,
    PipelineStepStatusInput,
    RegisterPipelineInput,
    RepoNameInput,
    SetInstanceChartDataInput,
    SetRedisStatsInput,
    SetRedisValueInput,
)


class ModelProviderFactory:
    """Factory to initialize and manage providers for various tasks."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.providers: Dict[
            str, Union[BaseEmbeddingProvider, BaseTextGenerationProvider]
        ] = {}
        self._initialize_providers()

    def _initialize_providers(self):
        if openai_api_key := os.getenv("OPENAI_API_KEY"):
            self.providers[EmbeddingType.OPENAI] = (
                embeddings.openai.OpenAIEmbeddingProvider(api_key=openai_api_key)
            )
            self.providers[TextGenerationType.OPENAI] = (
                text_generation.openai.OpenAITextGenerationProvider(
                    api_key=openai_api_key
                )
            )

        if bedrock_region := os.getenv("BEDROCK_REGION"):
            self.providers[EmbeddingType.BEDROCK] = (
                embeddings.bedrock.BedrockEmbeddingProvider(aws_region=bedrock_region)
            )
            self.providers[TextGenerationType.BEDROCK] = (
                embeddings.bedrock.BedrockEmbeddingProvider(aws_region=bedrock_region)
            )

        if onprem_model_path := os.getenv("ONPREM_MODEL_PATH"):
            self.providers[EmbeddingType.ON_PREM] = (
                embeddings.onprem.OnPremEmbeddingProvider(model_path=onprem_model_path)
            )
            self.providers[TextGenerationType.ON_PREM] = (
                embeddings.onprem.OnPremEmbeddingProvider(model_path=onprem_model_path)
            )

        if gemini_api_key := os.getenv("GEMINI_API_KEY"):
            self.providers[EmbeddingType.GEMINI] = (
                embeddings.gemini.GeminiEmbeddingProvider(api_key=gemini_api_key)
            )
            self.providers[TextGenerationType.GEMINI] = (
                text_generation.gemini.GoogleGeminiTextGenerationProvider(
                    api_key=gemini_api_key
                )
            )

        if not self.providers:
            raise EnvironmentError("No valid providers configured")

    def get_provider(self, task_type: str):
        provider = self.providers.get(task_type)
        if not provider:
            raise ValueError(f"No provider available for type {task_type}")
        return provider


class EmbeddingService:
    """Service class to handle embedding requests."""

    def __init__(self, factory: ModelProviderFactory):
        self.factory = factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        provider = self.factory.get_provider(request.info.type)

        try:
            if isinstance(provider, BaseTextGenerationProvider):
                raise TypeError
            vectors = provider.embed_documents(request.texts, request.info)
            return EmbeddingResponse(vectors=vectors, metadata=request.metadata)
        except Exception as e:
            error_msg = f"Error in embedding for provider {request.info.type}: {str(e)}"
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


class TextGenerationService:
    """Service class to handle text generation requests."""

    def __init__(self, factory: ModelProviderFactory):
        self.factory = factory
        self.logger = logging.getLogger(self.__class__.__name__)

    def generate_text(self, prompt: str, config: Dict[str, Any]) -> str:
        provider = self.factory.get_provider(config.get("type") or "")

        try:
            if isinstance(provider, BaseEmbeddingProvider):
                raise TypeError
            return provider.generate_text(prompt, config)
        except Exception as e:
            error_msg = (
                f"Error in text generation for provider {config.get('type')}: {str(e)}"
            )
            self.logger.error(error_msg)
            raise RuntimeError(error_msg)


class RPCClient(object):

    def __init__(self):
        self.connection = get_rmq_connection()

        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue="", exclusive=True)
        self.callback_queue = result.method.queue

        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self._on_response,
            auto_ack=True,
        )

        self.response = None
        self.corr_id = None

    def _on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            self.response = body

    def _publish_request(self, body: str | bytes, routing_key: RPCRoutingKeys):
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange=EXCHANGE_NAME,
            routing_key=routing_key,
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id,
            ),
            body=body,
        )

    def hello(self, o: Dict[str, Any]):
        self.response = None
        self._publish_request(json.dumps(o), RPCRoutingKeys.hello)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return json.loads(self.response)

    def get_repo_name(self, input: RepoNameInput) -> str:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.get_repo_name)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return str(self.response, "utf-8")

    def set_pipeline_step_running(self, input: PipelineStepStatusInput) -> None:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.set_pipeline_step_running)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return

    def set_redis_stats(self, input: SetRedisStatsInput) -> None:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.set_redis_stats)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return

    def set_redis_value(self, input: SetRedisValueInput) -> None:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.set_redis_value)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return

    def set_instance_chart_data(self, input: SetInstanceChartDataInput) -> None:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.set_instance_chart_data)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return

    def set_pipeline_step_completed(self, input: PipelineStepStatusInput) -> None:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.set_pipeline_step_completed)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return

    def get_max_version_of_dataset(self, input: MaxDatasetVersionInput) -> int:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.get_max_version_of_dataset)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return int(self.response)

    def create_dataset_version(self, input: CreateDatasetVersionInput) -> int:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.create_dataset_version)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return int(self.response)

    def log_info(self, log: LogInfo) -> str:
        self.response = None
        self._publish_request(log.json(), RPCRoutingKeys.log_info)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return str(self.response, "utf-8")

    def log_error(self, log: LogInfo) -> str:
        self.response = None
        self._publish_request(log.json(), RPCRoutingKeys.log_error)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return str(self.response, "utf-8")

    def get_dataset_version_commit_id(
        self, input: GetDatasetVersionCommitIdInput
    ) -> str:
        self.response = None
        self._publish_request(
            input.json(), RPCRoutingKeys.get_dataset_version_commit_id
        )
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return str(self.response, "utf-8")

    def get_collection_name(self, input: GetCollectionNameInput) -> str:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.get_collection_name)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return str(self.response, "utf-8")

    def register_experiment(self, input: RegisterPipelineInput) -> str:
        self.response = None
        self._publish_request(input.json(), RPCRoutingKeys.register_experiment)
        while self.response is None:
            self.connection.process_data_events(time_limit=0)
        return str(self.response, "utf-8")


class RedisRPCHelper:
    key: str
    client: RPCClient

    def __init__(self, key: str, client: RPCClient) -> None:
        self.key = key
        self.client = client

    def set_value(
        self,
        path: str,
        obj: Union[str, int, float, bool, None, Dict[str, Any], List[Any]],
    ) -> None:
        return self.client.set_redis_value(
            input=SetRedisValueInput(name=self.key, path=path, obj=obj)
        )


class RPCLogger:
    key: str
    client: RPCClient

    def __init__(self, key: str, client: RPCClient) -> None:
        self.key = key
        self.client = client

    def info(self, msg: str) -> str:
        return self.client.log_info(log=LogInfo(key=self.key, msg=msg))

    def error(self, msg: str) -> str:
        return self.client.log_error(log=LogInfo(key=self.key, msg=msg))
