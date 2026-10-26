# Audit Recon: AICTE Approval Workflow & Compliance Monitoring Platform ("Niyam")

Date: 2026-10-26  
Status: READ-ONLY AUDIT (Phase A)  
Repository: `saran612/SIH26262`

---

## 1. Repository Map

### Tree Structure (Depth 3)
```
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── .gitignore
├── BLOCKERS.md
├── CLAUDE.md
├── Makefile
├── README.md
├── TASKS.md
├── audit/
│   └── screenshots/
│       ├── 01_login_page.png
│       ├── 02_regional_dashboard.png
│       ├── 03_case_detail_view.png
│       ├── 04_audit_explorer.png
│       ├── 05_bureau_dashboard.png
│       └── 06_institution_dashboard.png
├── backend/
│   ├── .env
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/
│   │       └── ccda0eca8bab_initial_schema.py
│   ├── alembic.ini
│   ├── app/
│   │   ├── adapters/
│   │   │   └── aicte_import.py
│   │   ├── api/
│   │   │   ├── deps.py
│   │   │   ├── endpoints.py
│   │   │   └── schemas.py
│   │   ├── core/
│   │   │   ├── auth.py
│   │   │   ├── clock.py
│   │   │   ├── config.py
│   │   │   ├── database.py
│   │   │   └── routes_config.py
│   │   ├── main.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── entities.py
│   │   ├── services/
│   │   │   ├── audit.py
│   │   │   ├── obligation.py
│   │   │   ├── reconcile.py
│   │   │   ├── seed.py
│   │   │   ├── sla.py
│   │   │   ├── storage.py
│   │   │   └── workflow.py
│   │   └── workers/
│   │       └── scheduler.py
│   ├── requirements.txt
│   └── tests/
│       ├── test_api_security.py
│       ├── test_audit.py
│       ├── test_clock.py
│       ├── test_data_pipeline.py
│       ├── test_obligation_worker.py
│       ├── test_sla.py
│       ├── test_storage.py
│       └── test_workflow.py
├── docker-compose.yml
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   ├── DEMO.md
│   ├── HARDENING.md
│   ├── LIMITATIONS.md
│   └── SECURITY.md
├── frontend/
│   ├── .gitignore
│   ├── README.md
│   ├── _oxlintrc.json
│   ├── dist/
│   ├── index.html
│   ├── package-lock.json
│   ├── package.json
│   ├── playwright.config.ts
│   ├── public/
│   ├── src/
│   │   ├── App.tsx
│   │   ├── api.ts
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── AuditExplorer.tsx
│   │   │   ├── BureauDashboard.tsx
│   │   │   ├── CaseDetailView.tsx
│   │   │   ├── InstitutionDashboard.tsx
│   │   │   ├── RegionalDashboard.tsx
│   │   │   └── VirtualClockBar.tsx
│   │   ├── index.css
│   │   ├── main.jsx
│   │   └── types.ts
│   ├── tests/
│   │   └── e2e.spec.ts
│   └── vite.config.js
├── infra/
│   ├── Dockerfile.backend
│   └── Dockerfile.frontend
├── pyproject.toml
└── storage/
    └── documents/
```

### Languages & Frameworks
- **Backend**: Python 3.12, FastAPI 0.159.1, SQLAlchemy 2.1.6, Pydantic 2.14.1, Alembic 1.20.1, Argon2-cffi 25.1.0, PyJWT 2.15.1.
- **Frontend**: TypeScript 5, React 19, Vite 8.3.5, Tailwind CSS v4, Lucide React icons, Recharts 3.8.
- **Database / Infrastructure**: PostgreSQL 16 (port 5433 mapped to container 5432), MinIO S3 object storage (port 9000), MailHog SMTP server (ports 1025, 8025).

### Entry Points
- Backend server: `backend/app/main.py` (`uvicorn app.main:app`).
- Background worker: `backend/app/workers/scheduler.py` (`run_scheduler_loop()`).
- Database seed script: `backend/app/services/seed.py` (`python -m app.services.seed`).
- Frontend SPA: `frontend/src/main.jsx` -> `frontend/src/App.tsx`.

### DB Schema & Migrations
- Migration tool: Alembic (`backend/alembic/versions/ccda0eca8bab_initial_schema.py`).
- Tables: `regions`, `institutions`, `users`, `route_templates`, `applications`, `stage_transitions`, `escalation_policies`, `obligations`, `alerts`, `holiday_calendar`, `documents`, `audit_logs`.

### Environment Variables (`backend/.env`)
```
DATABASE_URL=postgresql+psycopg2://aicte_user:aicte_password@localhost:5433/aicte_db
ASYNC_DATABASE_URL=postgresql+asyncpg://aicte_user:aicte_password@localhost:5433/aicte_db
TEST_DATABASE_URL=sqlite:///./test.db
S3_ENDPOINT=http://localhost:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadminpassword
S3_BUCKET=aicte-documents
STORAGE_DIR=./storage/documents
SMTP_HOST=localhost
SMTP_PORT=1025
JWT_SECRET=dev_secret_key_change_in_production_super_secure_32_bytes_min
```

### Scripts (`Makefile`)
- `make up`: Boot docker compose (Postgres, MinIO, MailHog).
- `make seed`: Execute deterministic DB seeder (`python -m app.services.seed`).
- `make test`: Run pytest with coverage.
- `make lint`: Run ruff and oxlint.
- `make typecheck`: Run mypy on backend.
- `make check`: Run lint, typecheck, pytest, and AST/grep check for `datetime.now()`.
- `make e2e`: Run Playwright E2E suite.

---

## 2. Boot Record

### Execution Log

