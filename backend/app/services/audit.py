"""Audit logging service.

Provides a unified `record(db, action, entity_type, entity_id, payload, actor)`
invoked inside the same database transaction as every mutation.
Computes a cryptographic hash chain:
    hash = SHA-256(prev_hash + entity_type + entity_id + action + timestamp + payload_json)
Provides `verify_chain(db)` to detect any tampering or omission.
"""

import hashlib
import json
from datetime import UTC, datetime
from typing import Any

from app.core.clock import clock
from app.models.entities import AuditLog, User
from sqlalchemy.orm import Session

GENESIS_HASH = "0" * 64


def serialize_payload(payload: dict[str, Any]) -> str:
    """Canonical JSON serialization for hashing."""
    return json.dumps(payload, sort_keys=True, default=str)


def compute_audit_hash(
    prev_hash: str,
    entity_type: str,
    entity_id: str,
    action: str,
    timestamp: datetime,
    payload_serialized: str,
) -> str:
    hasher = hashlib.sha256()
    hasher.update(prev_hash.encode("utf-8"))
    hasher.update(entity_type.encode("utf-8"))
    hasher.update(str(entity_id).encode("utf-8"))
    hasher.update(action.encode("utf-8"))
    if timestamp.tzinfo is None:
        ts_utc = timestamp.replace(tzinfo=UTC)
    else:
        ts_utc = timestamp.astimezone(UTC)
    hasher.update(ts_utc.isoformat().encode("utf-8"))
    hasher.update(payload_serialized.encode("utf-8"))
    return hasher.hexdigest()


def record(
    db: Session,
    action: str,
    entity_type: str,
    entity_id: str,
    payload: dict[str, Any],
    actor: User | None = None,
) -> AuditLog:
    """Record audit log in current transaction with cryptographic chaining."""
    last_log = db.query(AuditLog).order_by(AuditLog.id.desc()).first()
    prev_hash = last_log.hash if last_log is not None else GENESIS_HASH

    now_ts = clock.now()
    payload_json = serialize_payload(payload)
    curr_hash = compute_audit_hash(
        prev_hash=prev_hash,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        timestamp=now_ts,
        payload_serialized=payload_json,
    )

    audit_entry = AuditLog(
        prev_hash=prev_hash,
        hash=curr_hash,
        entity_type=entity_type,
        entity_id=str(entity_id),
        action=action,
        actor_id=actor.id if actor else None,
        actor_role=actor.role.value if actor else None,
        payload=payload,
        timestamp=now_ts,
    )
    db.add(audit_entry)
    db.flush()  # assign ID in current transaction without committing
    return audit_entry


def verify_chain(db: Session) -> tuple[bool, int | None, str | None]:
    """Verifies the entire audit trail integrity.

    Returns (is_valid, corrupted_log_id, error_message).
    """
    logs = db.query(AuditLog).order_by(AuditLog.id.asc()).all()
    if not logs:
        return True, None, None

    expected_prev = GENESIS_HASH
    for log in logs:
        if log.prev_hash != expected_prev:
            return (
                False,
                log.id,
                f"Broken chain at log {log.id}: expected prev_hash {expected_prev}, found {log.prev_hash}",
            )

        payload_json = serialize_payload(log.payload)
        recomputed_hash = compute_audit_hash(
            prev_hash=log.prev_hash,
            entity_type=log.entity_type,
            entity_id=log.entity_id,
            action=log.action,
            timestamp=log.timestamp,
            payload_serialized=payload_json,
        )

        if log.hash != recomputed_hash:
            return (
                False,
                log.id,
                f"Hash mismatch at log {log.id}: stored {log.hash}, calculated {recomputed_hash}",
            )

        expected_prev = log.hash

    return True, None, None
