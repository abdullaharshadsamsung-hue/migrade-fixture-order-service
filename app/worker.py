"""Background worker: confirms each new order and records it in the audit log."""

import json
import time

import pika
from sqlalchemy import update

from app import audit, config
from app.db import Session, init_db
from app.models import Order


def handle(body: bytes) -> None:
    message = json.loads(body)
    if message.get("event") != "order.created":
        return
    order_id = message["order_id"]
    with Session() as db:
        # One atomic pending -> confirmed: a redelivered event, or two
        # workers, confirm and audit an order once.
        confirmed = db.execute(
            update(Order)
            .where(Order.id == order_id, Order.status == "pending")
            .values(status="confirmed")
        ).rowcount
        db.commit()
    if confirmed:
        audit.record(order_id, "confirmed")


def main() -> None:
    init_db()
    while True:
        try:
            connection = pika.BlockingConnection(pika.URLParameters(config.AMQP_URL))
            channel = connection.channel()
            channel.queue_declare(queue=config.ORDER_EVENTS_QUEUE, durable=True)

            def on_message(ch, method, _properties, body):
                handle(body)
                ch.basic_ack(delivery_tag=method.delivery_tag)

            channel.basic_consume(queue=config.ORDER_EVENTS_QUEUE, on_message_callback=on_message)
            print("worker: waiting for order events", flush=True)
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError:
            time.sleep(2)


if __name__ == "__main__":
    main()
