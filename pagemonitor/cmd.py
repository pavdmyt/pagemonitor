import signal
import sys
import time

import environs
import requests

from .config import parse_config
from .logger import log


__version__ = "0.1.0"


# TODO: add type annotations
def ping(url, conn_timeout=4, read_timeout=3):
    resp = requests.head(url, timeout=(conn_timeout, read_timeout))
    return resp.status_code, resp.elapsed


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

    # Main loop
    while True:
        try:
            http_code, resp_time = ping(
                conf.page_url, conf.conn_timeout, conf.read_timeout
            )
            log.info("metrics", http_code=http_code, response_time=resp_time)
        # RequestException is a parent for all requests.exceptions
        except requests.exceptions.RequestException as err:
            log.error(error=err)

        # Write monit data into Kafka
        #

        time.sleep(conf.ping_interval)
