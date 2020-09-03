import json
import multiprocessing as mp
import os
import time

import pagemonitor


def test_e2e(conf_topic, kafka_consumer):
    """End-to-end test of the service.

    Ping given page URL, build messages with metrics data and
    write them into the Kafka topic. Examine topic for produced
    messages, enusure they contain necessary fields.

    """
    # Pass test configuration
    page_url = "https://httpbin.org"
    os.environ["PAGEMON_URL"] = page_url
    os.environ["PAGEMON_KAFKA_TOPIC"] = conf_topic
    os.environ["PAGEMON_PING_INTERVAL"] = "0.5"

    # Run pagemonitor as a separate process
    proc = mp.Process(target=pagemonitor.run)
    proc.start()
    time.sleep(5)
    proc.terminate()

    # Consume messages from Kafka
    try:
        client = kafka_consumer
        client.subscribe([conf_topic])
        # Trying to consume more messages that are actually in the
        # topic blocks client.consume call
        messages_raw = client.consume(num_messages=3)
    finally:
        client.close()

    messages = [
        json.loads(msg.value()) for msg in messages_raw if not msg.error()
    ]

    # Check message contents
    for msg in messages:
        assert page_url == msg["page_url"]
        assert "http_code" in msg
        assert "response_time" in msg
        assert "ts" in msg
