import json
from asyncio import Queue

from confluent_kafka import Producer

from .config import DotDict


def _ack_handler(err, msg) -> None:
    """Delivery report handler.

    Called on successful or failed delivery of message.
    Used as callback by confluent_kafka.Producer.

    """
    if err:
        msg = {
            "event": "failed to deilver message",
            "error": err,
        }
    else:
        msg = {
            "event": "record produced",
            "topic": msg.topic(),
            "partition": msg.partition(),
            "offset": msg.offset(),
        }
    print(json.dumps(msg))


async def kafka_producer(
    client: Producer, conf: DotDict, queue: Queue
) -> None:
    """Async producer for Kafka.

    Pulls messages from queue.

    """
    while True:
        msg = await queue.get()
        client.produce(
            conf.kafka_topic,
            key=conf.page_url,
            value=json.dumps(msg),
            on_delivery=_ack_handler,
        )
        client.poll(0)
        queue.task_done()
