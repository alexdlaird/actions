.PHONY: all install check test validate-release

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
		flake8 && mypy --ignore-missing-imports */*.py && shellcheck -S warning */*.sh; \
	)

test:
	$(PYTHON_BIN) -m unittest discover -s tests -t . -v

validate-release:
	@if [[ "${VERSION}" == "" ]]; then echo "VERSION is not set" & exit 1 ; fi

	@if [[ $$(cat VERSION) != "${VERSION}" ]] ; then echo "Version not bumped in VERSION" & exit 1 ; fi
