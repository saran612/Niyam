"""Tests for AICTE MOCK Import Adapter and Reconciliation."""

from datetime import timedelta

import pytest
from app.adapters.aicte_import import import_aicte_data
from app.core.clock import clock
from app.core.database import Base
from app.core.routes_config import ROUTE_TEMPLATES_SEED
from app.models.entities import (
    Application,
    Institution,
    Obligation,
    ObligationStatusEnum,
    ObligationTypeEnum,
    Region,
    RoleEnum,
    RouteTemplate,
)
from app.services.reconcile import run_nightly_reconciliation
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    r = Region(id=1, code="SRO", name="South", created_at=clock.now())
    session.add(r)

    rt = RouteTemplate(
        id=1,
        name="Only Scrutiny",
        version=1,
        stages_definition=ROUTE_TEMPLATES_SEED[0]["stages_definition"],
        is_active=True,
        created_at=clock.now(),
    )
    session.add(rt)
    session.commit()

    yield session
    session.close()


def test_mock_importer_valid_and_malformed(db):
    csv_data = """application_number,aicte_id,institution_name,region_code,address,route_name
AICTE-2026-SRO-9001,1-90010001,Green Tech Campus,SRO,MG Road Bengaluru,Only Scrutiny
AICTE-2026-SRO-9002,INVALID_ID,Faulty Tech,SRO,Brigade Road,Only Scrutiny
AICTE-2026-SRO-9003,1-90030003,Island Tech,UNKNOWN_REGION,Ocean Road,Only Scrutiny
AICTE-2026-SRO-9001,1-90010001,Duplicate Entry,SRO,Duplicate Road,Only Scrutiny
"""
    summary = import_aicte_data(db, raw_content=csv_data, file_format="csv")

    assert summary.total_processed == 4
    assert summary.successful_count == 1
    assert summary.failed_count == 3

    # Check errors recorded
    reasons = [e.error for e in summary.errors]
    assert any("AICTE ID must start with" in r for r in reasons)
    assert any("UNKNOWN_REGION" in r for r in reasons)
    assert any("Duplicate" in r for r in reasons)


def test_reconciliation_anomaly_detection(db):
    inst = Institution(id=1, aicte_id="1-1111", name="Test Inst", region_id=1, address="X", created_at=clock.now())
    db.add(inst)
    db.flush()

    app = Application(
        id=1,
        application_number="APP-RECON-1",
        institution_id=1,
        region_id=1,
        academic_year="2026-2027",
        current_stage="SCRUTINY_PENDING",
        route_template_id=1,
        status="IN_PROGRESS",
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    db.add(app)
    db.flush()

    # Obligation 1: Past due but still PENDING
    ob_past = Obligation(
        id=1,
        application_id=app.id,
        institution_id=inst.id,
        region_id=1,
        obligation_type=ObligationTypeEnum.STAGE_SLA,
        title="Overdue Obligation",
        owner_role=RoleEnum.REGIONAL_OFFICER,
        stage_key="SCRUTINY_PENDING",
        status=ObligationStatusEnum.PENDING,
        due_at=clock.now() - timedelta(days=5),
        created_at=clock.now() - timedelta(days=20),
        updated_at=clock.now() - timedelta(days=20),
    )
    # Obligation 2: Stage mismatch
    ob_mismatch = Obligation(
        id=2,
        application_id=app.id,
        institution_id=inst.id,
        region_id=1,
        obligation_type=ObligationTypeEnum.STAGE_SLA,
        title="Mismatched Stage Obligation",
        owner_role=RoleEnum.REGIONAL_OFFICER,
        stage_key="APPLICATION_SUBMITTED",  # mismatch with current_stage SCRUTINY_PENDING
        status=ObligationStatusEnum.PENDING,
        due_at=clock.now() + timedelta(days=5),
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    db.add_all([ob_past, ob_mismatch])
    db.commit()

    report = run_nightly_reconciliation(db)
    assert report.total_obligations_checked == 2
    assert report.anomalies_found >= 2
    anomaly_types = {a.anomaly_type for a in report.anomalies}
    assert "OVERDUE_UNBREACHED" in anomaly_types
    assert "STAGE_MISMATCH" in anomaly_types
