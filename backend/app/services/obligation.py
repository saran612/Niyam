"""Obligation engine service.

Creates, manages, and recomputes obligations:
- Stage SLA obligations upon stage entry
- Undertaking submission obligations
- EVC report obligations
- Lease expiry obligations
- Recomputing due_at dates when route/SLA configuration changes
"""

from app.core.clock import clock
from app.models.entities import (
    Application,
    EscalationPolicy,
    Institution,
    Obligation,
    ObligationStatusEnum,
    ObligationTypeEnum,
    RoleEnum,
    RouteTemplate,
    User,
)
from app.services.audit import record
from app.services.sla import calculate_due_date
from sqlalchemy.orm import Session


def get_default_escalation_policy(db: Session) -> EscalationPolicy | None:
    return db.query(EscalationPolicy).filter_by(name="Standard SLA Escalation Policy").first()


def create_stage_sla_obligation(
    db: Session,
    application: Application,
    stage_key: str,
    sla_days: int,
    actor: User | None = None,
) -> Obligation:
    """Create a single obligation tracking the current stage's SLA."""
    due_at = calculate_due_date(
        start_datetime=clock.now(),
        sla_business_days=sla_days,
        db=db,
        region_id=application.region_id,
    )

    escalation_policy = get_default_escalation_policy(db)

    # Determine assigned role based on stage
    if "SCRUTINY" in stage_key or "EVC" in stage_key:
        owner_role = RoleEnum.REGIONAL_OFFICER
    elif "HEARING" in stage_key or "SAC" in stage_key or "SHC" in stage_key:
        owner_role = RoleEnum.BUREAU_OFFICER
    elif "DEFICIENCY" in stage_key:
        owner_role = RoleEnum.INSTITUTION
    else:
        owner_role = RoleEnum.REGIONAL_OFFICER

    # Find candidate user for owner if exists
    owner_user = (
        db.query(User)
        .filter(User.role == owner_role, User.region_id == application.region_id)
        .first()
    )

    obligation = Obligation(
        application_id=application.id,
        institution_id=application.institution_id,
        region_id=application.region_id,
        obligation_type=ObligationTypeEnum.STAGE_SLA,
        title=f"Stage SLA: {stage_key}",
        description=f"Compliance deadline for application {application.application_number} at stage {stage_key}",
        stage_key=stage_key,
        owner_id=owner_user.id if owner_user else None,
        owner_role=owner_role,
        status=ObligationStatusEnum.PENDING,
        escalation_policy_id=escalation_policy.id if escalation_policy else None,
        due_at=due_at,
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    db.add(obligation)
    db.flush()

    record(
        db=db,
        action="OBLIGATION_CREATED",
        entity_type="obligation",
        entity_id=str(obligation.id),
        payload={
            "application_id": application.id,
            "obligation_type": ObligationTypeEnum.STAGE_SLA.value,
            "stage_key": stage_key,
            "due_at": due_at.isoformat(),
            "owner_role": owner_role.value,
        },
        actor=actor,
    )
    return obligation


def create_lease_expiry_obligation(
    db: Session,
    institution: Institution,
    actor: User | None = None,
) -> Obligation | None:
    """Generates lease expiry obligation if lease date exists."""
    if not institution.lease_expiry_date:
        return None

    # Check if existing active lease obligation exists
    existing = (
        db.query(Obligation)
        .filter(
            Obligation.institution_id == institution.id,
            Obligation.obligation_type == ObligationTypeEnum.LEASE_EXPIRY,
            Obligation.status == ObligationStatusEnum.PENDING,
        )
        .first()
    )
    if existing:
        return existing

    escalation_policy = get_default_escalation_policy(db)
    obligation = Obligation(
        application_id=None,
        institution_id=institution.id,
        region_id=institution.region_id,
        obligation_type=ObligationTypeEnum.LEASE_EXPIRY,
        title=f"Land/Building Lease Renewal: {institution.name}",
        description=f"Institutional lease expires on {institution.lease_expiry_date.strftime('%Y-%m-%d')}. Renewal documentation required.",
        stage_key="ANNUAL_COMPLIANCE",
        owner_id=None,
        owner_role=RoleEnum.INSTITUTION,
        status=ObligationStatusEnum.PENDING,
        escalation_policy_id=escalation_policy.id if escalation_policy else None,
        due_at=institution.lease_expiry_date,
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    db.add(obligation)
    db.flush()

    record(
        db=db,
        action="OBLIGATION_CREATED",
        entity_type="obligation",
        entity_id=str(obligation.id),
        payload={
            "institution_id": institution.id,
            "obligation_type": ObligationTypeEnum.LEASE_EXPIRY.value,
            "due_at": institution.lease_expiry_date.isoformat(),
        },
        actor=actor,
    )
    return obligation


def close_stage_obligations(
    db: Session,
    application_id: int,
    stage_key: str,
    actor: User | None = None,
    new_status: ObligationStatusEnum = ObligationStatusEnum.SATISFIED,
) -> int:
    """Closes open stage SLA obligations when transitioning away from stage."""
    open_obligations = (
        db.query(Obligation)
        .filter(
            Obligation.application_id == application_id,
            Obligation.stage_key == stage_key,
            Obligation.status == ObligationStatusEnum.PENDING,
        )
        .all()
    )

    count = 0
    now_ts = clock.now()
    for ob in open_obligations:
        ob.status = new_status
        ob.satisfied_at = now_ts
        ob.updated_at = now_ts
        count += 1
        record(
            db=db,
            action="OBLIGATION_CLOSED",
            entity_type="obligation",
            entity_id=str(ob.id),
            payload={"status": new_status.value, "closed_at": now_ts.isoformat()},
            actor=actor,
        )
    return count


def recompute_obligations_for_route_update(
    db: Session,
    route_template_id: int,
    new_version: int,
    actor: User | None = None,
) -> int:
    """Recomputes due_at for pending obligations when SLA days in route template change."""
    route = db.query(RouteTemplate).filter_by(id=route_template_id).first()
    if not route:
        return 0

    stage_sla_map = {
        s["stage_key"]: s.get("sla_days", 15) for s in route.stages_definition
    }

    # Find pending obligations for applications using this route template
    apps = (
        db.query(Application)
        .filter(Application.route_template_id == route_template_id)
        .all()
    )

    recomputed_count = 0
    for app in apps:
        pending_obs = (
            db.query(Obligation)
            .filter(
                Obligation.application_id == app.id,
                Obligation.status == ObligationStatusEnum.PENDING,
                Obligation.obligation_type == ObligationTypeEnum.STAGE_SLA,
            )
            .all()
        )

        for ob in pending_obs:
            if ob.stage_key in stage_sla_map:
                sla_days = stage_sla_map[ob.stage_key]
                new_due_at = calculate_due_date(
                    start_datetime=ob.created_at,
                    sla_business_days=sla_days,
                    db=db,
                    region_id=ob.region_id,
                )
                if ob.due_at != new_due_at:
                    old_due = ob.due_at
                    ob.due_at = new_due_at
                    ob.updated_at = clock.now()
                    recomputed_count += 1
                    record(
                        db=db,
                        action="OBLIGATION_RECOMPUTED",
                        entity_type="obligation",
                        entity_id=str(ob.id),
                        payload={
                            "old_due_at": old_due.isoformat(),
                            "new_due_at": new_due_at.isoformat(),
                            "reason": f"Route template version updated to {new_version}",
                        },
                        actor=actor,
                    )

    return recomputed_count
