# AICTE Approval & Compliance Engine - Demo Script

> **Interactive demonstration script for SIH PS 26262.**

---

## Prerequisites
Ensure services and seed data are initialized:
```bash
make up
make seed
```
Access the application:
- **Frontend Web UI**: http://localhost:5173
- **Backend API Docs**: http://localhost:8000/docs
- **MailHog UI**: http://localhost:8025

---

## Click-by-Click Demo Flows

### Step 1: Regional Isolation & Region Scoping
1. Navigate to http://localhost:5173 and log in as the **South Regional Officer**:
   - **Email**: `ro.sro@aicte-india.org`
   - **Password**: `aicte@2026`
2. **Observe**: The dashboard displays applications scoped exclusively to the South Region (`SRO`).
3. **Verify**: Note that North Region (`NRO`) or Central Region (`CRO`) records are invisible. Attempting to fetch an external region application via direct API call returns `404 Not Found`.

---

### Step 2: Decision Stage & Mandatory Revert Reason
1. Under the assigned queue, select an application in `SCRUTINY_PENDING`.
2. Click **Revert / Deficiency**.
3. Leave the reason empty and click **Confirm Revert**.
   - **Observe**: The system rejects the action with `422 Unprocessable Entity` (reason is mandatory).
4. Enter reason: `"Deficiency: Building safety certificate not certified by municipal engineer."`
5. Click **Confirm Revert**.
   - **Observe**: Application transitions to `REVERTED_TO_DEFICIENCY`, creating a rectification obligation with assigned SLA.

---

### Step 3: Virtual Clock Advance & Deterministic Escalations
1. Log in as **System Administrator**:
   - **Email**: `admin@aicte-india.org`
   - **Password**: `aicte@2026`
2. In the top Virtual Time controller, select **+30 Days** and click **Advance Time**.
3. **Observe**:
   - The virtual clock advances across 30 calendar days.
   - Stage SLAs and pending undertakings transition to `BREACHED`.
   - The scheduler worker fires escalation ladder notifications (`T-30`, `T-7`, `T-0`, `OVERDUE`).
4. Open http://localhost:8025 (MailHog) to observe simulated escalation emails sent to institutional and bureau stakeholders.

---

### Step 4: Cryptographic Audit Trail Verification
1. Open the **Audit Explorer** tab.
2. View the hash-chained audit records with `prev_hash` and `hash`.
3. Click **Verify Chain Integrity**.
   - **Result**: `Valid: true` with zero corrupted blocks.
