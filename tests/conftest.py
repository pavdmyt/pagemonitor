import os
import time

import pytest
from confluent_kafka import Consumer

from pagemonitor.config import parse_config


@pytest.fixture(scope="module")
def page_url():
    return "https://httpbin.org"


@pytest.fixture(scope="module")
def app_conf(page_url):
    os.environ["PAGEMON_URL"] = page_url
    return parse_config()


@pytest.fixture(scope="module")
def conf_topic():
    ts = time.strftime("%Y%m%dT%H%M%SZ", time.gmtime())
    return f"_test_{ts}"


@pytest.fixture(scope="module")
def kafka_consumer(app_conf):
    return Consumer(
        {
            "bootstrap.servers": app_conf.kafka_broker_list,
            "group.id": 1729,
            "auto.offset.reset": "earliest",
        },
    )
