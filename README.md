Pagemonitor
===========

[![Build Status](https://travis-ci.org/pavdmyt/pagemonitor.svg?branch=master)](https://travis-ci.org/pavdmyt/pagemonitor)

Is a microservice designed to monitor website availability. It collects
availability metrics with configurable interval and writes them into
[Apache Kafka](https://kafka.apache.org/) for subsequent processing.


# Installation

Run the following commands:

```
$ make build
$ pip install dist/pagemonitor-*-py3-none-any.whl
```


# Configuration

Configuration is provided via environment variables. It contains good defaults
to start experimenting with. It is possible to override defaults either directly
(e.g. `export PAGEMON_PING_INTERVAL=30`) or via a file:

```
$ cat > pagemon.cfg <<EOF
> export PAGEMON_BACKOFF_RETRIES=5
> export PAGEMON_ENABLE_CERT_AUTH=True
>EOF
$
$ source pagemon.cfg
```

| Environment variable              | Parameter                | Description                                        | Default                                      |
|-----------------------------------|--------------------------|----------------------------------------------------|----------------------------------------------|
| `PAGEMON_URL`                     | `page_url`               | Webpage URL to monitor                             | `""`                                         |
| `PAGEMON_PING_INTERVAL`           | `ping_interval`          | How often webpage gets scraped (seconds)           | `10`                                         |
| `PAGEMON_CONNECT_TIMEOUT`         | `conn_timeout`           | Number of seconds to wait to establish a connection to a remote machine | `4`                     |
| `PAGEMON_READ_TIMEOUT`            | `read_timeout`           | Number of seconds the client will wait for the server to send a response | `3`                    |
| `PAGEMON_BACKOFF_RETRIES`         | `backoff_retries`        | Number of retries for exponential backoff (to handle connectivity issues)| `10`                   |
| `PAGEMON_BROKER_LIST`             | `kafka_broker_list`      | Initial list of brokers as host:port (comma delimited) | `localhost:9092,`                        |
| `PAGEMON_KAFKA_TOPIC`             | `kafka_topic`            | Kafka topic name to send monitoring data           | `pagemonitor_metrics`                        |
| `PAGEMON_PRODUCER_RETRIES`        | `producer_retries`       | How many times to retry sending a failing Message to Kafka | `3`                                  |
| `PAGEMON_ENABLE_CERT_AUTH`        | `kafka_enable_cert_auth` | Enable SSL mode for communication with Kafka       | `False`                                      |
| `PAGEMON_SSL_CA`                  | `kafka_ssl_ca`           | Path to CA file                                    | `/etc/pagemon/ssl/ca.pem`                    |
| `PAGEMON_SSL_CERT`                | `kafka_ssl_cert`         | Path to certificate file                           | `/etc/pagemon/ssl/service.cert`              |
| `PAGEMON_SSL_KEY`                 | `kafka_ssl_key`          | Path to key file                                   | `/etc/pagemon/ssl/service.key`               |



# Usage

After installation `pagemon` executable should be available in your `$PATH`.
Provide a desired config and start the service:

```
$ pagemon
{"bin": "/Users/me/.pyenv/versions/playground-py38/bin/pagemon", "version": "0.1.0", "config": {"page_url": "https://httpbin.org", "ping_interval": 5.0, "conn_timeout": 4.0, "read_timeout": 3.0, "backoff_retries": 10, "kafka_broker_list": "localhost:9092,", "kafka_topic": "pagemonitor_metrics", "producer_retries": 3, "kafka_enable_cert_auth": false, "kafka_ssl_ca": "PosixPath('/etc/pagemon/ssl/ca.pem')", "kafka_ssl_cert": "PosixPath('/etc/pagemon/ssl/service.cert')", "kafka_ssl_key": "PosixPath('/etc/pagemon/ssl/service.key')"}}
```


# Development

Clone the repository:

```
$ git clone git@github.com:pavdmyt/pagemonitor.git
```

Install dev dependencies:

```
$ poetry install

# if you don't have poetry installed:
pip install -r requirements.txt
```

Lint, format, isort code:

```
$ make lint
$ make fmt
$ make isort
```

Run tests:

```
$ make test
```

Build:

```
$ make build
```


# Contributing

1. Fork it!
2. Create your feature branch: `git checkout -b my-new-feature`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin my-new-feature`
5. Submit a pull request
6. Make sure tests are passing
