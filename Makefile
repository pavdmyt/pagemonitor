name='pagemonitor'

fmt:
	@black --line-length 79 ./$(name) ./tests

lint:
	@pylint ./$(name) -rn -f colorized

isort:
	@isort --atomic --verbose $(name)/

test:
	@pytest

clean:
	@find . -type d -name '__pycache__' -exec rm -rf {} +
	@find . -name '*.pyc' -exec rm -f {} +
	@find . -name '*.pyo' -exec rm -f {} +
	@find . -name '*~' -exec rm -f {} +

build:
	@poetry build

run:
	pip uninstall -y pagemonitor
	pip install dist/pagemonitor-*-py3-none-any.whl
	echo ""
	pagemon
