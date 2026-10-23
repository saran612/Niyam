"""FastAPI Dependencies for Auth, Roles, and Region-Scoping."""

from typing import Annotated

from app.core.auth import decode_access_token
from app.core.database import get_db
from app.models.entities import Application, Obligation, RoleEnum, User
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Query, Session

security = HTTPBearer()


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = int(payload["sub"])
    user = db.query(User).filter_by(id=user_id, is_active=True).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or disabled",
        )
    return user


def require_roles(allowed_roles: list[RoleEnum]):
    def role_checker(current_user: Annotated[User, Depends(get_current_user)]) -> User:
        if current_user.role != RoleEnum.ADMIN and current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation not permitted for role {current_user.role.value}",
            )
        return current_user
    return role_checker


def scope_applications_query(query: Query, user: User) -> Query:
    """Enforces server-side regional and institutional data isolation in repository layer."""
    if user.role == RoleEnum.ADMIN or user.role == RoleEnum.BUREAU_OFFICER:
        return query
    if user.role == RoleEnum.REGIONAL_OFFICER:
        if user.region_id is None:
            return query.filter(Application.id == -1)  # No region assigned -> empty
        return query.filter(Application.region_id == user.region_id)
    if user.role == RoleEnum.INSTITUTION:
        if user.institution_id is None:
            return query.filter(Application.id == -1)
        return query.filter(Application.institution_id == user.institution_id)
    if user.role == RoleEnum.COMMITTEE:
        if user.region_id is not None:
            return query.filter(Application.region_id == user.region_id)
        return query
    return query.filter(Application.id == -1)


def scope_obligations_query(query: Query, user: User) -> Query:
    """Enforces server-side regional isolation on single obligation table."""
    if user.role == RoleEnum.ADMIN or user.role == RoleEnum.BUREAU_OFFICER:
        return query
    if user.role == RoleEnum.REGIONAL_OFFICER:
        if user.region_id is None:
            return query.filter(Obligation.id == -1)
        return query.filter(Obligation.region_id == user.region_id)
    if user.role == RoleEnum.INSTITUTION:
        if user.institution_id is None:
            return query.filter(Obligation.id == -1)
        return query.filter(Obligation.institution_id == user.institution_id)
    return query
