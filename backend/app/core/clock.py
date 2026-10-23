"""Deterministic clock service.

Enforces zero direct calls to standard datetime retrieval in the codebase.
Virtual offset is stored in the database and loaded/cached into memory.
"""

from datetime import UTC, datetime, timedelta
from typing import Any

from app.core.database import Base
from sqlalchemy import Column, DateTime, Integer
from sqlalchemy.orm import Session


class ClockOffsetModel(Base):
    __tablename__ = "system_clock"

    id: Any = Column(Integer, primary_key=True, default=1)
    offset_seconds: Any = Column(Integer, default=0, nullable=False)
    updated_at: Any = Column(DateTime(timezone=True), nullable=True)


class VirtualClock:
    def __init__(self) -> None:
        self._cached_offset_seconds: int = 0
        self._is_initialized: bool = False

    def initialize(self, db: Session | None = None) -> None:
        if db is not None:
            clock_row = db.query(ClockOffsetModel).filter_by(id=1).first()
            if clock_row is not None:
                self._cached_offset_seconds = int(clock_row.offset_seconds)
            else:
                clock_row = ClockOffsetModel(id=1, offset_seconds=0)
                db.add(clock_row)
                db.commit()
                self._cached_offset_seconds = 0
        self._is_initialized = True

    def get_offset(self) -> int:
        return self._cached_offset_seconds

    def set_offset(self, seconds: int, db: Session | None = None) -> int:
        self._cached_offset_seconds = seconds
        if db is not None:
            clock_row = db.query(ClockOffsetModel).filter_by(id=1).first()
            now_utc = datetime.now(UTC)
            if clock_row is None:
                clock_row = ClockOffsetModel(id=1, offset_seconds=seconds, updated_at=now_utc)
                db.add(clock_row)
            else:
                clock_row.offset_seconds = seconds
                clock_row.updated_at = now_utc
            db.commit()
        return self._cached_offset_seconds

    def advance(self, seconds: int, db: Session | None = None) -> int:
        new_offset = self._cached_offset_seconds + seconds
        return self.set_offset(new_offset, db=db)

    def reset(self, db: Session | None = None) -> int:
        return self.set_offset(0, db=db)

    def now(self) -> datetime:
        """Returns deterministic UTC datetime accounting for simulated offset."""
        base_utc = datetime.now(UTC)
        return base_utc + timedelta(seconds=self._cached_offset_seconds)

    def today(self) -> datetime:
        return self.now().replace(hour=0, minute=0, second=0, microsecond=0)


clock = VirtualClock()
