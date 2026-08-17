from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"
    __table_args__ = (
        Index("ix_evaluation_runs_capability", "capability_id", "capability_version"),
        Index("ix_evaluation_runs_created_at", "created_at"),
    )

    id: Mapped[str] = mapped_column(String(256), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(32), nullable=False)
    capability_id: Mapped[str] = mapped_column(String(256), nullable=False)
    capability_version: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(256), nullable=False)
    dataset_version: Mapped[str] = mapped_column(String(64), nullable=False)
    dataset_hash: Mapped[str] = mapped_column(String(71), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    promotion: Mapped[str] = mapped_column(String(32), nullable=False)
    payload: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_by: Mapped[str | None] = mapped_column(String(256))
