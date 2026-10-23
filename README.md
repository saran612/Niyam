# AICTE Approval & Compliance Obligation Engine (SIH PS 26262)

[![CI Status](https://github.com/aicte-compliance/engine/actions/workflows/ci.yml/badge.svg)](https://github.com/aicte-compliance/engine)
![Python](https://img.shields.io/badge/Python-3.12-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-1.0-green.svg)
![React](https://img.shields.io/badge/React-19-cyan.svg)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue.svg)

> **One platform where every deadline (stage SLA, EVC due, undertaking, lease/document expiry) is a row in a single `obligation` table with an owner, due date, status, and escalation ladder. Deterministic engine, human decides, everything audited. No ML on the critical path.**

---

## Architecture Overview

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
                                        |
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

## Key Features

1. **Single Obligation Table**: All statutory requirements, stage SLAs, EVC obligations, undertakings, and lease deed expiries are tracked in a unified `obligation` table.
2. **Deterministic Virtual Clock**: Enables reliable time travel via `POST /admin/clock/advance` to test T-30, T-7, T-0, and overdue escalations. No raw system time is consumed.
3. **Cryptographic Audit Trail**: Hash-chained audit log with `SHA256(prev_hash + entity + action + payload + timestamp)` written inside every mutation transaction. Verified via `GET /audit/verify`.
4. **Server-Side Regional Scoping**: Regional officers are strictly restricted to their designated region at the database query level.
5. **Human-in-the-Loop Decisions**: Mechanical stages auto-advance; decision stages produce suggested actions requiring authorized approval. Reverts strictly require non-empty reasons.
6. **Concurrent Scheduler Worker**: Uses PostgreSQL `SELECT ... FOR UPDATE SKIP LOCKED` for duplicate-free escalation alerting.

---

## Quickstart

### 1. Start Infrastructure and Seed Database
```bash
make up
make seed
```

### 2. Run Verification Checks & Tests
```bash
make check
make e2e
```

### 3. Run Live Interactive Demo
```bash
make demo
```

---

## Service Endpoints
- **Web UI**: [http://localhost:5173](http://localhost:5173)
- **API Documentation (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **MailHog Email Preview**: [http://localhost:8025](http://localhost:8025)

---

## Documentation
- [Architecture Details](docs/ARCHITECTURE.md)
- [Architectural Decisions (ADR)](docs/DECISIONS.md)
- [Security Model & Audits](docs/SECURITY.md)
- [Interactive Demo Script](docs/DEMO.md)
- [Prototype Limitations & Assumptions](docs/LIMITATIONS.md)
- [Hardening & Review Passes](docs/HARDENING.md)
