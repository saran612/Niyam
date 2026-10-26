"""Integration tests for Authentication, Roles, and Region-Scoping security."""

import pytest
from app.core.auth import hash_password
from app.core.clock import clock
from app.core.database import Base, get_db
from app.core.routes_config import ROUTE_TEMPLATES_SEED
from app.main import app
from app.models.entities import (
    Application,
    Institution,
    Region,
    RoleEnum,
    RouteTemplate,
    User,
)
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture
def test_env():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()

    # Create 2 regions
    r1 = Region(id=1, code="SRO", name="South", created_at=clock.now())
    r2 = Region(id=2, code="NRO", name="North", created_at=clock.now())
    db.add_all([r1, r2])

    # Route template
    rt = RouteTemplate(
        id=1,
        name="Only Scrutiny",
        version=1,
        stages_definition=ROUTE_TEMPLATES_SEED[0]["stages_definition"],
        is_active=True,
        created_at=clock.now(),
    )
    db.add(rt)

    # Institutions
    i1 = Institution(id=1, aicte_id="INST-1", name="College South", region_id=1, address="BLR", created_at=clock.now())
    i2 = Institution(id=2, aicte_id="INST-2", name="College North", region_id=2, address="DEL", created_at=clock.now())
    db.add_all([i1, i2])

    # Users
    u_ro1 = User(
        id=1,
        email="ro.south@aicte.gov.in",
        full_name="South RO",
        password_hash=hash_password("secret123"),
        role=RoleEnum.REGIONAL_OFFICER,
        region_id=1,
        created_at=clock.now(),
    )
    u_admin = User(
        id=2,
        email="admin@aicte.gov.in",
        full_name="System Admin",
        password_hash=hash_password("admin123"),
        role=RoleEnum.ADMIN,
        created_at=clock.now(),
    )
    db.add_all([u_ro1, u_admin])

    # Applications
    app1 = Application(
        id=1,
        application_number="APP-SOUTH-001",
        institution_id=1,
        region_id=1,
        academic_year="2026-2027",
        current_stage="SCRUTINY_PENDING",
        route_template_id=1,
        status="IN_PROGRESS",
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    app2 = Application(
        id=2,
        application_number="APP-NORTH-002",
        institution_id=2,
        region_id=2,
        academic_year="2026-2027",
        current_stage="SCRUTINY_PENDING",
        route_template_id=1,
        status="IN_PROGRESS",
        created_at=clock.now(),
        updated_at=clock.now(),
    )
    db.add_all([app1, app2])
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app)

    yield client, db

    app.dependency_overrides.clear()
    db.close()


def test_auth_login_and_token(test_env):
    client, _ = test_env
    resp = client.post("/api/auth/login", json={"email": "ro.south@aicte.gov.in", "password": "secret123"})
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "regional_officer"


def test_cross_region_isolation(test_env):
    client, _ = test_env
    # Login as South RO
    login_resp = client.post("/api/auth/login", json={"email": "ro.south@aicte.gov.in", "password": "secret123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query applications list -> South RO should only see South application (APP-SOUTH-001)
    list_resp = client.get("/api/applications", headers=headers)
    assert list_resp.status_code == 200
    apps = list_resp.json()
    assert len(apps) == 1
    assert apps[0]["application_number"] == "APP-SOUTH-001"

    # Attempt direct get of North application (APP-NORTH-002, id=2) -> must return 404
    get_resp = client.get("/api/applications/2", headers=headers)
    assert get_resp.status_code == 404
    assert "not found or access denied" in get_resp.json()["detail"].lower()


def test_api_revert_requires_reason(test_env):
    client, _ = test_env
    login_resp = client.post("/api/auth/login", json={"email": "ro.south@aicte.gov.in", "password": "secret123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Revert without reason (empty string or missing)
    resp = client.post(
        "/api/applications/1/revert",
        json={"target_stage": "DEFICIENCY_COMMUNICATED", "reason": ""},
        headers=headers,
    )
    assert resp.status_code == 422


def test_api_advance_workflow_and_routes(test_env):
    client, _ = test_env
    login_resp = client.post("/api/auth/login", json={"email": "ro.south@aicte.gov.in", "password": "secret123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # List route templates
    routes_resp = client.get("/api/routes", headers=headers)
    assert routes_resp.status_code == 200
    assert len(routes_resp.json()) >= 1

    # South RO advances application 1 from SCRUTINY_PENDING -> APPROVED
    adv_resp = client.post(
        "/api/applications/1/advance",
        json={"target_stage": "APPROVED", "reason": "Scrutiny committee cleared all documents"},
        headers=headers,
    )
    assert adv_resp.status_code == 200
    assert adv_resp.json()["current_stage"] == "APPROVED"

    # List obligations
    ob_resp = client.get("/api/obligations", headers=headers)
    assert ob_resp.status_code == 200


def test_api_admin_clock_advance_and_audit_verify(test_env):
    client, _ = test_env
    login_resp = client.post("/api/auth/login", json={"email": "admin@aicte.gov.in", "password": "admin123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Advance clock by 3600 seconds
    clock_resp = client.post("/api/admin/clock/advance", json={"seconds": 3600}, headers=headers)
    assert clock_resp.status_code == 200
    assert clock_resp.json()["offset_seconds"] == 3600

    # Clock status
    status_resp = client.get("/api/admin/clock/status", headers=headers)
    assert status_resp.status_code == 200
    assert status_resp.json()["offset_seconds"] == 3600

    # Verify audit chain
    audit_resp = client.get("/api/audit/verify", headers=headers)
    assert audit_resp.status_code == 200
    assert audit_resp.json()["is_valid"] is True


def test_ro_can_access_audit_logs(test_env):
    client, _ = test_env
    login_resp = client.post("/api/auth/login", json={"email": "ro.south@aicte.gov.in", "password": "secret123"})
    token = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    logs_resp = client.get("/api/audit/logs", headers=headers)
    assert logs_resp.status_code == 200
    assert isinstance(logs_resp.json(), list)
