"""Workflow transition engine.

Handles deterministic workflow execution across route templates:
- Mechanical stages auto-advance automatically upon entry.
- Decision stages produce a `suggested_action` and require an authorized user action.
- Reverting to a previous stage requires a mandatory non-empty reason (raises ValueError/422).
- Closes old stage obligations and opens new stage obligations inside the same transaction.
"""

from typing import Any

from app.core.clock import clock
from app.models.entities import (
    Application,
    RoleEnum,
    RouteTemplate,
    StageTransition,
    User,
)
from app.services.audit import record
from app.services.obligation import (
    close_stage_obligations,
    create_stage_sla_obligation,
)
from sqlalchemy.orm import Session


class WorkflowError(Exception):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def get_stage_config(
    route: RouteTemplate, stage_key: str
) -> dict[str, Any] | None:
    for stage in route.stages_definition:
        if stage["stage_key"] == stage_key:
            return stage
    return None


def transition_stage(
    db: Session,
    application: Application,
    target_stage: str,
    action: str,  # ADVANCE, REVERT, APPROVE, REJECT
    actor: User | None = None,
    reason: str | None = None,
) -> tuple[Application, StageTransition]:
    """Execute a workflow stage transition with strict validation."""
    current_stage = application.current_stage
    route = db.query(RouteTemplate).filter_by(id=application.route_template_id).first()
    if not route:
        raise WorkflowError("Route template not found for application", status_code=404)

    curr_cfg = get_stage_config(route, current_stage)
    target_cfg = get_stage_config(route, target_stage)

    if not curr_cfg or not target_cfg:
        raise WorkflowError(f"Invalid stage configuration for transition {current_stage} -> {target_stage}", status_code=400)

    # 1. Revert validation: reason must be non-empty string
    if action == "REVERT":
        if not reason or not reason.strip():
            raise WorkflowError("Revert transition requires a non-empty reason", status_code=422)

    # 2. Authorization check if human decision
    if not curr_cfg.get("is_mechanical", False):
        if actor is None:
            raise WorkflowError("Human decision stage requires an authorized user", status_code=403)
        allowed_roles = curr_cfg.get("allowed_roles", [])
        if actor.role.value not in allowed_roles and actor.role != RoleEnum.ADMIN:
            raise WorkflowError(
                f"Role {actor.role.value} is not authorized to act on stage {current_stage}",
                status_code=403,
            )

    # 3. Close open obligations for the current stage
    close_stage_obligations(db=db, application_id=application.id, stage_key=current_stage, actor=actor)

    # 4. Update application state
    application.current_stage = target_stage
    application.updated_at = clock.now()

    if target_stage == "APPROVED":
        application.status = "APPROVED"
        application.suggested_action = None
    elif target_stage == "REJECTED":
        application.status = "REJECTED"
        application.suggested_action = None
    else:
        application.status = "IN_PROGRESS"
        # Determine suggested action for next stage
        next_stages = target_cfg.get("next_stages", [])
        application.suggested_action = next_stages[0] if next_stages else None

    # 5. Create stage SLA obligation for the newly entered stage
    sla_days = target_cfg.get("sla_days", 15)
    create_stage_sla_obligation(
        db=db,
        application=application,
        stage_key=target_stage,
        sla_days=sla_days,
        actor=actor,
    )

    # 6. Record stage transition
    transition = StageTransition(
        application_id=application.id,
        from_stage=current_stage,
        to_stage=target_stage,
        transition_type=action,
        performed_by_id=actor.id if actor else None,
        reason=reason.strip() if reason else None,
        created_at=clock.now(),
    )
    db.add(transition)
    db.flush()

    record(
        db=db,
        action="STAGE_TRANSITION",
        entity_type="application",
        entity_id=str(application.id),
        payload={
            "from_stage": current_stage,
            "to_stage": target_stage,
            "transition_type": action,
            "reason": reason,
            "actor": actor.email if actor else "SYSTEM_AUTOMATION",
        },
        actor=actor,
    )

    # 7. Check if target stage is mechanical -> recursively auto-advance
    if target_cfg.get("is_mechanical", False) and target_cfg.get("auto_advance_target"):
        auto_target = target_cfg["auto_advance_target"]
        return transition_stage(
            db=db,
            application=application,
            target_stage=auto_target,
            action="ADVANCE",
            actor=None,
            reason="Automated mechanical advance",
        )

    return application, transition
