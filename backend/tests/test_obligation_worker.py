"""Integration tests for Obligation Engine and Escalation Worker."""

from datetime import timedelta

import pytest
from app.core.clock import clock
from app.core.database import Base
from app.core.routes_config import ESCALATION_POLICY_SEED, ROUTE_TEMPLATES_SEED
from app.models.entities import (
    Alert,
    Application,
    EscalationPolicy,
    Institution,
    Obligation,
    ObligationStatusEnum,
    ObligationTypeEnum,
    Region,
    RoleEnum,
    RouteTemplate,
    User,
)
from app.services.obligation import (
    create_lease_expiry_obligation,
    create_stage_sla_obligation,
    recompute_obligations_for_route_update,
)
from app.workers.scheduler import process_escalations_batch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    region = Region(id=1, code="WRO", name="Western Regional Office", created_at=clock.now())
    session.add(region)

    for p in ESCALATION_POLICY_SEED:
        pol = EscalationPolicy(
            name=p["name"],
            version=p["version"],
            steps=p["steps"],
            created_at=clock.now(),
        )
        session.add(pol)

    for r_seed in ROUTE_TEMPLATES_SEED:
        rt = RouteTemplate(
            name=r_seed["name"],
            version=r_seed["version"],
            stages_definition=r_seed["stages_definition"],
            is_active=True,
            created_at=clock.now(),
        )
        session.add(rt)

    ro = User(
        id=1,
        email="ro.wro@aicte.gov.in",
        full_name="RO Western",
        password_hash="fake",
        role=RoleEnum.REGIONAL_OFFICER,
        region_id=1,
        created_at=clock.now(),
    )
    bureau = User(
        id=2,
        email="bureau@aicte.gov.in",
        full_name="Bureau Officer",
        password_hash="fake",
        role=RoleEnum.BUREAU_OFFICER,
        region_id=1,
        created_at=clock.now(),
    )
    session.add_all([ro, bureau])

    inst = Institution(
        id=1,
        aicte_id="1-99999",
        name="Mumbai Engineering College",
        region_id=1,
        address="Dadar, Mumbai",
        lease_expiry_date=clock.now() + timedelta(days=20),
        created_at=clock.now(),
    )
    session.add(inst)
    session.commit()

    yield session
    session.close()


def test_lease_expiry_obligation_generation(db):
    inst = db.query(Institution).first()
    ob = create_lease_expiry_obligation(db, inst)
    db.commit()

    assert ob is not None
    assert ob.obligation_type == ObligationTypeEnum.LEASE_EXPIRY
    assert ob.status == ObligationStatusEnum.PENDING
    assert ob.due_at == inst.lease_expiry_date


def test_scheduler_escalation_and_idempotency(db):
    inst = db.query(Institution).first()
    pol = db.query(EscalationPolicy).first()

    # Create obligation due in 5 days
    # Policy steps: T-30 (due-30d), T-7 (due-7d), T-0 (due-0d), OVERDUE_3D, OVERDUE_7D
    # Since today is due-5d:
    #   T-30 triggered at due-30d (which is in the past -> should fire)
    #   T-7 triggered at due-7d (which is in the past -> should fire)
    #   T-0 not yet reached
    ob = Obligation(
        institution_id=inst.id,
        region_id=inst.region_id,
        obligation_type=ObligationTypeEnum.STAGE_SLA,
        title="Stage Review SLA",
        owner_role=RoleEnum.REGIONAL_OFFICER,
        status=ObligationStatusEnum.PENDING,
        escalation_policy_id=pol.id,
        due_at=clock.now() + timedelta(days=5),
        created_at=clock.now() - timedelta(days=10),
        updated_at=clock.now() - timedelta(days=10),
    )
    db.add(ob)
    db.commit()

    # Run scheduler first time
    fired_first = process_escalations_batch(db)
    assert fired_first == 2  # T-30 and T-7

    alerts = db.query(Alert).filter_by(obligation_id=ob.id).all()
    assert len(alerts) == 2
    steps = {a.step for a in alerts}
    assert steps == {"T-30", "T-7"}

    # Run scheduler second time (idempotency check)
    fired_second = process_escalations_batch(db)
    assert fired_second == 0  # Zero duplicate alerts fired

    total_alerts = db.query(Alert).filter_by(obligation_id=ob.id).count()
    assert total_alerts == 2


def test_sla_config_change_recomputes_obligations(db):
    route = db.query(RouteTemplate).filter_by(name="Only Scrutiny").first()
    app = Application(
        application_number="APP-RECOMPUTE-01",
        institution_id=1,
        region_id=1,
        academic_year="2026-2027",
        current_stage="SCRUTINY_PENDING",
        route_template_id=route.id,
        status="IN_PROGRESS",
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    db.add(app)
    db.commit()

    ob = create_stage_sla_obligation(db, app, stage_key="SCRUTINY_PENDING", sla_days=15)
    db.commit()
    original_due = ob.due_at

    # Update route definition SLA from 15 to 25 days
    new_stages = []
    for s in route.stages_definition:
        if s["stage_key"] == "SCRUTINY_PENDING":
            s_copy = dict(s)
            s_copy["sla_days"] = 25
            new_stages.append(s_copy)
        else:
            new_stages.append(s)
    route.stages_definition = new_stages
    db.commit()

    recomputed = recompute_obligations_for_route_update(
        db, route_template_id=route.id, new_version=2
    )
    db.commit()

    assert recomputed == 1
    reloaded_ob = db.query(Obligation).filter_by(id=ob.id).first()
    assert reloaded_ob.due_at > original_due
