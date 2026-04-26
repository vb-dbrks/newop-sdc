.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend build migrate test test-backend test-frontend lint fake-agent clean

help:
	@echo "make install       - install backend + frontend deps"
	@echo "make dev           - run backend (8000) + frontend (5173)"
	@echo "make build         - build frontend bundle into frontend/dist"
	@echo "make migrate       - alembic upgrade head against \$$DATABASE_URL"
	@echo "make test          - run all tests"
	@echo "make lint          - ruff + tsc"
	@echo "make fake-agent    - run a local stub of the Agent API on :9000"

install: install-backend install-frontend

install-backend:
	pip install -e ".[dev]"

install-frontend:
	cd frontend && npm install

dev:
	@echo "Run 'make dev-backend' and 'make dev-frontend' in separate terminals."

dev-backend:
	uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend:
	cd frontend && npm run dev

build:
	cd frontend && npm run build

migrate:
	alembic -c backend/db/migrations/alembic.ini upgrade head

test: test-backend

test-backend:
	pytest

test-frontend:
	cd frontend && npm test --if-present

lint:
	ruff check backend tests
	cd frontend && npx tsc --noEmit

fake-agent:
	uvicorn tests.backend.fake_agent:app --host 0.0.0.0 --port 9000

clean:
	rm -rf frontend/dist .pytest_cache .ruff_cache .mypy_cache
	find . -name "__pycache__" -type d -exec rm -rf {} +
