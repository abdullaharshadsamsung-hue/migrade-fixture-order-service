"""Order events published to RabbitMQ."""

import json

import pika

from app import config


def publish(event: str, payload: dict) -> None:
    connection = pika.BlockingConnection(pika.URLParameters(config.AMQP_URL))
    try:
        channel = connection.channel()
        channel.queue_declare(queue=config.ORDER_EVENTS_QUEUE, durable=True)
        channel.basic_publish(
            exchange="",
            routing_key=config.ORDER_EVENTS_QUEUE,
            body=json.dumps({"event": event, **payload}),
            properties=pika.BasicProperties(delivery_mode=2),
        )
    finally:
        connection.close()
