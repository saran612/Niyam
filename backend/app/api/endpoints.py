"""FastAPI Routers for AICTE Obligation Engine."""

from typing import Annotated

from app.api.deps import (
    get_current_user,
    require_roles,
    scope_applications_query,
    scope_obligations_query,
)
from app.api.schemas import (
    AdvanceStageRequest,
    ApplicationDetailOut,
    ApplicationOut,
    AuditVerifyResponse,
    ClockAdvanceRequest,
    ClockStatusResponse,
    LoginRequest,
    ObligationOut,
    RevertStageRequest,
    RouteTemplateOut,
    TokenResponse,
)
from app.core.auth import create_access_token, verify_password
from app.core.clock import clock
from app.core.database import get_db
from app.models.entities import (
    Application,
    AuditLog,
    Document,
    Obligation,
    ObligationStatusEnum,
    RoleEnum,
    RouteTemplate,
    User,
)
from app.services.audit import record, verify_chain
from app.services.storage import generate_presigned_download_url, upload_document_bytes
from app.services.workflow import WorkflowError, transition_stage
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

auth_router = APIRouter(prefix="/auth", tags=["auth"])
admin_router = APIRouter(prefix="/admin", tags=["admin"])
apps_router = APIRouter(prefix="/applications", tags=["applications"])
obligations_router = APIRouter(prefix="/obligations", tags=["obligations"])
audit_router = APIRouter(prefix="/audit", tags=["audit"])
docs_router = APIRouter(prefix="/documents", tags=["documents"])
routes_router = APIRouter(prefix="/routes", tags=["routes"])


@routes_router.get("", response_model=list[RouteTemplateOut])
def list_routes(db: Annotated[Session, Depends(get_db)]):
    return db.query(RouteTemplate).filter_by(is_active=True).all()



# --- AUTH ENDPOINTS ---
@auth_router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Annotated[Session, Depends(get_db)]):
    user = db.query(User).filter_by(email=req.email).first()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=403, detail="User account is deactivated")

    token = create_access_token(user)
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        region_id=user.region_id,
        institution_id=user.institution_id,
    )


@auth_router.get("/me")
def get_me(user: Annotated[User, Depends(get_current_user)]):
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "region_id": user.region_id,
        "institution_id": user.institution_id,
    }


# --- CLOCK CONTROL ENDPOINTS ---
@admin_router.post("/clock/advance", response_model=ClockStatusResponse)
def advance_clock(
    req: ClockAdvanceRequest,
    user: Annotated[User, Depends(require_roles([RoleEnum.ADMIN]))],
    db: Annotated[Session, Depends(get_db)],
):
    new_offset = clock.advance(req.seconds, db=db)
    record(
        db=db,
        action="CLOCK_ADVANCED",
        entity_type="clock",
        entity_id="1",
        payload={"advanced_seconds": req.seconds, "total_offset": new_offset},
        actor=user,
    )
    db.commit()
    return ClockStatusResponse(current_time=clock.now().isoformat(), offset_seconds=new_offset)


@admin_router.post("/clock/reset", response_model=ClockStatusResponse)
def reset_clock(
    user: Annotated[User, Depends(require_roles([RoleEnum.ADMIN]))],
    db: Annotated[Session, Depends(get_db)],
):
    offset = clock.reset(db=db)
    record(
        db=db,
        action="CLOCK_RESET",
        entity_type="clock",
        entity_id="1",
        payload={"offset": 0},
        actor=user,
    )
    db.commit()
    return ClockStatusResponse(current_time=clock.now().isoformat(), offset_seconds=offset)


@admin_router.get("/clock/status", response_model=ClockStatusResponse)
def get_clock_status():
    return ClockStatusResponse(
        current_time=clock.now().isoformat(),
        offset_seconds=clock.get_offset(),
    )


# --- APPLICATIONS & WORKFLOW ENDPOINTS ---
@apps_router.get("", response_model=list[ApplicationOut])
def list_applications(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    stage: str | None = None,
):
    query = db.query(Application)
    query = scope_applications_query(query, user)
    if stage:
        query = query.filter(Application.current_stage == stage)
    return query.order_by(Application.id.desc()).all()


