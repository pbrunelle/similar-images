SOURCE_VENV = source .venv/bin/activate;
SHELL = /usr/bin/bash

create-venv:
	python3 -m venv .venv
	$(SOURCE_VENV) pip install -r requirements.in

all: ruff test

test:
	$(SOURCE_VENV) python -m pytest tests/unit

integration-test:
	$(SOURCE_VENV) python -m pytest tests/integration

ruff:
	$(SOURCE_VENV) python -m ruff check --select I --fix similar_images/ tests/ scripts/
	$(SOURCE_VENV) python -m ruff format similar_images/ tests/ scripts/

