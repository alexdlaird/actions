.PHONY: all install check test

SHELL := /usr/bin/env bash
PYTHON_BIN ?= python3
PROJECT_VENV ?= venv

all: check test

venv:
	$(PYTHON_BIN) -m venv $(PROJECT_VENV)

install: venv
	@( \
		source $(PROJECT_VENV)/bin/activate; \
		python -m pip install flake8 mypy; \
	)

check: install
	@( \
		source $(PROJECT_VENV)/bin/activate; \
		flake8 && mypy --ignore-missing-imports *.py */*.py && shellcheck -S warning */*.sh; \
	)

test:
	$(PYTHON_BIN) -m unittest discover -s tests -t . -v
