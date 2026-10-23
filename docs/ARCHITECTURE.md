# AICTE Approval & Compliance Obligation Engine - Architecture

> **Deterministic engine, human decides, everything audited. No ML on the critical path.**
> *All stage durations, SLAs, and escalation schedules are illustrative prototype configurations.*

---

## 1. System Overview

```
                      +-----------------------------------+
                      |      Frontend (React + Vite)      |
                      |  - Regional Officer Dashboard     |
                      |  - Bureau Executive Dashboard     |
                      |  - Institution Portal             |
                      |  - Admin & Virtual Time Controls  |
                      +-----------------+-----------------+
                                        | (HTTPS / REST)
                                        v
                      +-----------------------------------+
                      |         FastAPI Gateway           |
                      |  - JWT Auth + Argon2              |
                      |  - Strict Role Scoping (Region)   |
                      |  - MIME Magic-byte verification   |
                      +-----------------+-----------------+
                                        |
        +-------------------------------+-------------------------------+
        |                               |                               |
        v                               v                               v
+-------+---------------+     +---------+-----------+     +-------------+---------+
|   Workflow Engine     |     |  Obligation Engine  |     |   Audit Trail Engine  |
| - Mechanical Intake   |     | - Single Ob. Table  |     | - In-Tx Record Helper |
| - Human Decisions     |     | - SLA Calculator    |     | - Prev Hash + Hash    |
| - Mandatory Revert    |     | - Holiday Calendar  |     | - GET /audit/verify   |
+-------+---------------+     +---------+-----------+     +-------------+---------+
        |                               |                               |
        +-------------------------------+-------------------------------+
                                        | (Atomic DB Transactions)
                                        v
                      +-----------------------------------+
                      |     PostgreSQL Relational DB      |
                      | - application, institution, user  |
                      | - route_template, obligation      |
                      | - escalation_policy, alert        |
                      | - holiday_calendar, audit_log     |
                      +-----------------+-----------------+
                                        ^
                                        | (FOR UPDATE SKIP LOCKED)
                      +-----------------+-----------------+
                      |     Background Scheduler Worker   |
                      | - Polls due obligations           |
                      | - Idempotent escalation steps     |
                      | - Mailhog notification trigger    |
                      +-----------------------------------+
```

---

## 2. Core Principles & Data Model

### A. The Single Obligation Table (`obligation`)
Every compliance deadline, regardless of origin, is stored as a row in the `obligation` table:
- **Stage SLAs**: Scrutiny completion, SAC/SHC response deadlines.
- **EVC Inspections**: Expert Visit Committee compliance deadlines.
- **Institutional Undertakings**: Anti-ragging, land compliance, faculty affidavits.
- **Lease Expiries**: Land and building lease deed expiries.

**Lifecycle**: `PENDING` $\to$ `SUBMITTED` $\to$ `SATISFIED` (or `BREACHED` / `WAIVED`).

### B. Escalation Policies & Alerts (`escalation_policy`, `alert`)
- Escalations define relative triggers (e.g. T-30d, T-7d, T-0d, +3d, +7d).
- The alert table enforces `UNIQUE(obligation_id, step)` to ensure complete idempotency.

### C. The Virtual Clock (`system_clock`)
- No direct calls to system time. All business logic relies on `clock.now()`.
- System offset stored in DB table `system_clock` and managed via `POST /admin/clock/advance`.

### D. Hash-Chained Audit Trail (`audit_log`)
- Every mutation records an audit entry within the *same* database transaction.
- Each row links to `prev_hash` and hashes `SHA256(prev_hash + entity + action + payload + timestamp)`.
- Tampering detection verified with `GET /audit/verify`.
