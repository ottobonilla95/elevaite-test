from datetime import datetime
import json
from typing import Any, Dict, List, Literal, Optional, cast
import uuid
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_tool_message_param import (
    ChatCompletionToolMessageParam,
)
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

# RabbitMQ imports - commented out for Redis-only implementation
# import pika
# import pika.adapters.blocking_connection
# import pika.channel
# import pika.spec
from pydantic import BaseModel

from .agent_base import Agent
from utils import agent_schema, client
from data_classes import PromptObject

from .tools import tool_store


# RabbitMQ exchange name - commented out for Redis-only implementation
# EXCHANGE_NAME = "agents_exchange"


class ConsolePrinterAgentInput(BaseModel):
    query: str


@agent_schema
class ConsolePrinterAgent(Agent):
    # RabbitMQ-related attributes - commented out for Redis-only implementation
    # connection: pika.BlockingConnection = None
    # channel: pika.adapters.blocking_connection.BlockingChannel = None
    # callback_queue: str = ""
    # response: Optional[str] = None
    # corr_id: Optional[str] = None

    # RabbitMQ-related methods - commented out for Redis-only implementation
    # def bind_and_consume(self, routing_key: str, func: Callable[[Any], str | None]):
    #     t = threading.Thread(target=self._bind_and_consume, args=(routing_key, func))
    #     t.start()
    #
    # def _bind_and_consume(self, routing_key: str, func: Callable[[Any], str | None]):
    #     channel = get_rmq_connection().channel()
    #
    #     channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic")
    #     _res = channel.queue_declare(queue="", exclusive=True)
    #     queue_name = _res.method.queue
    #     channel.queue_bind(
    #         exchange=EXCHANGE_NAME, queue=queue_name, routing_key=routing_key
    #     )
    #
    #     def on_request(
    #         ch,
    #         method: pika.spec.Basic.Deliver,
    #         props: pika.spec.BasicProperties,
    #         body,
    #     ):
    #         _data = json.loads(body)
    #         print(func.__name__)
    #         # print("  [o] Received: ")
    #         # print(body)
    #         response = func(_data)
    #         # print("  [o] Responding: ")
    #         # print(response)
    #
    #         ch.basic_publish(
    #             exchange="",
    #             routing_key=props.reply_to,
    #             properties=pika.BasicProperties(correlation_id=props.correlation_id),
    #             body=response,
    #         )
    #         ch.basic_ack(delivery_tag=method.delivery_tag)
    #
    #     channel.basic_consume(queue=queue_name, on_message_callback=on_request)
    #     channel.start_consuming()
    #
    # def _on_response(self, ch, method, props, body):
    #     if self.corr_id == props.correlation_id:
    #         self.response = body
    #
    # def _publish_request(self, body: str | bytes, routing_key: str):
    #     self.corr_id = str(uuid.uuid4())
    #     self.channel.basic_publish(
    #         exchange=EXCHANGE_NAME,
    #         routing_key=routing_key,
    #         properties=pika.BasicProperties(
    #             reply_to=self.callback_queue,
    #             correlation_id=self.corr_id,
    #         ),
    #         body=body,
    #     )

    def __init__(
        self,
        # Agent, Human or Parent Agent
        failure_strategies: Optional[List[str]],
        name: str,
        agent_id: uuid.UUID,
        system_prompt: PromptObject,
        persona: Optional[str],
        functions: List[ChatCompletionToolParam],
        routing_options: Dict[str, str],
        parent_agent: Optional[uuid.UUID] = None,
        short_term_memory: bool = False,
        long_term_memory: bool = False,
        reasoning: bool = False,
        input_type: Optional[List[Literal["text", "voice", "image"]]] = [
            "text",
            "voice",
        ],
        output_type: Optional[List[Literal["text", "voice", "image"]]] = [
            "text",
            "voice",
        ],
        response_type: Optional[Literal["json", "yaml", "markdown", "HTML", "None"]] = "json",
        # Execution parameters
        max_retries: int = 3,
        timeout: Optional[int] = None,
        deployed: bool = False,
        status: Literal["active", "paused", "terminated"] = "active",
        priority: Optional[int] = None,
        # Logging and monitoring
        session_id: Optional[str] = None,
        last_active: Optional[datetime] = None,
        # logging_level: Optional[Literal["debug", "info", "warning", "error"]] = "info"  # Debug level
        collaboration_mode: Optional[Literal["single", "team", "parallel", "sequential"]] = "single",  # Multi-agent behavior
    ):
        super().__init__(
            agent_id=agent_id,
            collaboration_mode=collaboration_mode,
            deployed=deployed,
            failure_strategies=failure_strategies,
            functions=functions,
            input_type=input_type,
            last_active=last_active,
            long_term_memory=long_term_memory,
            max_retries=max_retries,
            name=name,
            output_type=output_type,
            parent_agent=parent_agent,
            persona=persona,
            reasoning=reasoning,
            response_type=response_type,
            routing_options=routing_options,
            short_term_memory=short_term_memory,
            session_id=session_id,
            status=status,
            system_prompt=system_prompt,
            timeout=timeout,
            priority=priority,
        )
        # RabbitMQ initialization - commented out for Redis-only implementation
        # self.connection = get_rmq_connection()
        #
        # self.channel = self.connection.channel()
        #
        # result = self.channel.queue_declare(queue="", exclusive=True)
        # self.callback_queue = result.method.queue
        #
        # self.channel.basic_consume(
        #     queue=self.callback_queue,
        #     on_message_callback=self._on_response,
        #     auto_ack=True,
        # )
        #
        # self.response = None
        # self.corr_id = None
        # self.bind_and_consume("console_printer_agent", self._execute)

        # Initialize Redis communication
        self.initialize_redis_communication()

    def _execute(self, payload: Any):
        """
        This agent prints the input to the console.
        """
        query = payload["query"]
        tries = 0
        routing_options = "\n".join([f"{k}: {v}" for k, v in self.routing_options.items()])
        system_prompt = (
            self.system_prompt.prompt
            + f"""
        Here are the routing options:
        {routing_options}

        Your response should be in the format:
        {{ "routing": "respond", "content": "The answer to the query."}}

        """
        )
        messages: List[ChatCompletionMessageParam] = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query},
        ]
        while tries < self.max_retries:
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=self.functions,
                    stream=False,
                )
                if response.choices[0].finish_reason == "tool_calls" and response.choices[0].message.tool_calls is not None:
                    tool_calls = response.choices[0].message.tool_calls
                    messages.append(
                        cast(
                            ChatCompletionMessageParam,
                            {
                                "role": "assistant",
                                "tool_calls": cast(List[ChatCompletionToolMessageParam], tool_calls),
                            },
                        )
                    )
                    for tool in tool_calls:
                        print(tool.function.name)
                        tool_id = tool.id
                        arguments = json.loads(tool.function.arguments)
                        function_name = tool.function.name
                        result = tool_store[function_name](**arguments)
                        print(result)
                        messages.append(
                            cast(
                                ChatCompletionMessageParam,
                                {
                                    "role": "tool",
                                    "tool_call_id": tool_id,
                                    "content": str(result),
                                },
                            )
                        )

                else:
                    return response.choices[0].message.content

            except Exception as e:
                print(f"Error: {e}")
            tries += 1

    def execute(
        self,
        query: str,
        session_id: Optional[str] = None,
        user_id: Optional[str] = None,
        chat_history: Optional[List[Dict[str, Any]]] = None,
        enable_analytics: bool = False,
        **kwargs: Any,
    ) -> str:
        return super().execute(
            query=query,
            session_id=session_id,
            user_id=user_id,
            chat_history=chat_history,
            enable_analytics=enable_analytics,
            **kwargs,
        )