@apps_router.get("/{app_id}", response_model=ApplicationDetailOut)
def get_application_detail(
    app_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    query = db.query(Application).filter(Application.id == app_id)
    query = scope_applications_query(query, user)
    app = query.first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found or access denied")
    return app


@apps_router.post("/{app_id}/advance", response_model=ApplicationOut)
def advance_application(
    app_id: int,
    req: AdvanceStageRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    query = db.query(Application).filter(Application.id == app_id)
    query = scope_applications_query(query, user)
    app = query.first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found or unauthorized")

    try:
        updated_app, _ = transition_stage(
            db=db,
            application=app,
            target_stage=req.target_stage,
            action="ADVANCE",
            actor=user,
            reason=req.reason,
        )
        db.commit()
        return updated_app
    except WorkflowError as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


@apps_router.post("/{app_id}/revert", response_model=ApplicationOut)
def revert_application(
    app_id: int,
    req: RevertStageRequest,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    query = db.query(Application).filter(Application.id == app_id)
    query = scope_applications_query(query, user)
    app = query.first()
    if not app:
        raise HTTPException(status_code=404, detail="Application not found or unauthorized")

    try:
        updated_app, _ = transition_stage(
            db=db,
            application=app,
            target_stage=req.target_stage,
            action="REVERT",
            actor=user,
            reason=req.reason,
        )
        db.commit()
        return updated_app
    except WorkflowError as e:
        db.rollback()
        raise HTTPException(status_code=e.status_code, detail=e.message) from e


# --- OBLIGATIONS ENDPOINTS ---
@obligations_router.get("", response_model=list[ObligationOut])
def list_obligations(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    status_filter: ObligationStatusEnum | None = None,
):
    query = db.query(Obligation)
    query = scope_obligations_query(query, user)
    if status_filter:
        query = query.filter(Obligation.status == status_filter)
    return query.order_by(Obligation.due_at.asc()).all()


@obligations_router.post("/{ob_id}/satisfy", response_model=ObligationOut)
def satisfy_obligation(
    ob_id: int,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    query = db.query(Obligation).filter(Obligation.id == ob_id)
    query = scope_obligations_query(query, user)
    ob = query.first()
    if not ob:
        raise HTTPException(status_code=404, detail="Obligation not found or unauthorized")

    ob.status = ObligationStatusEnum.SATISFIED
    ob.satisfied_at = clock.now()
    ob.updated_at = clock.now()

    record(
        db=db,
        action="OBLIGATION_SATISFIED",
        entity_type="obligation",
        entity_id=str(ob.id),
        payload={"satisfied_at": ob.satisfied_at.isoformat()},
        actor=user,
    )
    db.commit()
    return ob


# --- AUDIT ENDPOINTS ---
@audit_router.get("/verify", response_model=AuditVerifyResponse)
def verify_audit_trail(db: Annotated[Session, Depends(get_db)]):
    is_valid, bad_id, err = verify_chain(db)
    total = db.query(AuditLog).count()
    return AuditVerifyResponse(
        is_valid=is_valid,
        total_logs=total,
        corrupted_log_id=bad_id,
        error_message=err,
    )


@audit_router.get("/logs")
def get_audit_logs(
    user: Annotated[User, Depends(require_roles([RoleEnum.ADMIN, RoleEnum.BUREAU_OFFICER]))],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 50,
):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(limit).all()
    return [
        {
            "id": log_item.id,
            "prev_hash": log_item.prev_hash,
            "hash": log_item.hash,
            "entity_type": log_item.entity_type,
            "entity_id": log_item.entity_id,
            "action": log_item.action,
            "actor_id": log_item.actor_id,
            "payload": log_item.payload,
            "timestamp": log_item.timestamp.isoformat(),
        }
        for log_item in logs
    ]


# --- DOCUMENTS ENDPOINTS ---
@docs_router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),  # noqa: B008
    institution_id: int = Form(...),  # noqa: B008
    title: str = Form(...),  # noqa: B008
    document_type: str = Form(...),  # noqa: B008
    application_id: int | None = Form(None),  # noqa: B008
    user: Annotated[User, Depends(get_current_user)] = None,  # type: ignore[assignment]
    db: Annotated[Session | None, Depends(get_db)] = None,
):
    content = await file.read()
    try:
        s3_key, mime, size, sha256 = upload_document_bytes(
            content=content,
            original_filename=file.filename or "uploaded_file",
            institution_id=institution_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    doc = Document(
        application_id=application_id,
        institution_id=institution_id,
        title=title,
        document_type=document_type,
        s3_key=s3_key,
        mime_type=mime,
        file_size_bytes=size,
        sha256_hash=sha256,
        uploaded_by_id=user.id,
        created_at=clock.now(),
    )
    if db:
        db.add(doc)
        db.flush()

        record(
            db=db,
            action="DOCUMENT_UPLOADED",
            entity_type="document",
            entity_id=str(doc.id),
            payload={"title": title, "s3_key": s3_key, "sha256": sha256},
            actor=user,
        )
        db.commit()

    download_url = generate_presigned_download_url(s3_key)
    return {
        "id": doc.id,
        "title": doc.title,
        "document_type": doc.document_type,
        "s3_key": doc.s3_key,
        "download_url": download_url,
    }
