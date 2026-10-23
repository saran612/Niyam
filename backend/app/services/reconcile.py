"""Nightly reconciliation service for obligations.

Audits and identifies:
1. Active obligations lacking an assigned owner or role
2. Obligations whose stage does not match their application's current stage
3. Past-due obligations erroneously marked PENDING instead of BREACHED
4. Broken foreign keys or orphan obligations
Outputs an anomaly report and audit entry.
"""

from app.core.clock import clock
from app.models.entities import Application, Obligation, ObligationStatusEnum
from app.services.audit import record
from pydantic import BaseModel
from sqlalchemy.orm import Session


class ReconciliationAnomaly(BaseModel):
    obligation_id: int
    anomaly_type: str
    details: str


class ReconciliationReport(BaseModel):
    run_timestamp: str
    total_obligations_checked: int
    anomalies_found: int
    anomalies: list[ReconciliationAnomaly] = []


def run_nightly_reconciliation(db: Session) -> ReconciliationReport:
    """Scans all obligations and flags state discrepancies or missing ownership."""
    now_ts = clock.now()
    obligations = db.query(Obligation).all()

    anomalies: list[ReconciliationAnomaly] = []

    for ob in obligations:
        # Check 1: Missing owner role
        if not ob.owner_role:
            anomalies.append(
                ReconciliationAnomaly(
                    obligation_id=ob.id,
                    anomaly_type="MISSING_OWNER_ROLE",
                    details=f"Obligation {ob.id} has no owner_role specified.",
                )
            )

        # Check 2: Past-due still in PENDING status
        due_at = ob.due_at if ob.due_at.tzinfo else ob.due_at.replace(tzinfo=now_ts.tzinfo)
        if ob.status == ObligationStatusEnum.PENDING and now_ts > due_at:
            anomalies.append(
                ReconciliationAnomaly(
                    obligation_id=ob.id,
                    anomaly_type="OVERDUE_UNBREACHED",
                    details=f"Obligation {ob.id} is overdue since {ob.due_at.isoformat()} but status is still PENDING.",
                )
            )

        # Check 3: Stage mismatch with application
        if ob.application_id and ob.stage_key:
            app = db.query(Application).filter_by(id=ob.application_id).first()
            if not app:
                anomalies.append(
                    ReconciliationAnomaly(
                        obligation_id=ob.id,
                        anomaly_type="ORPHAN_APPLICATION_REFERENCE",
                        details=f"Application ID {ob.application_id} does not exist.",
                    )
                )
            elif (
                ob.status == ObligationStatusEnum.PENDING
                and ob.stage_key != app.current_stage
                and app.status == "IN_PROGRESS"
            ):
                anomalies.append(
                    ReconciliationAnomaly(
                        obligation_id=ob.id,
                        anomaly_type="STAGE_MISMATCH",
                        details=f"Obligation stage '{ob.stage_key}' does not match application current stage '{app.current_stage}'.",
                    )
                )

    report = ReconciliationReport(
        run_timestamp=now_ts.isoformat(),
        total_obligations_checked=len(obligations),
        anomalies_found=len(anomalies),
        anomalies=anomalies,
    )

    record(
        db=db,
        action="NIGHTLY_RECONCILIATION_RUN",
        entity_type="reconciliation",
        entity_id="1",
        payload={
            "total_checked": report.total_obligations_checked,
            "anomalies_count": report.anomalies_found,
            "anomalies": [a.model_dump() for a in report.anomalies],
        },
    )
    db.commit()

    return report
