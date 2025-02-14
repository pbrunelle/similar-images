SOURCE_VENV = source .venv/bin/activate;
SHELL = /usr/bin/bash

create-venv:
	python3 -m venv .venv
	$(SOURCE_VENV) pip install -r requirements.in

test:
	$(SOURCE_VENV) python -m pytest tests

ruff-format:
	$(SOURCE_VENV) python -m ruff format tests/test_types.py
