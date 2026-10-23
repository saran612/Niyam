"""SQLAlchemy domain models for AICTE Obligation Engine."""

import enum
from datetime import datetime
from typing import Any

from app.core.database import Base
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


class RoleEnum(enum.StrEnum):
    REGIONAL_OFFICER = "regional_officer"
    BUREAU_OFFICER = "bureau_officer"
    COMMITTEE = "committee"
    INSTITUTION = "institution"
    ADMIN = "admin"


class ObligationStatusEnum(enum.StrEnum):
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    SATISFIED = "SATISFIED"
    BREACHED = "BREACHED"
    WAIVED = "WAIVED"


class ObligationTypeEnum(enum.StrEnum):
    STAGE_SLA = "STAGE_SLA"
    EVC_REPORT = "EVC_REPORT"
    UNDERTAKING = "UNDERTAKING"
    LEASE_EXPIRY = "LEASE_EXPIRY"
    DEFICIENCY_RECTIFICATION = "DEFICIENCY_RECTIFICATION"


class Region(Base):
    __tablename__ = "regions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    users: Mapped[list["User"]] = relationship("User", back_populates="region")
    institutions: Mapped[list["Institution"]] = relationship("Institution", back_populates="region")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="region")


class Institution(Base):
    __tablename__ = "institutions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    aicte_id: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("regions.id"), nullable=False)
    address: Mapped[str] = mapped_column(Text, nullable=False)
    lease_expiry_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    region: Mapped[Region] = relationship("Region", back_populates="institutions")
    applications: Mapped[list["Application"]] = relationship("Application", back_populates="institution")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="institution")


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum), nullable=False)
    region_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("regions.id"), nullable=True)
    institution_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("institutions.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    region: Mapped[Region | None] = relationship("Region", back_populates="users")
    institution: Mapped[Institution | None] = relationship("Institution")
    assigned_obligations: Mapped[list["Obligation"]] = relationship("Obligation", back_populates="owner")


class RouteTemplate(Base):
    __tablename__ = "route_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # List of stages with: {stage_key, label, is_mechanical, allowed_roles, sla_days, auto_advance_target}
    stages_definition: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("name", "version", name="uq_route_template_name_version"),)


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_number: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    institution_id: Mapped[int] = mapped_column(Integer, ForeignKey("institutions.id"), nullable=False)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("regions.id"), nullable=False)
    academic_year: Mapped[str] = mapped_column(String(20), nullable=False)
    current_stage: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    route_template_id: Mapped[int] = mapped_column(Integer, ForeignKey("route_templates.id"), nullable=False)
    route_template_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="IN_PROGRESS")
    suggested_action: Mapped[str | None] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    institution: Mapped[Institution] = relationship("Institution", back_populates="applications")
    region: Mapped[Region] = relationship("Region", back_populates="applications")
    route_template: Mapped[RouteTemplate] = relationship("RouteTemplate")
    transitions: Mapped[list["StageTransition"]] = relationship("StageTransition", back_populates="application")
    obligations: Mapped[list["Obligation"]] = relationship("Obligation", back_populates="application")
    documents: Mapped[list["Document"]] = relationship("Document", back_populates="application")


class StageTransition(Base):
    __tablename__ = "stage_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int] = mapped_column(Integer, ForeignKey("applications.id"), nullable=False, index=True)
    from_stage: Mapped[str] = mapped_column(String(100), nullable=False)
    to_stage: Mapped[str] = mapped_column(String(100), nullable=False)
    transition_type: Mapped[str] = mapped_column(String(50), nullable=False) # ADVANCE, REVERT, REJECT, APPROVE
    performed_by_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True) # Enforced non-empty for REVERT
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    application: Mapped[Application] = relationship("Application", back_populates="transitions")
    performed_by: Mapped[User | None] = relationship("User")


class EscalationPolicy(Base):
    __tablename__ = "escalation_policies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # ladder steps: [{"step": "T-30", "offset_days": -30, "target_role": "institution", "action": "email"}, ...]
    steps: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (UniqueConstraint("name", "version", name="uq_escalation_policy_name_version"),)


class Obligation(Base):
    __tablename__ = "obligations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("applications.id"), nullable=True, index=True)
    institution_id: Mapped[int] = mapped_column(Integer, ForeignKey("institutions.id"), nullable=False, index=True)
    region_id: Mapped[int] = mapped_column(Integer, ForeignKey("regions.id"), nullable=False, index=True)
    obligation_type: Mapped[ObligationTypeEnum] = mapped_column(SQLEnum(ObligationTypeEnum), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    stage_key: Mapped[str | None] = mapped_column(String(100), nullable=True)

    owner_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    owner_role: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum), nullable=False)

    status: Mapped[ObligationStatusEnum] = mapped_column(
        SQLEnum(ObligationStatusEnum),
        default=ObligationStatusEnum.PENDING,
        nullable=False,
        index=True
    )

    escalation_policy_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("escalation_policies.id"), nullable=True)

    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    satisfied_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    application: Mapped[Application | None] = relationship("Application", back_populates="obligations")
    institution: Mapped[Institution] = relationship("Institution")
    region: Mapped[Region] = relationship("Region")
    owner: Mapped[User | None] = relationship("User", back_populates="assigned_obligations")
    escalation_policy: Mapped[EscalationPolicy | None] = relationship("EscalationPolicy")
    alerts: Mapped[list["Alert"]] = relationship("Alert", back_populates="obligation")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    obligation_id: Mapped[int] = mapped_column(Integer, ForeignKey("obligations.id"), nullable=False)
    step: Mapped[str] = mapped_column(String(50), nullable=False) # e.g. T-30, T-7, T-0, OVERDUE_3D
    target_role: Mapped[RoleEnum] = mapped_column(SQLEnum(RoleEnum), nullable=False)
    target_user_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    channel: Mapped[str] = mapped_column(String(50), nullable=False, default="EMAIL_AND_INAPP")
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="SENT")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    fired_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    obligation: Mapped[Obligation] = relationship("Obligation", back_populates="alerts")
    target_user: Mapped[User | None] = relationship("User")

    __table_args__ = (
        UniqueConstraint("obligation_id", "step", name="uq_alert_obligation_step"),
        Index("ix_alerts_obligation_step", "obligation_id", "step"),
    )


class HolidayCalendar(Base):
    __tablename__ = "holiday_calendar"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("regions.id"), nullable=True) # Null = National
    is_national: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    __table_args__ = (
        UniqueConstraint("date", "region_id", name="uq_holiday_date_region"),
    )


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    application_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("applications.id"), nullable=True)
    institution_id: Mapped[int] = mapped_column(Integer, ForeignKey("institutions.id"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    document_type: Mapped[str] = mapped_column(String(100), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(500), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    file_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    uploaded_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    application: Mapped[Application | None] = relationship("Application", back_populates="documents")
    institution: Mapped[Institution] = relationship("Institution", back_populates="documents")
    uploaded_by: Mapped[User] = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    prev_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_type: Mapped[str] = mapped_column(String(100), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(100), nullable=False)
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    actor_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("users.id"), nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    actor: Mapped[User | None] = relationship("User")

    __table_args__ = (
        Index("ix_audit_logs_timestamp", "timestamp"),
    )
