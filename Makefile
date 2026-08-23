# SciFiLingo Makefile
# Usage: make <target>
# Windows: use `make` via chocolatey or run commands directly with python manage.py

.PHONY: help install install-dev migrate makemigrations createsuperuser runserver runserver-plus shell shell-plus test lint format check clean graph_models collectstatic deploy-check

# Default target
help:
	@echo "SciFiLingo — Available commands:"
	@echo ""
	@echo "Setup:"
	@echo "  install          Install production dependencies"
	@echo "  install-dev      Install development dependencies (includes prod)"
	@echo ""
	@echo "Database:"
	@echo "  migrate          Apply database migrations"
	@echo "  makemigrations   Create new migrations from model changes"
	@echo "  createsuperuser  Create an admin superuser interactively"
	@echo ""
	@echo "Development:"
	@echo "  runserver        Start the development server (port 8000)"
	@echo "  runserver-plus   Start dev server with Werkzeug debugger (django-extensions)"
	@echo "  shell            Start Django shell"
	@echo "  shell-plus       Start enhanced Django shell (autoloads models)"
	@echo ""
	@echo "Quality:"
	@echo "  test             Run all tests with pytest"
	@echo "  lint             Run ruff linter"
	@echo "  format           Run ruff formatter"
	@echo "  check            Run Django system checks"
	@echo "  deploy-check     Run Django deployment checks (production mode)"
	@echo ""
	@echo "Utilities:"
	@echo "  graph_models     Generate ER diagram (requires graphviz)"
	@echo "  collectstatic    Collect static files for production"
	@echo "  clean            Remove cache, .pyc, and temp files"

# === Setup ===

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt

# === Database ===

migrate:
	python manage.py migrate

makemigrations:
	python manage.py makemigrations

createsuperuser:
	python manage.py createsuperuser

# === Development ===

runserver:
	python manage.py runserver

runserver-plus:
	python manage.py runserver_plus

shell:
	python manage.py shell

shell-plus:
	python manage.py shell_plus

# === Quality ===

test:
	pytest -v

lint:
	ruff check .

format:
	ruff format .
	ruff check --fix .

check:
	python manage.py check

deploy-check:
	python manage.py check --deploy

# === Utilities ===

graph_models:
	python manage.py graph_models -a -o scifilingo_er_diagram.png

collectstatic:
	python manage.py collectstatic --noinput

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	rm -rf .pytest_cache .ruff_cache staticfiles
