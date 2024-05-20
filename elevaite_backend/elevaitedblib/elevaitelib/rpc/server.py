#!/usr/bin/env python
import json
import os
import threading
from typing import Any, Callable
from dotenv import load_dotenv
import pika
import pika.spec
from elevaite_client.rpc.connection import get_rmq_connection
from elevaite_client.rpc.constants import EXCHANGE_NAME


class RPCServer:
    def bind_and_consume(self, routing_key: str, func: Callable[[Any], str | None]):
        t = threading.Thread(target=self._bind_and_consume, args=(routing_key, func))
        t.start()

    def _bind_and_consume(self, routing_key: str, func: Callable[[Any], str | None]):
        channel = get_rmq_connection().channel()

        channel.exchange_declare(exchange=EXCHANGE_NAME, exchange_type="topic")
        _res = channel.queue_declare(queue="", exclusive=True)
        queue_name = _res.method.queue
        channel.queue_bind(
            exchange=EXCHANGE_NAME, queue=queue_name, routing_key=routing_key
        )

        def on_request(
            ch,
            method: pika.spec.Basic.Deliver,
            props: pika.spec.BasicProperties,
            body,
        ):
            _data = json.loads(body)
            print("  [o] Received: ")
            print(body)
            response = func(_data)
            print("  [o] Responding: ")
            print(response)

            ch.basic_publish(
                exchange="",
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body=response,
            )
            ch.basic_ack(delivery_tag=method.delivery_tag)

        channel.basic_consume(queue=queue_name, on_message_callback=on_request)
        channel.start_consuming()
