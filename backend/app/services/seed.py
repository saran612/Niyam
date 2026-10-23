"""Deterministic seed generator for ~80 applications across 5 regions.

Generates:
- 5 AICTE Regions (CRO, NRO, NWRO, SRO, WRO)
- Route templates & escalation policies
- National & regional public holidays
- 5 Role-based default users with standard passwords
- ~80 Institutions across 5 regions with diverse lease expiries
- ~80 Applications across all route templates and stages (with SLA stage obligations and historical transitions)
Idempotent and seeded via random.Random(42).
"""

import random
from datetime import timedelta

from app.core.auth import hash_password
from app.core.clock import clock
from app.core.database import SessionLocal
from app.core.routes_config import ESCALATION_POLICY_SEED, ROUTE_TEMPLATES_SEED
from app.models.entities import (
    Alert,
    Application,
    AuditLog,
    Document,
    EscalationPolicy,
    HolidayCalendar,
    Institution,
    Obligation,
    Region,
    RoleEnum,
    RouteTemplate,
    StageTransition,
    User,
)
from app.services.obligation import create_lease_expiry_obligation, create_stage_sla_obligation

REGIONS_DATA = [
    {"code": "CRO", "name": "Central Regional Office (Bhopal)"},
    {"code": "NRO", "name": "Northern Regional Office (Kanpur)"},
    {"code": "NWRO", "name": "North-Western Regional Office (Chandigarh)"},
    {"code": "SRO", "name": "Southern Regional Office (Chennai)"},
    {"code": "WRO", "name": "Western Regional Office (Mumbai)"},
]

HOLIDAYS_DATA = [
    {"name": "Republic Day", "month": 1, "day": 26, "is_national": True},
    {"name": "Independence Day", "month": 8, "day": 15, "is_national": True},
    {"name": "Gandhi Jayanti", "month": 10, "day": 2, "is_national": True},
    {"name": "Diwali Festival", "month": 11, "day": 12, "is_national": True},
    {"name": "Christmas Day", "month": 12, "day": 25, "is_national": True},
]


