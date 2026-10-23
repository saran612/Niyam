"""Tests for Audit Log hash chaining and verification."""

import pytest
from app.core.database import Base
from app.models.entities import AuditLog
from app.services.audit import record, verify_chain
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_audit_hash_chain_validity(db):
    # Record 3 events
    record(db, "CREATE", "application", "1", {"status": "NEW"})
    record(db, "UPDATE", "application", "1", {"status": "IN_PROGRESS"})
    record(db, "APPROVE", "application", "1", {"status": "APPROVED"})
    db.commit()

    is_valid, bad_id, err = verify_chain(db)
    assert is_valid is True
    assert bad_id is None
    assert err is None


def test_audit_detects_tampering(db):
    record(db, "CREATE", "application", "1", {"amount": 100})
    record(db, "APPROVE", "application", "1", {"amount": 100})
    db.commit()

    assert verify_chain(db)[0] is True

    # Manually tamper with first row payload
    first_log = db.query(AuditLog).filter_by(id=1).first()
    first_log.payload = {"amount": 999999}
    db.commit()

    is_valid, bad_id, err = verify_chain(db)
    assert is_valid is False
    assert bad_id == 1
    assert "Hash mismatch" in err
