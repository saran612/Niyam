"""Pydantic schemas for API request and response bodies."""

from datetime import datetime
from typing import Any

from app.models.entities import ObligationStatusEnum, ObligationTypeEnum, RoleEnum
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    email: str
    full_name: str
    role: RoleEnum
    region_id: int | None = None
    institution_id: int | None = None


class ClockAdvanceRequest(BaseModel):
    seconds: int = Field(..., description="Seconds to advance virtual clock by (e.g. 86400 for 1 day)")


class ClockStatusResponse(BaseModel):
    current_time: str
    offset_seconds: int


class RevertStageRequest(BaseModel):
    target_stage: str
    reason: str = Field(..., min_length=1, description="Non-empty reason required for reverting")


class AdvanceStageRequest(BaseModel):
    target_stage: str
    reason: str | None = None


class ObligationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: int | None = None
    institution_id: int
    region_id: int
    obligation_type: ObligationTypeEnum
    title: str
    description: str | None = None
    stage_key: str | None = None
    owner_id: int | None = None
    owner_role: RoleEnum
    status: ObligationStatusEnum
    due_at: datetime
    satisfied_at: datetime | None = None
    created_at: datetime


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_number: str
    institution_id: int
    region_id: int
    academic_year: str
    current_stage: str
    status: str
    suggested_action: str | None = None
    created_at: datetime
    updated_at: datetime


class ApplicationDetailOut(ApplicationOut):
    obligations: list[ObligationOut] = []


class RouteTemplateOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    version: int
    description: str | None = None
    stages_definition: list[dict[str, Any]]
    is_active: bool
    created_at: datetime


class AuditVerifyResponse(BaseModel):
    is_valid: bool
    total_logs: int
    corrupted_log_id: int | None = None
    error_message: str | None = None