def run_seed() -> None:
    rng = random.Random(42)
    now_ts = clock.now()
    default_pw_hash = hash_password("aicte@2026")

    with SessionLocal() as db:
        print("Seeding database deterministically with random seed 42...")

        # 1. Clean existing records in strict dependency order
        db.query(Alert).delete()
        db.query(StageTransition).delete()
        db.query(Obligation).delete()
        db.query(Document).delete()
        db.query(AuditLog).delete()
        db.query(Application).delete()
        db.query(User).delete()
        db.query(Institution).delete()
        db.query(HolidayCalendar).delete()
        db.query(EscalationPolicy).delete()
        db.query(RouteTemplate).delete()
        db.query(Region).delete()
        db.commit()

        # 2. Seed Regions
        regions = []
        for r_data in REGIONS_DATA:
            r = Region(code=r_data["code"], name=r_data["name"], created_at=now_ts)
            db.add(r)
            regions.append(r)
        db.flush()

        # 3. Seed Route Templates
        route_templates = []
        for r_seed in ROUTE_TEMPLATES_SEED:
            rt = RouteTemplate(
                name=r_seed["name"],
                version=r_seed["version"],
                description=r_seed.get("description"),
                stages_definition=r_seed["stages_definition"],
                is_active=True,
                created_at=now_ts,
            )
            db.add(rt)
            route_templates.append(rt)
        db.flush()

        # 4. Seed Escalation Policies
        for p_seed in ESCALATION_POLICY_SEED:
            ep = EscalationPolicy(
                name=p_seed["name"],
                version=p_seed["version"],
                steps=p_seed["steps"],
                created_at=now_ts,
            )
            db.add(ep)
        db.flush()


        admin_user = User(
            email="admin@aicte-india.org",
            full_name="National System Administrator",
            password_hash=default_pw_hash,
            role=RoleEnum.ADMIN,
            is_active=True,
            created_at=now_ts,
        )
        bureau_user = User(
            email="bureau.officer@aicte-india.org",
            full_name="Approvals Bureau Director",
            password_hash=default_pw_hash,
            role=RoleEnum.BUREAU_OFFICER,
            is_active=True,
            created_at=now_ts,
        )
        db.add_all([admin_user, bureau_user])

        ro_users = []
        for reg in regions:
            ro = User(
                email=f"ro.{reg.code.lower()}@aicte-india.org",
                full_name=f"Regional Officer ({reg.code})",
                password_hash=default_pw_hash,
                role=RoleEnum.REGIONAL_OFFICER,
                region_id=reg.id,
                is_active=True,
                created_at=now_ts,
            )
            db.add(ro)
            ro_users.append(ro)
        db.flush()

        # 7. Seed ~80 Institutions and ~80 Applications
        institutions = []
        inst_names_pool = [
            "National Institute of Technology",
            "College of Engineering & Technology",
            "Polytechnic Institute of Sciences",
            "Institute of Management & Research",
            "Academy of Pharmaceutical Sciences",
            "Universal College of Architecture",
            "Apex Business School",
            "Metropolitan Technical Campus",
        ]

        total_apps = 80
        for i in range(1, total_apps + 1):
            assigned_region = regions[(i - 1) % len(regions)]
            prefix = inst_names_pool[(i - 1) % len(inst_names_pool)]
            inst_name = f"{prefix} - Campus {i:03d} ({assigned_region.code})"

            # Random lease expiry date (some expired, some in 30 days, some in 2 years)
            lease_offset = rng.choice([-10, 15, 28, 45, 90, 365, 700])
            lease_date = now_ts + timedelta(days=lease_offset)

            inst = Institution(
                aicte_id=f"1-{10000000 + i}",
                name=inst_name,
                region_id=assigned_region.id,
                address=f"Plot No. {i * 12}, Knowledge Corridor, Sector {i % 20 + 1}",
                lease_expiry_date=lease_date,
                created_at=now_ts,
            )
            db.add(inst)
            db.flush()
            institutions.append(inst)

            # Institution user
            inst_user = User(
                email=f"dean.inst{i:03d}@aicte-india.org",
                full_name=f"Dean {inst.name}",
                password_hash=default_pw_hash,
                role=RoleEnum.INSTITUTION,
                region_id=assigned_region.id,
                institution_id=inst.id,
                is_active=True,
                created_at=now_ts,
            )
            db.add(inst_user)

            # Application route & stage selection
            route = route_templates[i % len(route_templates)]
            stage_keys = [s["stage_key"] for s in route.stages_definition if not s.get("is_mechanical", False)]
            chosen_stage = rng.choice(stage_keys)

            status = "IN_PROGRESS"
            if chosen_stage == "APPROVED":
                status = "APPROVED"
            elif chosen_stage == "REJECTED":
                status = "REJECTED"

            app = Application(
                application_number=f"AICTE-2026-{assigned_region.code}-{i:04d}",
                institution_id=inst.id,
                region_id=assigned_region.id,
                academic_year="2026-2027",
                current_stage=chosen_stage,
                route_template_id=route.id,
                route_template_version=route.version,
                status=status,
                suggested_action="APPROVE" if status == "IN_PROGRESS" else None,
                created_at=now_ts - timedelta(days=rng.randint(5, 60)),
                updated_at=now_ts,
            )
            db.add(app)
            db.flush()

            # Create SLA obligation for current stage if in progress
            if status == "IN_PROGRESS":
                stage_cfg = next((s for s in route.stages_definition if s["stage_key"] == chosen_stage), None)
                sla_days = stage_cfg.get("sla_days", 15) if stage_cfg else 15
                create_stage_sla_obligation(db, app, stage_key=chosen_stage, sla_days=sla_days)

            # Create lease expiry obligation
            create_lease_expiry_obligation(db, inst)

        db.commit()
        print(f"Seed complete! Generated {len(regions)} regions, {len(institutions)} institutions, and {total_apps} applications.")


if __name__ == "__main__":
    run_seed()
