name='pagemonitor'

fmt:
	@black --line-length 79 ./$(name) ./tests

lint:
	@pylint ./$(name) -rn -f colorized

lint-tests:
	@pylint ./tests -rn -f colorized

isort:
	@isort --atomic --verbose $(name)/
	@isort --atomic --verbose tests/

test:
	@pytest --capture=no

coverage: clean
	@poetry run py.test --cov-report=term --cov-report=html --cov-report=xml --cov $(name) tests/
	@echo "open file://`pwd`/htmlcov/index.html"

clean:
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +

build: fmt isort
	@poetry build

run:
	pip uninstall -y pagemonitor
	pip install dist/pagemonitor-*-py3-none-any.whl
	echo ""
	pagemon

mypy:
	@mypy ./$(name)

travis-setup:
	curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | python
	poetry install

ci:
	poetry run py.test --capture=no

export-requirements:
	@poetry export -f requirements.txt --dev > requirements.txt
