"""Tests for Virtual Clock and Determinism."""

import pytest
from app.core.clock import VirtualClock
from app.core.database import Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_virtual_clock_advance(in_memory_db):
    clock = VirtualClock()
    clock.initialize(in_memory_db)

    t0 = clock.now()
    offset = clock.advance(86400, db=in_memory_db)  # Advance 1 day
    assert offset == 86400

    t1 = clock.now()
    diff = (t1 - t0).total_seconds()
    assert 86395 <= diff <= 86405

    # Reload from DB into fresh clock instance
    fresh_clock = VirtualClock()
    fresh_clock.initialize(in_memory_db)
    assert fresh_clock.get_offset() == 86400

    # Reset
    fresh_clock.reset(in_memory_db)
    assert fresh_clock.get_offset() == 0
