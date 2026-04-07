SYSTEM_PYTHON ?= python3.12
VENV_DIR := .venv
PYTHON := $(VENV_DIR)/bin/python
PIP := $(VENV_DIR)/bin/pip
VENV_STAMP := $(VENV_DIR)/.dev-installed
MANAGE := manage.py
DEV_REQUIREMENTS := requirements/development.txt

DJANGO_DEV := DJANGO_SETTINGS_MODULE=config.settings.development
DJANGO_PROD := DJANGO_SETTINGS_MODULE=config.settings.production
DJANGO_TEST := DJANGO_SETTINGS_MODULE=config.settings.testing

$(PYTHON):
	@$(SYSTEM_PYTHON) -m venv $(VENV_DIR)

$(VENV_STAMP): $(PYTHON) $(DEV_REQUIREMENTS) requirements/base.txt
	@$(PIP) install --upgrade pip setuptools wheel
	@$(PIP) install -r $(DEV_REQUIREMENTS)
	@touch $(VENV_STAMP)

.PHONY: init
init: $(VENV_STAMP)
	@echo "Virtual environment ready at $(VENV_DIR)"

.PHONY: help
help:
	@echo "make init            Create .venv and install development dependencies"
	@echo "make run dev         Run Django dev server (dev settings)"
	@echo "make run prod        Run Django server (prod settings)"
	@echo "make run test        Run Django tests (testing settings)"
	@echo "make migrate         Apply migrations (dev settings)"
	@echo "make makemigrations  Create migrations (dev settings)"
	@echo "make shell           Open Django shell (dev settings)"
	@echo "make createsuperuser Create a superuser (dev settings)"

.PHONY: run dev prod test
run: dev

dev: init
	@$(DJANGO_DEV) $(PYTHON) $(MANAGE) runserver 8001

prod: init
	@$(DJANGO_PROD) $(PYTHON) $(MANAGE) runserver

test: init
	@$(DJANGO_TEST) $(PYTHON) $(MANAGE) test

.PHONY: migrate
migrate: init
	@$(DJANGO_DEV) $(PYTHON) $(MANAGE) migrate

.PHONY: makemigrations
makemigrations: init
	@$(DJANGO_DEV) $(PYTHON) $(MANAGE) makemigrations

.PHONY: shell
shell: init
	@$(DJANGO_DEV) $(PYTHON) $(MANAGE) shell

.PHONY: createsuperuser
createsuperuser: init
	@$(DJANGO_DEV) $(PYTHON) $(MANAGE) createsuperuser
