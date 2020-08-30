import json
import signal
import sys
import time

import backoff
import environs
import requests
from confluent_kafka import Producer

from . import __version__
from .config import parse_config
from .logger import log, producer_log
from .ping import backoff_handler, ping
from .producer import ack_handler


def run():
    # Handle Ctrl+C
    # TODO: handle SIGHUP?
    signal.signal(signal.SIGINT, lambda signal, frame: sys.exit(0))

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

    # Configure exponential backoff without jitter;
    # no competing clients, as described here:
    # https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    backoff_deco = backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        on_backoff=backoff_handler,
        max_tries=conf.backoff_retries,
        jitter=None,
    )

    # Instantiate Kafka producer
    # Configuration options:
    # https://github.com/edenhill/librdkafka/blob/master/CONFIGURATION.md
    producer = Producer(
        # XXX: production setup should communicate via SSL
        {
            "bootstrap.servers": conf.kafka_broker_list,
            "retries": conf.producer_retries,
        },
        logger=producer_log,
    )

    # Main loop
    while True:
        # Ping webpage
        #
        try:
            http_code, resp_time = backoff_deco(ping)(
                conf.page_url, conf.conn_timeout, conf.read_timeout
            )
            log.info("metrics", http_code=http_code, response_time=resp_time)
        # RequestException is a parent for all requests.exceptions
        except requests.exceptions.RequestException as err:
            log.error(error=err)
            sys.exit(1)

        # Compose Kafka message
        #
        msg = {
            # Following xkcd.com/1179, sorry ISO 8601
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "page_url": conf.page_url,
            "http_code": http_code,
            "response_time": resp_time.microseconds,
        }

        # Write monit data into Kafka synchronously
        #
        log.info("producing record", record=msg)
        # https://docs.confluent.io/current/clients/confluent-kafka-python/index.html#confluent_kafka.Producer.produce

        # TODO: connection failures should not block page pings
        # TODO: write with key specifying page_url
        producer.produce(
            conf.kafka_topic, json.dumps(msg), on_delivery=ack_handler
        )
        producer.flush()  # calls poll() automatically

        time.sleep(conf.ping_interval)
