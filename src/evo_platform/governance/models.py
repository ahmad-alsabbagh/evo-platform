"""SQLAlchemy models for governance persistence: audit trail + approvals.

Both tables are designed to be append-mostly:
  - audit_log: strictly INSERT-only in application code. Revoke UPDATE/DELETE
    grants on this table in production (e.g. via a read-only app role) to get
    a true write-once guarantee at the database layer.
  - approval_requests: INSERT then a single UPDATE on resolution (approve/deny).
"""

from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class AuditLogRow(Base):
    __tablename__ = "audit_log"

    sequence = Column(Integer, primary_key=True, autoincrement=True)
    entry_id = Column(String(64), unique=True, nullable=False, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    agent_id = Column(String(128), nullable=False, index=True)
    user_id = Column(String(128), nullable=False)
    session_id = Column(String(128), nullable=False, index=True)
    action = Column(String(128), nullable=False)
    authorization_tier = Column(String(32), nullable=False)
    outcome = Column(String(32), nullable=False)
    metadata_json = Column(JSON, nullable=False, default=dict)
    prev_hash = Column(String(64), nullable=False)
    entry_hash = Column(String(64), nullable=False)


class ApprovalRequestRow(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, autoincrement=True)
    approval_id = Column(String(64), unique=True, nullable=False, index=True)
    agent_id = Column(String(128), nullable=False, index=True)
    session_id = Column(String(128), nullable=False, index=True)
    action_type = Column(String(128), nullable=False)
    reason = Column(Text, nullable=False)
    payload_json = Column(JSON, nullable=False, default=dict)
    status = Column(String(16), nullable=False, default="pending", index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    resolved_by = Column(String(128), nullable=True)
    resolution_note = Column(Text, nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
