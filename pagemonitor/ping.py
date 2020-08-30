import json

import requests


def ping(url, conn_timeout=4, read_timeout=3):
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
def backoff_handler(details):
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
