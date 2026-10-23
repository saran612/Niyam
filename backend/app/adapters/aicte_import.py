"""MOCK Adapter for AICTE Legacy CSV/JSON Data Import.

Interface: `AICTEImporter`
Features:
- Validates rows (required fields, valid AICTE ID format, region existence)
- Deduplication against existing applications and institutions
- Per-row error reporting with row number and failure reason
- Atomic or batch error handling
- Labelled strictly as MOCK adapter
"""

import csv
import io
import json
from typing import Any

from app.core.clock import clock
from app.models.entities import (
    Application,
    Institution,
    Region,
    RouteTemplate,
)
from app.services.audit import record
from app.services.obligation import create_stage_sla_obligation
from pydantic import BaseModel, ValidationError, field_validator
from sqlalchemy.orm import Session


class ImportRowSchema(BaseModel):
    application_number: str
    aicte_id: str
    institution_name: str
    region_code: str
    address: str
    academic_year: str = "2026-2027"
    route_name: str = "Only Scrutiny"

    @field_validator("aicte_id")
    @classmethod
    def validate_aicte_id(cls, v: str) -> str:
        if not v.startswith("1-") or len(v) < 5:
            raise ValueError("AICTE ID must start with '1-' followed by numeric identifier")
        return v

    @field_validator("application_number")
    @classmethod
    def validate_app_number(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Application number cannot be empty")
        return v.strip()


class RowError(BaseModel):
    row_index: int
    data: dict[str, Any]
    error: str


class ImportSummary(BaseModel):
    adapter: str = "MOCK_AICTE_LEGACY_IMPORT_ADAPTER"
    total_processed: int
    successful_count: int
    failed_count: int
    errors: list[RowError] = []


def import_aicte_data(
    db: Session,
    raw_content: str,
    file_format: str = "csv",  # "csv" or "json"
) -> ImportSummary:
    """Parses and ingests legacy AICTE records behind a validated mock adapter interface."""
    rows: list[dict[str, Any]] = []

    if file_format.lower() == "json":
        try:
            parsed = json.loads(raw_content)
            rows = parsed if isinstance(parsed, list) else [parsed]
        except Exception as e:
            return ImportSummary(
                total_processed=0,
                successful_count=0,
                failed_count=0,
                errors=[RowError(row_index=0, data={}, error=f"Invalid JSON payload: {e}")],
            )
    else:  # CSV format
        try:
            f = io.StringIO(raw_content.strip())
            reader = csv.DictReader(f)
            rows = list(reader)
        except Exception as e:
            return ImportSummary(
                total_processed=0,
                successful_count=0,
                failed_count=0,
                errors=[RowError(row_index=0, data={}, error=f"Invalid CSV structure: {e}")],
            )

    successful = 0
    errors: list[RowError] = []

    # Cache regions and routes
    regions_map = {r.code: r for r in db.query(Region).all()}
    routes_map = {rt.name: rt for rt in db.query(RouteTemplate).all()}

    for idx, row in enumerate(rows, start=1):
        # 1. Schema Validation
        try:
            validated = ImportRowSchema(**row)
        except ValidationError as ve:
            errors.append(
                RowError(row_index=idx, data=row, error=str(ve.errors()[0]["msg"]))
            )
            continue

        # 2. Region check
        region = regions_map.get(validated.region_code)
        if not region:
            errors.append(
                RowError(
                    row_index=idx,
                    data=row,
                    error=f"Region code '{validated.region_code}' not found in database",
                )
            )
            continue

        # 3. Route check
        route = routes_map.get(validated.route_name)
        if not route:
            errors.append(
                RowError(
                    row_index=idx,
                    data=row,
                    error=f"Route template '{validated.route_name}' not found",
                )
            )
            continue

        # 4. Deduplication
        existing_app = (
            db.query(Application)
            .filter_by(application_number=validated.application_number)
            .first()
        )
        if existing_app:
            errors.append(
                RowError(
                    row_index=idx,
                    data=row,
                    error=f"Duplicate application number '{validated.application_number}'",
                )
            )
            continue

        # 5. Create or find institution
        inst = db.query(Institution).filter_by(aicte_id=validated.aicte_id).first()
        if not inst:
            inst = Institution(
                aicte_id=validated.aicte_id,
                name=validated.institution_name,
                region_id=region.id,
                address=validated.address,
                created_at=clock.now(),
            )
            db.add(inst)
            db.flush()

        # 6. Ingest application
        app = Application(
            application_number=validated.application_number,
            institution_id=inst.id,
            region_id=region.id,
            academic_year=validated.academic_year,
            current_stage="APPLICATION_SUBMITTED",
            route_template_id=route.id,
            route_template_version=route.version,
            status="IN_PROGRESS",
            created_at=clock.now(),
            updated_at=clock.now(),
        )
        db.add(app)
        db.flush()

        # Generate stage obligation
        create_stage_sla_obligation(db, app, stage_key="APPLICATION_SUBMITTED", sla_days=1)

        record(
            db=db,
            action="MOCK_IMPORT_RECORD",
            entity_type="application",
            entity_id=str(app.id),
            payload={"application_number": app.application_number, "aicte_id": inst.aicte_id},
        )
        successful += 1

    db.commit()
    return ImportSummary(
        total_processed=len(rows),
        successful_count=successful,
        failed_count=len(errors),
        errors=errors,
    )
