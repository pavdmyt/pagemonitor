import signal
import sys
import time

import backoff
import environs
import requests

from .config import parse_config
from .logger import log
from .ping import backoff_handler, ping


__version__ = "0.1.0"


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

    # Main loop
    while True:
        try:
            http_code, resp_time = backoff_deco(ping)(
                conf.page_url, conf.conn_timeout, conf.read_timeout
            )
            log.info("metrics", http_code=http_code, response_time=resp_time)
        # RequestException is a parent for all requests.exceptions
        except requests.exceptions.RequestException as err:
            log.error(error=err)
            sys.exit(1)

        # Write monit data into Kafka
        #

        time.sleep(conf.ping_interval)
