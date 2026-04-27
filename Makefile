.PHONY: help install install-backend install-frontend dev dev-backend dev-frontend build db-reset test test-backend test-frontend lint fake-agent clean bundle-validate bundle-deploy bundle-destroy seed-dev app-status app-logs app-restart

# Override these on the command line or via env vars, e.g.
#   make bundle-deploy DBX_PROFILE=mycustomer DBX_TARGET=dev
DBX_PROFILE ?= DEFAULT
DBX_TARGET  ?= dev
APP_NAME    ?= velocia-newop-sdc

help:
	@echo "make install         - install backend + frontend deps"
	@echo "make dev             - run backend (8000) + frontend (5173) (separate terminals)"
	@echo "make build           - build frontend bundle into frontend/dist"
	@echo "make db-reset        - delete the local SQLite db (next start re-creates schema via init_db)"
	@echo "make test            - run all tests"
	@echo "make lint            - ruff + tsc"
	@echo "make fake-agent      - run a local stub of the Agent API on :9000"
	@echo ""
	@echo "Databricks Asset Bundle (target=$(DBX_TARGET) profile=$(DBX_PROFILE)):"
	@echo "  make bundle-validate - validate databricks.yml against the workspace"
	@echo "  make bundle-deploy   - provision Lakebase + app, deploy code"
	@echo "  make bundle-destroy  - tear down everything the bundle owns"
	@echo "  make seed-dev        - seed the deployed Lakebase with dev data"
	@echo "  make app-status      - show app + deployment status"
	@echo "  make app-logs        - tail the app's recent logs"
	@echo "  make app-restart     - restart the running app"

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

db-reset:
	rm -f local.db
	@echo "local.db removed; next backend start will recreate the schema via init_db()."

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

# --- Databricks Asset Bundle ---

bundle-validate:
	databricks bundle validate -t $(DBX_TARGET) --profile $(DBX_PROFILE)

bundle-deploy: build
	databricks bundle deploy -t $(DBX_TARGET) --profile $(DBX_PROFILE)
	@echo ">>> Ensuring app compute is started..."
	databricks --profile $(DBX_PROFILE) apps start $(APP_NAME) || true
	@echo ">>> Pushing app source code from the bundle workspace path..."
	@EMAIL=$$(databricks --profile $(DBX_PROFILE) current-user me -o json | python3 -c 'import json,sys; print(json.load(sys.stdin)["emails"][0]["value"])'); \
	databricks --profile $(DBX_PROFILE) apps deploy $(APP_NAME) \
		--source-code-path "/Workspace/Users/$$EMAIL/.bundle/velocia-newop-sdc/$(DBX_TARGET)/files"

bundle-destroy:
	databricks bundle destroy -t $(DBX_TARGET) --profile $(DBX_PROFILE) --auto-approve

seed-dev:
	python scripts/seed_dev.py --profile $(DBX_PROFILE) --app $(APP_NAME)

app-status:
	databricks --profile $(DBX_PROFILE) apps get $(APP_NAME)

app-logs:
	@# `apps logs` requires OAuth (PAT-based profiles fail with 'OAuth Token not supported').
	@# We'll try the canonical profile first and fall back to opening the /logz URL.
	databricks --profile $(DBX_PROFILE)-oauth apps logs $(APP_NAME) --tail-lines 200 \
		2>/dev/null \
		|| echo "Run-time logs: $$(databricks --profile $(DBX_PROFILE) apps get $(APP_NAME) --output json | python -c 'import json,sys;print(json.load(sys.stdin)[\"url\"])')/logz"

app-restart:
	databricks --profile $(DBX_PROFILE) apps stop $(APP_NAME) || true
	databricks --profile $(DBX_PROFILE) apps start $(APP_NAME)
