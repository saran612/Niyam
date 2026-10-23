"""Integration tests for Workflow Engine and Transitions."""

import pytest
from app.core.clock import clock
from app.core.database import Base
from app.core.routes_config import ROUTE_TEMPLATES_SEED
from app.models.entities import (
    Application,
    Institution,
    Region,
    RoleEnum,
    RouteTemplate,
    User,
)
from app.services.workflow import WorkflowError, transition_stage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    # Seed Region
    region = Region(id=1, code="SRO", name="South Regional Office", created_at=clock.now())
    session.add(region)

    # Seed Route Templates
    for r_seed in ROUTE_TEMPLATES_SEED:
        rt = RouteTemplate(
            name=r_seed["name"],
            version=r_seed["version"],
            description=r_seed.get("description"),
            stages_definition=r_seed["stages_definition"],
            is_active=True,
            created_at=clock.now(),
        )
        session.add(rt)

    # Seed Users
    ro = User(
        id=1,
        email="ro@aicte.gov.in",
        full_name="Regional Officer",
        password_hash="fakehash",
        role=RoleEnum.REGIONAL_OFFICER,
        region_id=1,
        created_at=clock.now(),
    )
    inst_user = User(
        id=2,
        email="inst@college.edu",
        full_name="Institution Dean",
        password_hash="fakehash",
        role=RoleEnum.INSTITUTION,
        region_id=1,
        created_at=clock.now(),
    )
    session.add_all([ro, inst_user])

    # Seed Institution
    inst = Institution(
        id=1,
        aicte_id="1-12345678",
        name="Apex Institute of Technology",
        region_id=1,
        address="100 Tech Park, Bengaluru",
        created_at=clock.now(),
    )
    session.add(inst)
    session.commit()

    yield session
    session.close()


def test_mechanical_intake_auto_advances(db):
    route = db.query(RouteTemplate).filter_by(name="Only Scrutiny").first()
    app = Application(
        application_number="APP-2026-001",
        institution_id=1,
        region_id=1,
        academic_year="2026-2027",
        current_stage="APPLICATION_SUBMITTED",
        route_template_id=route.id,
        status="IN_PROGRESS",
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    db.add(app)
    db.commit()

    # Auto-advance mechanical stage
    updated_app, tr = transition_stage(
        db=db,
        application=app,
        target_stage="APPLICATION_SUBMITTED",
        action="ADVANCE",
    )
    db.commit()

    # Mechanical stage APPLICATION_SUBMITTED auto-advances to SCRUTINY_PENDING
    assert updated_app.current_stage == "SCRUTINY_PENDING"
    assert updated_app.status == "IN_PROGRESS"


def test_revert_without_reason_rejected(db):
    route = db.query(RouteTemplate).filter_by(name="Only Scrutiny").first()
    app = Application(
        application_number="APP-2026-002",
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

    ro_user = db.query(User).filter_by(role=RoleEnum.REGIONAL_OFFICER).first()

    # Attempt revert with empty reason -> must fail with 422
    with pytest.raises(WorkflowError) as exc_info:
        transition_stage(
            db=db,
            application=app,
            target_stage="REVERTED_TO_DEFICIENCY",
            action="REVERT",
            actor=ro_user,
            reason="",
        )
    assert exc_info.value.status_code == 422
    assert "non-empty reason" in exc_info.value.message

    # Attempt revert with valid reason -> succeeds
    updated_app, tr = transition_stage(
        db=db,
        application=app,
        target_stage="REVERTED_TO_DEFICIENCY",
        action="REVERT",
        actor=ro_user,
        reason="Fire safety certificate expired, please upload renewed certificate.",
    )
    db.commit()
    assert updated_app.current_stage == "REVERTED_TO_DEFICIENCY"
    assert tr.reason == "Fire safety certificate expired, please upload renewed certificate."


def test_unauthorized_actor_rejected(db):
    route = db.query(RouteTemplate).filter_by(name="Only Scrutiny").first()
    app = Application(
        application_number="APP-2026-003",
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

    inst_user = db.query(User).filter_by(role=RoleEnum.INSTITUTION).first()

    # Institution cannot approve or advance scrutiny stage
    with pytest.raises(WorkflowError) as exc_info:
        transition_stage(
            db=db,
            application=app,
            target_stage="APPROVED",
            action="ADVANCE",
            actor=inst_user,
        )
    assert exc_info.value.status_code == 403
