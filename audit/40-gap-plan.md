# Gap Plan & Execution Backlog

Date: 2026-10-26  
Status: READ-ONLY AUDIT (Phase A)  
Platform: AICTE Approval Workflow & Compliance Monitoring Platform ("Niyam")

Every non-DONE row from the Spec Conformance Matrix and Page Audit has been converted into a concrete task with ID, size, dependencies, acceptance test, and priority tier (P0 = engine correctness & security, P1 = dashboards, reports & AI, P2 = polish & docs).

---

## Task Inventory

| Task ID | Title / Scope | Size | Priority | Dependencies | Acceptance Test (Command + Expected Output) |
|---|---|---|---|---|---|
| **P0-SEC-1** | Add Rate Limiting & Strict Security Headers Middleware | M | **P0** | None | `curl -i http://localhost:8000/api/auth/login` includes `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Strict-Transport-Security`, and rapid repeated requests return `429 Too Many Requests`. |
| **P0-DOC-1** | Fix Document Upload UI Wiring & File Picker in Institution Dashboard | M | **P0** | None | Playwright test: Log in as Institution (`dean.inst001@aicte-india.org`), click upload on an undertaking, select a valid PDF file, submit -> `POST /api/documents/upload` returns 200, document appears in database and obligation advances/satisfies. |
| **P0-WF-1** | Regional Role Authorization on Audit Logs Endpoint | S | **P0** | None | `curl -H "Authorization: Bearer <ro_token>" http://localhost:8000/api/audit/logs` returns 200 with regional scoped logs instead of 403 error, or UI suppresses the tab cleanly for RO. |
| **P1-RPT-1** | CSV & PDF Report Export Service | L | **P1** | None | `curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/reports/pendency?format=csv` returns 200 with `Content-Type: text/csv` containing headers `application_number,current_stage,days_pending,due_at`. |
| **P1-DSH-1** | Committee Role Dedicated Dashboard | M | **P1** | None | Log in as Committee (`committee@aicte-india.org`) -> redirected to Committee hearing / scrutiny view displaying pending scrutiny cases, document inspection modal, and decision recommendation buttons. |
| **P1-DSH-2** | Regional Workload & Regional Breakdown Comparative View in Bureau Dashboard | M | **P1** | None | Bureau Dashboard displays a regional pendency breakdown table (CRO, NRO, NWRO, SRO, WRO) with officer workload distribution and average turnaround days. |
| **P1-WF-2** | Deterministic Case Summary & Notice Generator (Jinja2) | M | **P1** | None | `PYTHONPATH=backend backend/.venv/bin/pytest backend/tests/test_notices.py` passes; generating notice for an application outputs rendered HTML/PDF with application number, institution name, hearing date, and deficiency list. |
| **P1-AI-1** | Advisory Breach-Risk Scoring Engine with Reason Codes | L | **P1** | None | `GET /api/applications/:id/risk` returns `{"risk_score": 0.85, "risk_level": "HIGH", "reason_codes": ["LEASE_EXPIRING_SOON", "HISTORICAL_DEFICIENCY_REVERT"]}`. Verified advisory-only: state is never automatically advanced. |
| **P1-AI-2** | Advisory RAG Copilot with APH (Approval Process Handbook) Clause Citations | L | **P1** | P1-AI-1 | `POST /api/copilot/query` with `{"clause_query": "land requirement for technical campus"}` returns relevant APH citations (e.g. "APH 2026-27 Clause 2.3.1: Land Requirement in Urban Areas"). Audit log records model version and query. |
| **P1-OCR-1** | Document OCR Date Extraction with Human Verification Widget | M | **P1** | P0-DOC-1 | Uploading a lease deed document extracts the expiry date via regex/OCR pattern matcher; displays in UI with confidence score and an explicit human confirmation button before updating `lease_expiry_date`. |
| **P2-POL-1** | UI Polish & Consistency Audit across Screen Sizes | S | **P2** | P1-DSH-1 | Mobile/tablet responsive check passes on 375px and 768px viewports with zero horizontal overflow, consistent 4px/8px grid spacing, and strict color tokens. |
| **P2-DOC-1** | Complete User Demo & Limitations Guide | S | **P2** | All P0/P1 | Run `make demo` script cleanly from fresh checkout; update `docs/DEMO.md` with step-by-step screenshots and click-through walkthrough. |
