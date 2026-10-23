"""Background scheduler worker.

Polls obligations requiring escalation alerts using:
    SELECT ... WHERE due_at - offset <= clock.now() AND step not fired ... FOR UPDATE SKIP LOCKED
Inserts alerts, routes by role + region via escalation_policy, sends mock email/in-app notification.
Strictly idempotent: running worker twice or restarting mid-batch creates zero duplicate alerts.
"""

import logging
from datetime import UTC, timedelta

from app.core.clock import clock
from app.core.database import SessionLocal
from app.models.entities import (
    Alert,
    EscalationPolicy,
    Obligation,
    ObligationStatusEnum,
    RoleEnum,
    User,
)
from app.services.audit import record
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


def process_escalations_batch(db: Session, batch_size: int = 50) -> int:
    """Processes a single batch of obligations and triggers escalation ladder steps.

    Guarantees concurrency safety via FOR UPDATE SKIP LOCKED and idempotency
    via UNIQUE(obligation_id, step) on table alerts.
    """
    now_ts = clock.now()

    # Query obligations that are pending and have an escalation policy
    # We use SKIP LOCKED to allow multiple concurrent scheduler workers safely
    pending_obligations = (
        db.query(Obligation)
        .filter(Obligation.status == ObligationStatusEnum.PENDING)
        .filter(Obligation.escalation_policy_id.isnot(None))
        .with_for_update(skip_locked=True)
        .limit(batch_size)
        .all()
    )

    alerts_generated = 0

    for ob in pending_obligations:
        policy = (
            db.query(EscalationPolicy)
            .filter_by(id=ob.escalation_policy_id)
            .first()
        )
        if not policy or not policy.steps:
            continue

        for step_cfg in policy.steps:
            step_name = step_cfg["step"]
            offset_days = step_cfg.get("offset_days", 0)
            target_role_str = step_cfg.get("target_role", "regional_officer")
            step_msg = step_cfg.get("message", f"Obligation alert for step {step_name}")

            # Trigger condition: due_at + offset_days <= now_ts
            due_at_utc = ob.due_at if ob.due_at.tzinfo else ob.due_at.replace(tzinfo=UTC)
            trigger_time = due_at_utc + timedelta(days=offset_days)

            if now_ts >= trigger_time:
                # Check if this alert step has already fired
                existing_alert = (
                    db.query(Alert)
                    .filter_by(obligation_id=ob.id, step=step_name)
                    .first()
                )
                if existing_alert:
                    continue  # Idempotent: already fired, skip

                target_role = RoleEnum(target_role_str)
                # Find target user in this region
                target_user = (
                    db.query(User)
                    .filter(User.role == target_role, User.region_id == ob.region_id)
                    .first()
                )

                # Insert alert
                alert = Alert(
                    obligation_id=ob.id,
                    step=step_name,
                    target_role=target_role,
                    target_user_id=target_user.id if target_user else None,
                    channel="EMAIL_AND_INAPP",
                    status="SENT",
                    message=f"[{step_name}] {ob.title}: {step_msg}",
                    fired_at=now_ts,
                )
                db.add(alert)
                db.flush()

                record(
                    db=db,
                    action="ALERT_TRIGGERED",
                    entity_type="alert",
                    entity_id=str(alert.id),
                    payload={
                        "obligation_id": ob.id,
                        "step": step_name,
                        "target_role": target_role.value,
                        "offset_days": offset_days,
                    },
                )

                alerts_generated += 1

                # If overdue and now_ts > due_at, mark obligation breached
                if now_ts > due_at_utc and ob.status == ObligationStatusEnum.PENDING:
                    ob.status = ObligationStatusEnum.BREACHED
                    ob.updated_at = now_ts
                    record(
                        db=db,
                        action="OBLIGATION_BREACHED",
                        entity_type="obligation",
                        entity_id=str(ob.id),
                        payload={"breached_at": now_ts.isoformat(), "due_at": due_at_utc.isoformat()},
                    )

    db.commit()
    return alerts_generated


def run_scheduler_loop(poll_interval_seconds: int = 5, max_iterations: int | None = None) -> None:
    """Worker loop entry point."""
    import time
    logger.info("Starting AICTE obligation escalation scheduler worker...")
    iterations = 0
    while max_iterations is None or iterations < max_iterations:
        with SessionLocal() as db:
            try:
                fired = process_escalations_batch(db)
                if fired > 0:
                    logger.info("Fired %d escalation alerts at %s", fired, clock.now())
            except Exception as e:
                logger.error("Error in scheduler batch: %s", e)
                db.rollback()
        iterations += 1
        time.sleep(poll_interval_seconds)


if __name__ == "__main__":
    run_scheduler_loop()
