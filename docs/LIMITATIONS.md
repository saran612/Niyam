# Prototype Limitations & Scope Clarifications

> **SIH PS 26262 Prototype Scope and Assumptions**

---

## 1. What is Mocked
1. **AICTE External ERP Ingestion (`adapters/aicte_import.py`)**:
   - The CSV/JSON importer is labelled **MOCK** and simulates institutional application batch uploads from external legacy systems.
2. **Document Object Storage**:
   - Supported with MinIO (or Zenko / S3-compatible endpoints), with fallback local directory buffering in dev setups.
3. **Email Delivery**:
   - Email notifications are routed through MailHog (`localhost:1025`) for inspection rather than live external SMTP relays.

---

## 2. What is Real and Enforced
1. **Deterministic Obligation Engine**:
   - Single `obligation` database table tracking all deadlines.
   - Business-day SLA calculator honoring regional and national holiday calendars.
2. **Cryptographic Audit Trail**:
   - Hash chain computed via SHA-256 within the same database transaction for every mutation.
   - `GET /audit/verify` actively traverses and asserts integrity.
3. **Database-Backed Worker & Locking**:
   - Background scheduler uses PostgreSQL `SELECT ... FOR UPDATE SKIP LOCKED` for concurrency and zero-duplicate guarantees.
4. **Mandatory Authorization & Workflow Rules**:
   - Mechanical stages advance deterministically; decision stages require authenticated human sign-off.
   - Reverts strictly require a non-empty textual justification (enforced via 422 HTTP responses).
5. **Strict Virtual Clock**:
   - Zero direct system time calls; everything consumes `clock.now()` with offset control.

---

## 3. Illustrative SLA & Route Configurations
- Route stages (Only Scrutiny, Scrutiny+EVC, EVC+SAC/SHC, Only EVC) and SLA day counts are configured for testing and demonstrative evaluation; live AICTE Approval Process Handbook (APH) regulations may specify different day counters for statutory phases.
