PYTHON?=python3
PIP?=pip3
VENV:=venv
VENV_BIN:=$(VENV)/bin
PROJECT_NAME=mel_collecte
ZIP_FILE=${PROJECT_NAME}.zip
HA_CONFIG_DIR=custom_components/${PROJECT_NAME}

.PHONY: help install install-dev test lint lint-black lint-ruff lint-mypy build clean

help:
	@echo "Cibles disponibles :"
	@echo "  install     - Crée un venv local et installe les dépendances"
	@echo "  install-dev - Installe les dépendances de dev (pytest, ruff...)"
	@echo "  test        - Exécute pytest"
	@echo "  lint        - Lance l'ensemble des lint (ruff + black --check + mypy)"
	@echo "  lint-ruff   - Lint avec ruff"
	@echo "  lint-black  - Vérifie la formatting via black --check"
	@echo "  lint-mypy   - Vérifie la statique avec mypy"
	@echo "  build       - Crée l'archive ZIP pour Home Assistant"
	@echo "  clean       - Supprime le venv, le zip et les caches"

install:
	@test -d $(VENV) || ${PYTHON} -m venv $(VENV)
	$(VENV_BIN)/python -m pip install --upgrade pip
	$(VENV_BIN)/pip install -r requirements-dev.txt

install-dev: install

test: install
	$(VENV_BIN)/pytest

lint: install lint-ruff lint-black lint-mypy

lint-ruff:
	$(VENV_BIN)/ruff check custom_components tests

lint-black:
	$(VENV_BIN)/black --check custom_components tests

lint-mypy:
	$(VENV_BIN)/mypy custom_components

build:
	rm -f ${ZIP_FILE}
	zip -r ${ZIP_FILE} ${HA_CONFIG_DIR} README.md --exclude "*/__pycache__/*" "*/.DS_Store"

clean:
	rm -rf $(VENV)
	rm -f ${ZIP_FILE}
	find . -type d -name "__pycache__" -exec rm -rf {} +