1. **Docker Infrastructure**:
   - Command: `docker compose ps`
   - Output:
     ```
     NAME             IMAGE                    SERVICE   STATUS
     aicte-mailhog    mailhog/mailhog:v1.0.1   mailhog   Up (ports 1025, 8025)
     aicte-postgres   postgres:16-alpine       db        Up (healthy, port 5433)
     ```
   - Note: Docker container `minio` was not configured in `docker-compose.yml`, but `app.services.storage` provides fallback to `./storage/documents` if S3 endpoint is unavailable.

2. **Database Seeding**:
   - Command: `PYTHONPATH=backend backend/.venv/bin/python -m app.services.seed`
   - Exit Code: 0
   - Output:
     ```
     Seeding database deterministically with random seed 42...
     Seed complete! Generated 5 regions, 80 institutions, and 80 applications.
     ```

3. **Backend Boot**:
   - Command: `backend/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`
   - Output:
     ```
     INFO:     Started server process [23673]
     INFO:     Application startup complete.
     INFO:     Uvicorn running on http://127.0.0.1:8000
     ```
   - Health check: `curl http://127.0.0.1:8000/health` -> `{"status":"ok","system_time":"2026-10-26T00:20:00Z"}`

4. **Frontend Boot**:
   - Command: `npm run dev -- --host 127.0.0.1 --port 5173`
   - Output:
     ```
     VITE v8.3.5  ready in 360 ms
     ➜  Local:   http://127.0.0.1:5173/
     ```

---

## 3. Test, Lint & Typecheck Results

### Backend Pytest
- Command: `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests -v`
- Pass Count: 23 passed, 0 failed, 1 warning (Starlette testclient warning)
- Duration: 21.06s
- Evidence log:
  ```
  backend/tests/test_api_security.py::test_auth_login_and_token PASSED
  backend/tests/test_api_security.py::test_cross_region_isolation PASSED
  backend/tests/test_api_security.py::test_api_revert_requires_reason PASSED
  backend/tests/test_api_security.py::test_api_advance_workflow_and_routes PASSED
  backend/tests/test_api_security.py::test_api_admin_clock_advance_and_audit_verify PASSED
  backend/tests/test_audit.py::test_audit_hash_chain_validity PASSED
  backend/tests/test_audit.py::test_audit_detects_tampering PASSED
  backend/tests/test_clock.py::test_virtual_clock_advance PASSED
  backend/tests/test_data_pipeline.py::test_mock_importer_valid_and_malformed PASSED
  backend/tests/test_data_pipeline.py::test_reconciliation_anomaly_detection PASSED
  backend/tests/test_obligation_worker.py::test_lease_expiry_obligation_generation PASSED
  backend/tests/test_obligation_worker.py::test_scheduler_escalation_and_idempotency PASSED
  backend/tests/test_obligation_worker.py::test_sla_config_change_recomputes_obligations PASSED
  backend/tests/test_sla.py::test_business_day_detection PASSED
  backend/tests/test_sla.py::test_calculate_due_date_across_weekend PASSED
  backend/tests/test_sla.py::test_calculate_due_date_across_holiday PASSED
  backend/tests/test_sla.py::test_calculate_due_date_zero_or_negative PASSED
  backend/tests/test_storage.py::test_magic_byte_detection PASSED
  backend/tests/test_storage.py::test_sanitize_filename PASSED
  backend/tests/test_storage.py::test_upload_validations PASSED
  backend/tests/test_workflow.py::test_mechanical_intake_auto_advances PASSED
  backend/tests/test_workflow.py::test_revert_without_reason_rejected PASSED
  backend/tests/test_workflow.py::test_unauthorized_actor_rejected PASSED
  ======================== 23 passed, 1 warning in 21.06s ========================
  ```

### Backend Linter & Typecheck
- Command: `backend/.venv/bin/ruff check backend/app backend/tests`
  - Output: `All checks passed!`
- Command: `backend/.venv/bin/mypy backend/app`
  - Output: `Success: no issues found in 20 source files`
- Virtual Clock Grep Enforcement:
  - Command: `! grep -rn --exclude-dir="__pycache__" --include="*.py" -E "^\s*[^#*\"'].*datetime\.now\(\)" backend/app/`
  - Output: 0 matches (Exited with code 0). Direct `datetime.now()` strictly prohibited.

### Frontend Linter
- Command: `npm run lint`
  - Output: `Found 0 warnings and 0 errors. Finished in 23ms on 13 files with 96 rules.`

### Playwright E2E Tests
- Command: `npx playwright test`
  - Pass Count: 4 passed in 928ms
  - Evidence:
    ```
    ✓ E2E › revert requires non-empty reason and rejects empty input with 422 (129ms)
    ✓ E2E › cross-region isolation returns 404/403 for unauthorized regional access (119ms)
    ✓ E2E › clock advance triggers obligation breach and alerts idempotently (140ms)
    ✓ E2E › SLA config route modification updates route template and recomputes obligations (66ms)
    ```

---

## 4. Recon Findings Summary

1. **Working & Green Core Engine**:
   - The virtual clock, SLA business-day calculation, append-only hash-chained audit logging, SKIP LOCKED scheduler worker, and role/region scoping in repository queries are fully implemented and backed by passing unit and integration tests.
2. **Missing Components vs Broad Spec**:
   - No Committee dedicated dashboard (committee members see default view).
   - Reports (CSV/PDF export) are not implemented as endpoints or UI triggers.
   - OCR date extraction and Jinja2 notice/case summary generation are not implemented.
   - AI/ML features (breach risk score, advisory RAG copilot with APH clauses) are not implemented.
   - Bandit identified 1 Low warning in `seed.py` (standard `random.Random(42)` pseudo-random generator used for deterministic synthetic data seeding).
