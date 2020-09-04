import asyncio
import signal
import sys

import environs
import httpx
from confluent_kafka import Producer

from .config import parse_config
from .logger import log, producer_log
from .monitor import monitor
from .producer import kafka_producer


__version__ = "0.1.0"


async def main() -> None:
    """Main logic.

    Implements programm's flow.
    """
    # Get Config
    try:
        conf = parse_config()
    except environs.EnvValidationError as err:
        log.error(error=err)
        sys.exit(1)

    # Basic config info
    log.info(
        bin=sys.argv[0],
        version=__version__,
        config=conf,
    )

    # Instantiate Kafka producer
    #

    # Configuration options:
    # https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    client_conf = {
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
        client_conf.update(auth_conf)

    kafka_client = Producer(
        client_conf,
        logger=producer_log,
    )

    # Instantiate HTTP client for monitor
    #
    timeout = httpx.Timeout(connect=conf.conn_timeout, read=conf.read_timeout)
    client = httpx.AsyncClient(timeout=timeout)

    # Implement producer-consumer pattern, where monitors are producers and
    # kafka_producer is actually a consumer for monitoring data
    queue = asyncio.Queue()
    monitors = asyncio.create_task(monitor(client, conf, queue, logger=log))
    asyncio.create_task(kafka_producer(kafka_client, conf, queue))
    await asyncio.gather(monitors)


def run() -> None:
    """Entry point for the built executable."""
    # TODO: signals should be registered on event loop, with proper handling
    #       for each of them.
    # Temporary solution.
    signal.signal(signal.SIGINT, lambda signal, frame: sys.exit(0))

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except asyncio.exceptions.CancelledError:
        print({"error": "tasks has been cancelled"})
    finally:
        loop.close()
