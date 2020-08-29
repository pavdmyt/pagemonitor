from environs import Env


class DotDict(dict):
    """dot.notation access to dict attributes."""

    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


# Store configuration separate from your code, as per The Twelve-Factor App
# methodology.
def parse_config():
    # TODO: add type hints
    env = Env()
    env.read_env()

    config = {
        # env.url() returns obj of type urllib.parse.ParseResult
        "page_url": env.url("PAGEMON_URL").geturl(),
        "ping_interval": env.float("PAGEMON_PING_INTERVAL", 5),
        # Number of seconds to wait to establish a connection to a remote machine.
        #
        # It’s a good practice to set connect timeouts to slightly larger than a
        # multiple of 3, which is the default TCP packet retransmission window
        # (https://www.hjp.at/doc/rfc/rfc2988.txt)
        "conn_timeout": env.float("PAGEMON_CONNECT_TIMEOUT", 4),
        # Number of seconds the client will wait for the server to send a response.
        # In 99.9% of cases, this is the time before the server sends the first byte).
        # READ_TIMEOUT = 3
        "read_timeout": env.float("PAGEMON_READ_TIMEOUT", 3),
    }
    return DotDict(config)
