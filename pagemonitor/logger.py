import structlog


structlog.configure(
    # Assuming logs collected into Elasticsearch
    processors=[
        structlog.processors.JSONRenderer(),
    ]
)

log = structlog.get_logger()
