import asyncio
import signal
import sys

import environs
from confluent_kafka import Producer

from . import __version__
from .config import parse_config
from .logger import log, producer_log
from .monitor import monitor
from .producer import kafka_producer


async def main():
    # Get Config
    try:
        conf = parse_config()
    except environs.EnvValidationError as err:
        log.error(error=err)
        sys.exit(1)

    # Start
    log.info(
        bin=sys.argv[0],
        version=__version__,
        config=conf,
    )

    # Instantiate Kafka producer
    # Configuration options:
    # https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    kafka_client = Producer(
        # XXX: production setup should communicate via SSL
        {
            "bootstrap.servers": conf.kafka_broker_list,
            "retries": conf.producer_retries,
        },
        logger=producer_log,
    )

    # Implement producer-consumer pattern, where monitors are producers and
    # kafka_producer is actually a consumer for monitoring data
    queue = asyncio.Queue()
    monitors = asyncio.create_task(monitor(conf, queue, logger=log))
    asyncio.create_task(kafka_producer(kafka_client, conf, queue))
    await asyncio.gather(monitors)


def run():
    # Handle Ctrl+C
    # TODO: handle SIGHUP?
    signal.signal(signal.SIGINT, lambda signal, frame: sys.exit(0))
    asyncio.run(main())
