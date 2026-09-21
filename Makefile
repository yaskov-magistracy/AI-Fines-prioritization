.DEFAULT_GOAL := help
POETRY ?= poetry

help: ## Показать команды
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install: ## Поставить зависимости и pre-commit
	$(POETRY) install --with dev
	$(POETRY) run pre-commit install

lint: ## ruff check + format --check
	$(POETRY) run ruff check .
	$(POETRY) run ruff format --check .

fmt: ## Автоформат
	$(POETRY) run ruff check --fix .
	$(POETRY) run ruff format .

types: ## mypy
	$(POETRY) run mypy

test: ## pytest с покрытием
	$(POETRY) run pytest

check: lint types test ## Всё, что гоняет CI

run: ## Локальный API с автоперезагрузкой
	$(POETRY) run uvicorn fines.main:app --reload

migrate: ## Накатить миграции
	$(POETRY) run alembic upgrade head

revision: ## Новая миграция: make revision m="описание"
	$(POETRY) run alembic revision --autogenerate -m "$(m)"

up: ## Поднять стек в docker
	docker compose up --build -d

down: ## Погасить стек
	docker compose down -v

.PHONY: help install lint fmt types test check run migrate revision up down
