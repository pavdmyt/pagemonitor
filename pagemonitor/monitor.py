import asyncio
import json
import sys
import time

import backoff
import requests


def _ping(url, conn_timeout=4, read_timeout=3):
    # TODO: add type annotations
    resp = requests.head(url, timeout=(conn_timeout, read_timeout))
    return resp.status_code, resp.elapsed


# Handlers must be callables with a unary signature accepting a dict argument.
# This dict contains the details of the invocation. Valid keys include:
#
#     target: reference to the function or method being invoked
#     args: positional arguments to func
#     kwargs: keyword arguments to func
#     tries: number of invocation tries so far
#     elapsed: elapsed time in seconds so far
#     wait: seconds to wait (on_backoff handler only)
#     value: value triggering backoff (on_predicate decorator only)
#
# https://github.com/litl/backoff#event-handlers
def _backoff_handler(details):
    """Pretty-print backoff details."""
    msg = {
        "event": "backoff",
        "target": repr(details["target"]),
        "args": details["args"],
        "kwargs": details["kwargs"],
        "tries": details["tries"],
        "elapsed": details["elapsed"],
        "wait": details["wait"],
    }
    print(json.dumps(msg))


async def monitor(conf, queue, logger):
    # Configure exponential backoff without jitter;
    # no competing clients, as described here:
    # https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    backoff_deco = backoff.on_exception(
        backoff.expo,
        requests.exceptions.RequestException,
        on_backoff=_backoff_handler,
        max_tries=conf.backoff_retries,
        jitter=None,
    )

    while True:
        # Ping webpage
        #
        try:
            http_code, resp_time = backoff_deco(_ping)(
                conf.page_url, conf.conn_timeout, conf.read_timeout
            )
        except requests.exceptions.RequestException as err:
            logger.error(error=err)
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
        logger.info(source="monitor", message=msg)

        await queue.put(msg)
        await asyncio.sleep(conf.ping_interval)
