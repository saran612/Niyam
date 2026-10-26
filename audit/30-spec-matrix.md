# Spec Conformance Matrix

Date: 2026-10-26  
Status: READ-ONLY AUDIT (Phase A)  
Platform: AICTE Approval Workflow & Compliance Monitoring Platform ("Niyam")

---

| Item | Requirement Description | Status | Evidence (File + Lines / Test / Command Output) | Notes & Missing Aspects |
|---|---|---|---|---|
| **A. WORKFLOW** | | | | |
| **A1** | Configurable route templates (Only Scrutiny, Scrutiny+EVC, EVC+SAC/SHC, Only EVC, re-scrutiny loop), stored as data, versioned | **DONE** | `backend/app/core/routes_config.py:11-266`, `backend/app/models/entities.py:96-109`, `test_workflow.py:test_mechanical_intake_auto_advances` | All 5 route templates stored with JSONB stage graphs, versions, and unique constraint `uq_route_template_name_version`. |
| **A2** | Auto-advance on mechanical stages; decision stages only SUGGEST, require authorised click | **DONE** | `backend/app/services/workflow.py:1-150`, `test_workflow.py:test_mechanical_intake_auto_advances`, `test_workflow.py:test_unauthorized_actor_rejected` | Mechanical stage automatically transitions; decision stages populate `application.suggested_action` and require authorized user click. |
| **A3** | Return/revert with mandatory reason (rejected if empty) | **DONE** | `backend/app/services/workflow.py:65-68`, `test_workflow.py:test_revert_without_reason_rejected`, Playwright test `e2e.spec.ts:4-36` | Returns 422 if reason is empty or whitespace. Recorded in stage transition log. |
| **A4** | Observations recorded per stage | **DONE** | `backend/app/models/entities.py:135-150`, `backend/app/services/workflow.py:113-126` | `stage_transitions` table records every stage shift, actor ID, and observation/reason text. |
| **A5** | Deterministic case summary + templated notices (Jinja2 or equivalent) | **MISSING** | Grep: no Jinja2 or notice template generator in repo | No templated PDF/HTML notice generation or deterministic case summary generator exists. |
| **B. DASHBOARDS** | | | | |
| **B1** | Role dashboards: Regional, Bureau, Committee, Institution, Admin | **PARTIAL** | Regional (`RegionalDashboard.tsx`), Bureau/Admin (`BureauDashboard.tsx`), Institution (`InstitutionDashboard.tsx`) exist. | Committee dedicated dashboard is **MISSING** (falls back to generic view). |
| **B2** | Ageing, stage-wise pendency, region-wise, bottlenecks, officer workload | **PARTIAL** | `BureauDashboard.tsx:94-118` (stage bar chart & pendency counts). | Missing officer workload distribution table and region-wise comparison breakdown. |
| **B3** | Alerts for approaching/exceeding timelines | **DONE** | `RegionalDashboard.tsx:72-76`, `BureauDashboard.tsx:73-80`, `backend/app/workers/scheduler.py:87-98` | Active stage SLAs, Breached Deadlines, and T-30/T-7/T-0/OVERDUE alerts displayed. |
| **B4** | CSV/PDF reports: pendency, EVC, compliance, document validity, overdue, region performance | **MISSING** | No export endpoints or report generators in backend or UI | Needs CSV streaming endpoints and printable/PDF reports. |
| **C. EVC** | | | | |
| **C1** | Auto-queue after preliminary stages | **DONE** | `routes_config.py:83-93`, `workflow.py:84-106` | In "Scrutiny + EVC" and "EVC + SAC/SHC" routes, passing scrutiny queues `EVC_PENDING`. |
| **C2** | Due/completion tracking | **DONE** | `obligation.py:68-85`, `entities.py:43` | Handled via single `obligations` table (`obligation_type="EVC_REPORT"`). |
| **C3** | New-institution distinct SLA | **MISSING** | `routes_config.py` uses fixed stage SLA | SLA does not differentiate between new institution setup vs existing institution renewal. |
| **C4** | Reminders + escalation | **DONE** | `scheduler.py:49-106`, `entities.py:151-163` | Escalation policies attached to EVC obligations fire reminders across ladder steps. |
| **D. UNDERTAKINGS** | | | | |
| **D1** | Record with condition text, due date, evidence | **DONE** | `entities.py:44`, `obligation.py:88-105` | `ObligationTypeEnum.UNDERTAKING` records condition text, due date, and application link. |
| **D2** | Institution upload | **PARTIAL** | `InstitutionDashboard.tsx:88-115` has satisfy action; `endpoints.py:302-356` supports upload. | Direct document file picker modal in Institution UI table is missing (currently calls satisfy directly). |
| **D3** | Officer verification | **PARTIAL** | Handled indirectly via application review | No explicit "verify undertaking" button on case detail view. |
| **D4** | Overdue escalation | **DONE** | `scheduler.py:58-98`, `test_obligation_worker.py:27-52` | Overdue undertakings trigger escalation alerts to regional and bureau officers. |
| **E. LEASE/DOCUMENTS** | | | | |
| **E1** | Expiry tracking | **DONE** | `entities.py:45,70`, `obligation.py:108-145`, `test_obligation_worker.py:11-25` | Generates `LEASE_EXPIRY` obligation based on `institutions.lease_expiry_date`. |
| **E2** | Advance alerts | **DONE** | `scheduler.py:58-98`, `routes_config.py` default policy | Escalation ladder fires T-30, T-7 alerts prior to lease expiry. |
| **E3** | Renewal submission + verification | **PARTIAL** | Document upload endpoint exists | No explicit lease renewal workflow stage. |
| **E4** | Overdue escalation | **DONE** | `scheduler.py:68-98`, `test_obligation_worker.py` | Overdue lease expiry generates escalated breach alerts. |
| **E5** | OCR date extraction with human verify | **MISSING** | No OCR library (tesseract/vision) or date extraction model present | No automated document date extraction implemented. |
| **F. ENGINE** | | | | |
| **F1** | Single obligation table (type: STAGE_SLA\|EVC\|UNDERTAKING\|LEASE) | **DONE** | `backend/app/models/entities.py:164-200` | Single `obligations` table with `obligation_type` enum covering STAGE_SLA, EVC_REPORT, UNDERTAKING, LEASE_EXPIRY, DEFICIENCY_RECTIFICATION. |
| **F2** | Scheduler is DB-backed, restart-safe (SKIP LOCKED), alerts UNIQUE(obligation_id, step), idempotent | **DONE** | `backend/app/workers/scheduler.py:38-45,71-76`, `backend/app/models/entities.py:218-220`, `test_obligation_worker.py:test_scheduler_escalation_and_idempotency` | Uses PostgreSQL `FOR UPDATE SKIP LOCKED`, unique constraint on `(obligation_id, step)`. |
| **F3** | Escalation ladder T-30/T-7/T-0/T+N routed by role+region from versioned policy | **DONE** | `backend/app/workers/scheduler.py:58-98`, `backend/app/models/entities.py:151-163` | Configured in `escalation_policies` JSONB ladder steps, resolves target user by `role` and `region_id`. |
| **F4** | Business-day SLA with holiday calendar | **DONE** | `backend/app/services/sla.py:1-92`, `backend/app/models/entities.py:223-235`, `test_sla.py` (4 tests pass) | Skips weekends and region/national holidays from `holiday_calendar` table. |
| **F5** | Virtual clock (no direct now() in business logic: grep for datetime.now/Date.now/now()) | **DONE** | `backend/app/core/clock.py:1-85`, `Makefile:34-35`, `test_clock.py` | Verified: 0 occurrences of direct `datetime.now()` in `backend/app/`. Tested in CI. |
| **F6** | Audit log append-only, hash-chained, written in same transaction as the change, verify endpoint | **DONE** | `backend/app/services/audit.py:1-126`, `backend/app/api/endpoints.py:266-276`, `test_audit.py` (2 tests pass) | SHA-256 hash chaining: `curr_hash = SHA-256(prev_hash + ...)`, in-transaction flush, `GET /api/audit/verify` detects any tampering. |
| **F7** | SLA/config change recomputes existing obligations | **DONE** | `backend/app/services/obligation.py:187-251`, `test_obligation_worker.py:test_sla_config_change_recomputes_obligations` | `recompute_stage_sla_obligations()` recalibrates `due_at` and records audit entries. |
| **G. SECURITY** | | | | |
| **G1** | JWT/OIDC with role+region claims | **DONE** | `backend/app/core/auth.py:37-69`, `test_api_security.py:test_auth_login_and_token` | Claims: `sub`, `email`, `role`, `region_id`, `institution_id`, `exp`, `iat`. Validated against virtual clock. |
| **G2** | Region scoping in query layer | **DONE** | `backend/app/api/deps.py:48-80`, `test_api_security.py:test_cross_region_isolation` | Server-side SQL query filtering; regional officers cannot query or mutate outside jurisdiction. |
| **G3** | Upload validation (magic bytes, size cap) | **DONE** | `backend/app/services/storage.py:25-78`, `test_storage.py` (3 tests pass) | Checks file magic bytes (PDF, JPEG, PNG only), 10MB file size cap, path traversal sanitization. |
| **G4** | Rate limiting, password hashing, security headers, CORS allowlist | **PARTIAL** | Password hashing (Argon2id) and CORS allowlist are **DONE**. Security headers & Redis rate limiter are **MISSING**. | Uses Argon2id for passwords; CORS configured in `main.py`. Missing explicit rate-limiting middleware (`slowapi` or Redis token bucket) and strict CSP headers. |
| **G5** | No secrets in repo | **DONE** | `.gitignore`, `backend/.env` | No production credentials or secrets committed to git. |
| **G6** | Dependency audit | **DONE** | `npm audit` (0 vulnerabilities), `bandit -r backend/app` (0 Medium/High issues; 1 Low on random seed in seed.py) | Dependencies are clean. |
| **H. AI/ML (advisory only, never changes state)** | | | | |
| **H1** | Breach-risk score + reason codes | **MISSING** | No ML risk model or scoring endpoint | Spec requires advisory breach-risk scoring with explainability reason codes. |
| **H2** | Anomaly flags | **DONE** | `backend/app/services/reconcile.py:1-105`, `test_data_pipeline.py:test_reconciliation_anomaly_detection` | Detects missing owners, stage mismatches, and overdue unbreached obligations. |
| **H3** | RAG copilot with APH clause citations, human approval | **MISSING** | No vector store or LLM copilot | Spec requires advisory RAG citing Approval Process Handbook (APH) clauses. |
| **H4** | Every AI artefact logged with model version | **MISSING** | Dependent on H1/H3 | Needs model version metadata in audit logs when AI artifacts are created. |
| **I. PLATFORM** | | | | |
| **I1** | Docker compose one-command | **DONE** | `docker-compose.yml`, `infra/Dockerfile.backend`, `infra/Dockerfile.frontend` | `docker compose up -d` boots db and mailhog. |
| **I2** | Seed/synthetic data | **DONE** | `backend/app/services/seed.py`, `Makefile:20-21` | Deterministic seeder generates 5 regions, 80 institutions, 80 applications, users, obligations, and holidays with seed 42. |
| **I3** | AICTE adapter (mock import) | **DONE** | `backend/app/adapters/aicte_import.py:1-195`, `test_data_pipeline.py:test_mock_importer_valid_and_malformed` | Parses legacy CSV/JSON, deduplicates, and logs row-level anomalies. Labelled MOCK. |
| **I4** | Tests (unit/integration/e2e) | **DONE** | 23 Pytest unit/integration tests + 4 Playwright E2E tests, 100% passing. | Real backend tests covering security, audit tampering, SLAs, and concurrency. |
| **I5** | CI | **DONE** | `.github/workflows/ci.yml` | GitHub actions workflow running lint, typecheck, pytest, and clock rule. |
| **I6** | Docs | **DONE** | `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/DEMO.md`, `docs/SECURITY.md`, `docs/LIMITATIONS.md` | Comprehensive documentation on system guarantees, trade-offs, and demo instructions. |
