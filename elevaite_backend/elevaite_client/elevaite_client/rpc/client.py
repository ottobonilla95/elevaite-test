#!/usr/bin/env python
import json
import logging
import os
from typing import Any, Dict, List, Union
import pika
import uuid

from ..connectors.embeddings.core.interfaces import (
    EmbeddingRequest,
    EmbeddingResponse,
    EmbeddingType,
)
from ..connectors.embeddings.bedrock import BedrockEmbeddingProvider
from ..connectors.embeddings.core.class import BaseEmbeddingProvider
from ..connectors.embeddings.onprem import OnPremLLMEmbeddingProvider
from ..connectors.embeddings.openai import OpenAIEmbeddingProvider
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


class EmbeddingRPCService:
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

        # Dynamically initialize providers based on available configurations
        self.providers: Dict[EmbeddingType, BaseEmbeddingProvider] = (
            self._initialize_providers()
        )

    def _initialize_providers(self) -> Dict[EmbeddingType, BaseEmbeddingProvider]:
        providers = {}

        openai_api_key = os.getenv("OPENAI_API_KEY")
        if openai_api_key:
            providers[EmbeddingType.OPENAI] = OpenAIEmbeddingProvider(
                api_key=openai_api_key
            )

        bedrock_region = os.getenv("BEDROCK_REGION")
        if bedrock_region:
            providers[EmbeddingType.BEDROCK] = BedrockEmbeddingProvider(
                aws_region=bedrock_region
            )

        onprem_model_path = os.getenv("ONPREM_MODEL_PATH")
        if onprem_model_path:
            providers[EmbeddingType.ON_PREM] = OnPremLLMEmbeddingProvider(
                model_path=onprem_model_path
            )

        if not providers:
            raise EnvironmentError("No valid embedding providers configured")

        return providers

    def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        try:
            # Select the provider based on the request type
            provider = self.providers.get(request.info.type)
            if not provider:
                raise ValueError(f"No provider available for type {request.info.type}")

            vectors = provider.embed_documents(request.texts, request.info)

            return EmbeddingResponse(vectors=vectors, metadata=request.metadata)

        except ValueError as ve:
            self.logger.error(f"Validation error: {ve}")
            raise ve
        except Exception as e:
            self.logger.error(f"Embedding failed: {e}")
            raise RuntimeError(f"Embedding service encountered an error: {e}")


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
