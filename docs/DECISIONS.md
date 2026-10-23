# Architectural Decisions Record (ADR)

## DEC-001: Technology Stack Selection
- **Backend**: Python 3 (3.11/3.12 compatible runtime), FastAPI, SQLAlchemy 2 (async + sync support for workers), Alembic, Pydantic v2.
- **Frontend**: React 19 + TypeScript + Vite + Tailwind CSS + Lucide React (clean SVG icons instead of emojis) + Recharts.
- **Data Stores**: PostgreSQL 16 for relational data, MinIO for S3-compatible document storage, Mailhog for local SMTP preview.
- **Task Scheduling**: PostgreSQL-backed `FOR UPDATE SKIP LOCKED` scheduler worker running in dedicated process. Avoids Celery/Redis overhead while guaranteeing strict transactional consistency and preventing double-firing.

## DEC-002: Deterministic Clock Design
- All system time checks must consume `clock.now()` provided by `app.core.clock`.
- DB table `system_clock` stores a global microsecond offset.
- Advancing clock via `POST /admin/clock/advance` enables testing time-dependent SLA breaches, T-30, T-7, T-0, and overdue alerts deterministically.

## DEC-003: Single Obligation Table Architecture
- Every compliance requirement (Stage SLA, EVC submission, Undertaking submission, Land/Building Lease Expiry) is modeled as a row in the `obligation` table.
- Obligations possess explicit lifecycle: `PENDING`, `SUBMITTED`, `SATISFIED`, `BREACHED`, `WAIVED`.
- Escalation policies define step intervals relative to `due_at` (e.g. -30d, -7d, 0d, +3d, +7d). Alerts enforce unique constraint `UNIQUE(obligation_id, step)`.

## DEC-004: Hash-Chained Audit Trail
- Each audit log record contains `prev_hash` (pointing to the prior record's hash) and `hash = SHA256(prev_hash + entity + action + payload + timestamp)`.
- Verification endpoint `GET /audit/verify` iterates through all logs to detect any modification or gap.

## DEC-005: Region Scoping at Query Layer
- Base queries for applications and obligations apply user region filters unconditionally for `regional_officer` roles.
- Cross-region attempts return 403 Forbidden or 404 Not Found to prevent data exposure.
