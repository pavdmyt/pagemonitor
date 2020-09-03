import asyncio
import json
import time

import backoff
import httpx


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


async def monitor(client, conf, queue, logger):
    # Configure exponential backoff without jitter;
    # no competing clients, as described here:
    # https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/
    backoff_deco = backoff.on_exception(
        backoff.expo,
        httpx.TransportError,
        on_backoff=_backoff_handler,
        max_tries=conf.backoff_retries,
        jitter=None,
    )

    try:
        while True:
            # Ping webpage
            #
            try:
                resp = await backoff_deco(client.get)(conf.page_url)
            # Executed when backoff retries gave no result
            except httpx.TransportError as err:
                logger.error(error=err)
                break
            else:
                http_code = resp.status_code
                resp_time = resp.elapsed

                # Compose Kafka message
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
    finally:
        await client.aclose()
        for task in asyncio.Task.all_tasks():
            logger.info("cancelling task", task=task)
            task.cancel()
