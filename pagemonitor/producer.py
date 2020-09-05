import json
from asyncio import Queue

from confluent_kafka import Producer

from .config import DotDict
from .logger import producer_log


def new_producer(conf: DotDict) -> Producer:
    """Create pre-configured instance of confluent_kafka.Producer.

    Configuration options:
    https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md

    """
    basic_conf = {
        "bootstrap.servers": conf.kafka_broker_list,
        "retries": conf.producer_retries,
    }
    if conf.kafka_enable_cert_auth:
        auth_conf = {
            "security.protocol": "ssl",
            "ssl.key.location": conf.kafka_ssl_key,
            "ssl.certificate.location": conf.kafka_ssl_cert,
            "ssl.ca.location": conf.kafka_ssl_ca,
        }
        basic_conf.update(auth_conf)
    return Producer(basic_conf, logger=producer_log)


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
