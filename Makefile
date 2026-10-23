.PHONY: up down restart build logs seed test lint typecheck check e2e demo clean

VENV = backend/.venv
PYTHON = $(VENV)/bin/python
PYTEST = $(VENV)/bin/pytest
RUFF = $(VENV)/bin/ruff
MYPY = $(VENV)/bin/mypy

up:
	docker compose up -d db minio mailhog
	@echo "Waiting for services..."
	@sleep 2

down:
	docker compose down -v

logs:
	docker compose logs -f

seed:
	PYTHONPATH=backend $(PYTHON) -m app.services.seed

test:
	PYTHONPATH=backend $(PYTEST) backend/tests -v --cov=backend/app --cov-report=term-missing

lint:
	$(RUFF) check backend/app backend/tests
	cd frontend && npm run lint

typecheck:
	$(MYPY) backend/app

check: lint typecheck test
	@echo "Enforcing CLAUDE.md clock rule: no direct datetime.now() in app/..."
	@! grep -rn --exclude-dir="__pycache__" --include="*.py" -E "^\s*[^#*\"'].*datetime\.now\(\)" backend/app/ || (echo "ERROR: direct datetime.now() found! Use clock.now()" && exit 1)
	@echo "All checks passed successfully."

e2e:
	@echo "Running Playwright E2E tests..."
	cd frontend && npx playwright test

demo:
	PYTHONPATH=backend $(PYTHON) -m app.services.demo
