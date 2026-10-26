# Backend Section-by-Section Audit

Date: 2026-10-26  
Status: READ-ONLY AUDIT (Phase A)  
Backend Base: FastAPI + SQLAlchemy 2.0 + PostgreSQL 16 + Pydantic v2

---

## 1. Endpoints & Services Matrix

Every endpoint was tested using live HTTP requests as different roles, with adversarial test payloads (cross-region access, missing tokens, empty reasons, oversized uploads, and invalid file bytes).

| Endpoint / Service | Method | Purpose | Auth / RBAC Enforced? | Region Scoping Server-Side? | Input Validation | Tests | Status | Evidence |
|---|---|---|---|---|---|---|---|---|
| `/api/auth/login` | `POST` | Authenticate user, issue virtual-clock signed JWT | Public (N/A) | N/A | Pydantic `LoginRequest` (email, password) | `test_api_security.py:test_auth_login_and_token` | **DONE** | Tested: returns 200 with JWT token for valid credentials, 401 for bad password. `endpoints.py:59-76` |
| `/api/auth/me` | `GET` | Get authenticated user profile & claims | Yes (`HTTPBearer` + Argon2/JWT) | Self | N/A | `test_api_security.py:test_auth_login_and_token` | **DONE** | Tested: returns user claims (`role`, `region_id`, `institution_id`). Returns 401 if token missing. `endpoints.py:79-88` |
| `/api/admin/clock/advance` | `POST` | Advance virtual clock by N seconds and record audit log | Yes (`RoleEnum.ADMIN` only) | N/A | Pydantic `ClockAdvanceRequest` (`seconds >= 1`) | `test_clock.py:test_virtual_clock_advance`, `test_api_security.py:test_api_admin_clock_advance_and_audit_verify` | **DONE** | Tested: Admin advances clock -> 200; Regional Officer -> 403 Forbidden. `endpoints.py:92-108` |
| `/api/admin/clock/reset` | `POST` | Reset virtual clock to 0 offset | Yes (`RoleEnum.ADMIN` only) | N/A | None | `test_clock.py` | **DONE** | Tested: Admin resets clock -> 200 with offset 0. `endpoints.py:111-126` |
| `/api/admin/clock/status` | `GET` | Retrieve virtual clock timestamp & offset | Public / Internal | N/A | None | Polled by frontend header | **DONE** | Tested: returns ISO timestamp and offset in seconds. `endpoints.py:129-134` |
| `/api/applications` | `GET` | List applications filtered by jurisdiction & stage | Yes (`get_current_user`) | **Enforced**: `scope_applications_query` filters `region_id` or `institution_id` in SQL | Query param `stage` (optional) | `test_api_security.py:test_cross_region_isolation` | **DONE** | Tested: RO SRO gets SRO apps only; no token -> 401. `deps.py:48-65`, `endpoints.py:138-148` |
| `/api/applications/{id}` | `GET` | Retrieve single application details & history | Yes (`get_current_user`) | **Enforced**: query filtered by user scope in SQL query layer | Path param `app_id: int` | `test_api_security.py:test_cross_region_isolation` | **DONE** | Tested: SRO requesting NRO app (ID #237) returns **404 Not Found** (prevents ID enumeration). `endpoints.py:151-163` |
| `/api/applications/{id}/advance` | `POST` | Advance workflow to next stage | Yes (`allowed_roles` on stage + `RoleEnum.ADMIN`) | **Enforced**: query filtered by user scope in SQL | Pydantic `AdvanceStageRequest` | `test_api_security.py:test_api_advance_workflow_and_routes` | **DONE** | Tested: Advances stage, closes old stage obligation, creates new stage obligation in single transaction. `endpoints.py:165-192` |
| `/api/applications/{id}/revert` | `POST` | Revert application to deficiency stage | Yes (`allowed_roles` + `RoleEnum.ADMIN`) | **Enforced**: query filtered by user scope in SQL | Pydantic `RevertStageRequest` with non-empty validation | `test_workflow.py:test_revert_without_reason_rejected`, `test_api_security.py:test_api_revert_requires_reason` | **DONE** | Tested: Empty string reason rejected with **422 Unprocessable Entity**. Valid reason reverts stage and records audit log. `endpoints.py:194-221` |
| `/api/obligations` | `GET` | List obligations filtered by jurisdiction | Yes (`get_current_user`) | **Enforced**: `scope_obligations_query` in SQL query layer | Query param `status_filter` | `test_obligation_worker.py:test_lease_expiry_obligation_generation` | **DONE** | Tested: Single table for all obligation types (STAGE_SLA, LEASE, etc.). Regional isolation verified. `endpoints.py:224-235` |
| `/api/obligations/{id}/satisfy` | `POST` | Satisfy / mark compliance obligation completed | Yes (`get_current_user`) | **Enforced**: query scoped to institution/region | Path param `ob_id: int` | `test_obligation_worker.py` | **DONE** | Tested: Sets `status = SATISFIED` and `satisfied_at = clock.now()`, records in audit trail. `endpoints.py:237-263` |
| `/api/audit/verify` | `GET` | Verify cryptographic SHA-256 hash chain | Public / Admin / Bureau | N/A | None | `test_audit.py:test_audit_hash_chain_validity`, `test_audit.py:test_audit_detects_tampering` | **DONE** | Tested: returns `{"is_valid": true, "total_logs": 132}`. Detects tampering when row payload or hash is mutated. `endpoints.py:266-276` |
| `/api/audit/logs` | `GET` | Retrieve append-only audit trail records | Yes (`RoleEnum.ADMIN`, `RoleEnum.BUREAU_OFFICER`) | National | Query param `limit` | `test_audit.py` | **DONE** | Tested: returns log array. Returns 403 Forbidden if accessed by Regional Officer. `endpoints.py:278-299` |
| `/api/documents/upload` | `POST` | Upload compliance evidence document | Yes (`get_current_user`) | Scoped to institution | Multi-part form: checks magic bytes, max 10MB file size cap, path traversal prevention | `test_storage.py:test_magic_byte_detection`, `test_storage.py:test_upload_validations` | **DONE** | Tested: EXE file rejected (400); >10MB rejected (400); valid PDF succeeds (200) with sha256 and S3 presigned URL. `endpoints.py:302-356` |
| `/api/routes` | `GET` | List active route templates & stage graphs | Public / Authenticated | N/A | None | `test_workflow.py` | **DONE** | Tested: returns JSON definitions of all versioned route templates. `endpoints.py:52-55` |
| `/health` | `GET` | Liveness health check | Public | N/A | None | `main.py:75-76` | **DONE** | Tested: returns `{"status": "ok", "system_time": "..."}` |
| **Scheduler Worker** | Daemon/Worker | Concurrency-safe escalation worker (`SKIP LOCKED`) | System | Scoped by region + role from policy | Idempotent via `UNIQUE(obligation_id, step)` | `test_obligation_worker.py:test_scheduler_escalation_and_idempotency` | **DONE** | Tested: Advances ladder T-30, T-7, T-0, OVERDUE. Re-running worker generates 0 duplicates. `scheduler.py:28-112` |
| **Reconcile Worker** | Nightly Service | Detects orphaned obligations, state mismatches, overdue unbreached | System | Scans all obligations | Pydantic output report | `test_data_pipeline.py:test_reconciliation_anomaly_detection` | **DONE** | Tested: Correctly flags state mismatches and overdue unbreached obligations in audit log. `reconcile.py:31-105` |

---

## 2. Adversarial Curl & Break Tests

1. **Unauthenticated Access**:
   - `curl http://127.0.0.1:8000/api/applications` -> **401 Unauthorized** (Pass).
2. **Privilege Escalation**:
   - `POST /api/admin/clock/advance` as Regional Officer -> **403 Forbidden** (Pass).
3. **Cross-Region Enumeration**:
   - `GET /api/applications/237` (NRO region) as SRO Regional Officer -> **404 Not Found** (Pass: does not leak existence).
4. **Empty Revert Reason**:
   - `POST /api/applications/237/revert` with `{"reason": ""}` -> **422 Unprocessable Entity** (Pass).
5. **Malicious / Disallowed File Upload**:
   - Uploading Windows executable (`MZ\x90...`) -> **400 Bad Request** ("Disallowed or invalid file type. Only PDF and JPG/PNG are permitted.") (Pass).
6. **Oversized Upload**:
   - Uploading 11MB PDF -> **400 Bad Request** ("File size 11534345 exceeds maximum limit of 10485760 bytes") (Pass).
7. **Audit Tamper Detection**:
   - Mutating a database record's payload or hash causes `verify_chain(db)` to return `is_valid: False` with the exact corrupted log ID (Tested in `test_audit_detects_tampering`).
