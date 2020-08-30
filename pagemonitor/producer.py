import json


def ack_handler(err, msg):
    """Delivery report handler called on
    successful or failed delivery of message
    """
    if err:
        msg = {
            "event": "failed to deilver message",
            "error": err,
        }
    else:
        msg = {
            "event": "record produced",
            "topic": msg.topic(),
            "partition": msg.partition(),
            "offset": msg.offset(),
        }
    print(json.dumps(msg))
