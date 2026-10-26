# Frontend Page-by-Page Audit

Date: 2026-10-26  
Status: READ-ONLY AUDIT (Phase A)  
Frontend Base: React 19 + TypeScript + Vite + Tailwind CSS v4

---

## 1. Route & View Inventory

The frontend is an authenticated Single Page Application governed by `frontend/src/App.tsx`. The views are mapped dynamically based on the authenticated user's `role` and the selected tab/application state.

| Page / Route / View | Role(s) | Sections Present | Data Source | Status | Evidence | Defects & Slop Flags |
|---|---|---|---|---|---|---|
| **Login Screen** (`/`) | Public / Unauthenticated | Header with AICTE crest, Email input, Password input, Error badge, Submit button, Demo credentials quick-picker | Real API (`POST /api/auth/login`) | **DONE** | Screenshot: `audit/screenshots/01_login_page.png`; File: `frontend/src/App.tsx:78-142` | None. Clean, centered card, clear validation errors. |
| **Virtual Clock Top Bar** (Global header) | All authenticated roles | Running virtual clock indicator, UTC timestamp display, Offset badge in days/seconds, Advance dropdown (+1d, +7d, +14d, +30d), Advance button, Reset button | Real API (`GET /admin/clock/status`, `POST /admin/clock/advance`, `POST /admin/clock/reset`) | **DONE** | File: `frontend/src/components/VirtualClockBar.tsx`; App.tsx:147; Test: `frontend/tests/e2e.spec.ts:64-96` | Restricted in backend to Admin only (`403` if clicked by RO/Institution), but Advance/Reset buttons remain visible in UI for non-admin roles (shows browser `alert` on failure). |
| **Regional Officer Dashboard** (`#tab-dashboard`) | `regional_officer` | Metric cards (Assigned Applications, Active Stage SLAs, Breached Deadlines, Scrutiny Backlog), Applications table with filters, stage badges, SLA countdowns, "Review Case" actions | Real API (`GET /api/applications`, `GET /api/obligations`) | **DONE** | Screenshot: `audit/screenshots/02_regional_dashboard.png`; File: `frontend/src/components/RegionalDashboard.tsx` | Missing CSV/PDF export button. Missing officer workload distribution table. |
| **Case Detail View** (`#case-detail/:id`) | `regional_officer`, `bureau_officer`, `admin` | Application meta header (number, academic year, region), Stage history timeline, Active SLA obligation card, Workflow action buttons ("Advance to Next Stage", "Revert to Deficiency"), Revert reason modal/form | Real API (`GET /api/applications/:id`, `POST /api/applications/:id/advance`, `POST /api/applications/:id/revert`) | **DONE** | Screenshot: `audit/screenshots/03_case_detail_view.png`; File: `frontend/src/components/CaseDetailView.tsx`; E2E test `e2e.spec.ts:4-36` | Missing deterministic Jinja2 notice/case summary preview. Missing OCR date extractor human verify widget. |
| **Bureau Officer / Admin Dashboard** (`#tab-dashboard`) | `bureau_officer`, `admin` | Top banner with national statistics, Metric cards (National Stage Pendency, National SLA Breaches, Throughput), Stage Distribution Recharts bar chart, National pendency table | Real API (`GET /api/applications`, `GET /api/obligations`) | **DONE** | Screenshot: `audit/screenshots/05_bureau_dashboard.png`; File: `frontend/src/components/BureauDashboard.tsx` | Missing region-by-region comparative breakdown table. Missing PDF/CSV report generation download trigger. |
| **Institution Portal** (`#tab-dashboard`) | `institution` | Affiliated campus banner, Application reference & current status, Mandatory Compliance Deadlines table, Obligation type & due date badges, Upload / Satisfy action buttons | Real API (`GET /api/obligations`, `GET /api/applications`, `POST /api/obligations/:id/satisfy`) | **PARTIAL** | Screenshot: `audit/screenshots/06_institution_dashboard.png`; File: `frontend/src/components/InstitutionDashboard.tsx` | Document file upload form is in backend (`POST /api/documents/upload`), but UI button directly calls `satisfy` without file picker modal. |
| **Cryptographic Audit Explorer** (`#tab-audit`) | `admin`, `bureau_officer`, `regional_officer` | Chain integrity banner (SHA-256 verification status, log count), Re-verify chain button, Immutable audit trail table (action, entity, timestamp, current hash, previous hash) | Real API (`GET /api/audit/logs`, `GET /api/audit/verify`) | **DONE** | Screenshot: `audit/screenshots/04_audit_explorer.png`; File: `frontend/src/components/AuditExplorer.tsx` | Backend restricts `GET /api/audit/logs` to Admin and Bureau Officer (`403` for Regional Officer); Regional Officer clicking Audit tab gets alert error while `verify` endpoint succeeds. |
| **Committee Dashboard** | `committee` | Dedicated committee hearing and evaluation view | None (Falls back to Institution default or generic view) | **MISSING** | `frontend/src/App.tsx:210-214` checks only `regional_officer`, `bureau_officer`, `admin`, else renders `InstitutionDashboard`. | Dedicated committee hearing interface is missing. |

---

## 2. Layout Slop, Visual Hygiene & A11y Review

- **Color Palette & Styling**: Uses slate neutral tones (`bg-slate-50`, `bg-slate-900`, `text-slate-700`) with blue-700 accent. Clean government-tier aesthetic; no random gradient slop or card-in-card nesting.
- **Micro-states**:
  - Loading states: Implemented across all components (`#loading-state`, monospace loading text).
  - Empty states: Implemented in tables when `applications.length === 0` or `obligations.length === 0`.
  - Error states: Implemented with alert banners (`bg-red-50 border-red-200 text-red-700`).
- **A11y & Controls**:
  - All interactive buttons and inputs have explicit IDs (e.g., `#btn-login-submit`, `#login-email-input`, `#tab-dashboard`, `#tab-audit`, `#btn-advance-clock`).
  - Forms prevent submission when mandatory fields (such as revert reason) are missing.
