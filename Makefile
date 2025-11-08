PYTHON?=python3
PIP?=pip3
PROJECT_NAME=mel_collecte
ZIP_FILE=${PROJECT_NAME}.zip
HA_CONFIG_DIR=custom_components/${PROJECT_NAME}

.PHONY: help install test lint lint-black lint-ruff lint-mypy build clean

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

install: venv/bin/activate

venv/bin/activate:
	test -d venv || ${PYTHON} -m venv venv
	. venv/bin/activate && ${PIP} install --upgrade pip
	. venv/bin/activate && ${PIP} install -r requirements-dev.txt

install-dev: install

test:
	. venv/bin/activate && pytest

lint: lint-ruff lint-black lint-mypy

lint-ruff:
	. venv/bin/activate && ruff check custom_components tests

lint-black:
	. venv/bin/activate && black --check custom_components tests

lint-mypy:
	. venv/bin/activate && mypy custom_components

build:
	rm -f ${ZIP_FILE}
	zip -r ${ZIP_FILE} ${HA_CONFIG_DIR} README.md --exclude "*/__pycache__/*" "*/.DS_Store"

clean:
	rm -rf venv
	rm -f ${ZIP_FILE}
	find . -type d -name "__pycache__" -exec rm -rf {} +

