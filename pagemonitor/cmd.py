import asyncio
import functools
import signal
import sys

import environs
from confluent_kafka import Producer
from httpx import AsyncClient

from .config import parse_config
from .logger import log
from .monitor import new_http_client, page_monitor
from .producer import kafka_producer, new_producer


__version__ = "0.2.0"


async def shutdown(
    loop, http_client: AsyncClient, kafka_client: Producer, _signal=None
) -> None:
    """Cleanup tasks tied to the service's shutdown."""
    if _signal:
        log.info("received exit signal", signal=_signal.name)

    log.info("closing transport and proxies", client=repr(http_client))
    await http_client.aclose()
    log.info("flushing Kafka producer")
    kafka_client.flush()

    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()

    log.info(f"cancelling {len(tasks)} outstanding tasks")
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()


def handle_exceptions(
    loop, ctx, http_client: AsyncClient, kafka_client: Producer
) -> None:
    """
    Custom exception handler for event loop.

    Context is a dict object containing the following keys:

    ‘message’:  Error message;
    ‘exception’ (optional): Exception object;
    ‘future’    (optional): asyncio.Future instance;
    ‘handle’    (optional): asyncio.Handle instance;
    ‘protocol’  (optional): Protocol instance;
    ‘transport’ (optional): Transport instance;
    ‘socket’    (optional): socket.socket instance.

    https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.call_exception_handler

    """
    # context["message"] will always be there; but context["exception"] may not
    msg = ctx.get("exception", ctx["message"])
    log.error("caught exception", exception=msg)
    log.info("Shutting down...")
    asyncio.create_task(shutdown(loop, http_client, kafka_client))


def run() -> None:
    """Entry point for the built executable."""
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

    # Instantiate clients
    http_client = new_http_client(conf.conn_timeout, conf.read_timeout)
    kafka_client = new_producer(conf)

    # Signals handling
    loop = asyncio.get_event_loop()
    signals = (signal.SIGHUP, signal.SIGTERM, signal.SIGINT)
    for s in signals:
        loop.add_signal_handler(
            s,
            lambda s=s: asyncio.create_task(
                shutdown(loop, http_client, kafka_client, _signal=s)
            ),
        )

    # Exception handler must be a callable with the signature matching
    # (loop, context)
    # https://docs.python.org/3/library/asyncio-eventloop.html#asyncio.loop.set_exception_handler
    exc_handler = functools.partial(
        handle_exceptions, http_client=http_client, kafka_client=kafka_client
    )
    loop.set_exception_handler(exc_handler)
    queue = asyncio.Queue()

    try:
        loop.create_task(page_monitor(http_client, conf, queue, log))
        loop.create_task(kafka_producer(kafka_client, conf, queue))
        loop.run_forever()
    finally:
        loop.close()
        log.info("shutdown successfully")
