# AICTE Approval & Compliance Engine Implementation Backlog ("Niyam")

## Priority 0 (P0): Engine Correctness, Safeguards & Security
- [ ] **P0-SEC-1**: Add Rate Limiting & Strict Security Headers Middleware (`app/main.py`)
- [ ] **P0-DOC-1**: Wire Document Upload File Picker Modal in Institution Dashboard (`InstitutionDashboard.tsx`)
- [x] **P0-WF-1**: Regional Role Query Scoping for Audit Trail Endpoint (`endpoints.py`, `deps.py`, `test_ro_can_access_audit_logs`)

## Priority 1 (P1): Dashboards, Reports, Automation & AI
- [ ] **P1-RPT-1**: Implement CSV/PDF Pendency & Compliance Report Export Service (`app/api/endpoints.py`, `app/services/reports.py`)
- [ ] **P1-DSH-1**: Build Committee Hearing & Scrutiny Evaluation Dashboard (`CommitteeDashboard.tsx`, `App.tsx`)
- [ ] **P1-DSH-2**: Regional Workload & Regional Breakdown Comparative View in Bureau Dashboard (`BureauDashboard.tsx`)
- [ ] **P1-WF-2**: Deterministic Case Summary & Jinja2 Notice Generator (`app/services/notices.py`, `CaseDetailView.tsx`)
- [ ] **P1-OCR-1**: Document OCR Date Extraction with Human Verification Interface (`app/services/ocr.py`, `CaseDetailView.tsx`)
- [ ] **P1-AI-1**: Advisory Breach-Risk Scoring Engine with Reason Codes (`app/services/risk.py`, `CaseDetailView.tsx`)
- [ ] **P1-AI-2**: Advisory RAG Copilot with APH (Approval Process Handbook) Clause Citations (`app/services/copilot.py`)

## Priority 2 (P2): UI Polish, Hardening & Documentation
- [ ] **P2-POL-1**: Comprehensive Responsive & Visual Hygiene Audit (No slop, clean spacing, a11y)
- [ ] **P2-DOC-1**: End-to-End Demo Script (`make demo`), Screenshots, and Final Hardening Report
